# -*- coding: utf-8 -*-
import enum
import json
import os.path
from collections import OrderedDict
from collections import namedtuple

from cli_common.log import get_logger
from uplift_bot.api import api_client
from uplift_bot.mercurial import MergeSkipped

logger = get_logger(__name__)

# Status can be: merged, failed, skipped
MergeResult = namedtuple('MergeResult', 'revision, status, message, parent')


class MergeStatus(enum.Enum):
    Merged = 'merged'
    Skipped = 'skipped'
    Failed = 'failed'


class MergeTest(object):
    '''
    A merge test for a set of patches
    against a branch
    '''
    def __init__(self, bugzilla_id, branch, status, patches, reviewer=None):
        self.bugzilla_id = bugzilla_id
        self.branch = branch
        self.status = status
        self.branch_rebased = None
        self.patches = patches
        self.parent = None  # Current parent revision
        self.revisions = None  # Listed revisions from patches
        self.results = OrderedDict()  # all the graft results
        self.group = 1  # Group used for every result

        # Parse email from reviewer name (from libmozdata)
        name = reviewer and reviewer.get('name')
        if name:
            self.reviewer_nick = '@' in name and name[:name.index('@')] or name
        else:
            self.reviewer_nick = None
        logger.info('New merge test', bz_id=self.bugzilla_id, branch=self.branch, reviewer=self.reviewer_nick)

    @staticmethod
    def from_json(path):
        assert os.path.exists(path)
        with open(path) as f:
            payload = json.load(f)

        mt = MergeTest(
            payload['bugzilla_id'],
            payload['branch'].encode('utf-8'),
            payload['status'],
            payload['patches'],
        )
        mt.reviewer_nick = payload['reviewer_nick']
        return mt

    def to_json(self):
        return json.dumps({
            'bugzilla_id': self.bugzilla_id,
            'branch': self.branch.decode('utf-8'),
            'status': self.status,
            'patches': self.patches,
            'reviewer_nick': self.reviewer_nick,
        }, indent=4)

    def is_needed(self):
        '''
        Check if running this test is needed:
         * on initial test (no patch status)
         * when branch parent has changed
        '''
        assert self.parent is not None
        assert self.revisions is not None

        # Always run test for approved merge tests
        if self.status == '+':
            return True

        # Load last patch status for first patch
        # Only use the ones for this branch + revision
        top_revision, _ = self.revisions[0]
        patch_statuses = [
            ps
            for ps in api_client.list_patch_status(self.bugzilla_id)
            if ps['branch'] == self.branch.decode('utf-8')
            and ps['revision'] == top_revision.decode('utf-8')
        ]
        if not patch_statuses:
            logger.info('No patch status', bz_id=self.bugzilla_id)
            return True  # initial test
        last_status = patch_statuses[0]

        # Update group
        self.group = int(last_status['group']) + 1

        # Run new test when parent has changed
        return self.parent != last_status['revision_parent']

    def is_valid(self):
        '''
        Check if all revisions are valid
        '''
        assert len(self.results) > 0, \
            'Merge test must be run before using is_valid'
        return all([
            r.status in (MergeStatus.Merged, MergeStatus.Skipped)
            for r in self.results.values()
        ])

    def list_revisions(self, repository):
        '''
        List patch revisions, ordered in time
        Mercurial graft tests will be run in this order
        '''
        def _id_revision(revision):
            revision = isinstance(revision, int) \
                and str(revision).encode('utf-8') \
                or revision.encode('utf-8')

            # Get numerical id
            local_id = repository.identify(revision)

            return revision, local_id

        # Sorted by local id (numerical)
        return sorted([
            _id_revision(revision)
            for revision, patch in self.patches.items()
            if patch['source'] == 'mercurial'
        ], key=lambda x: x[1])

    def run(self, repository):
        '''
        Run full merge test on repository
        We assume the repository is already on correct branch
        '''
        assert repository.branch == self.branch, \
            'Repository is not on correct branch ({}/{})'.format(repository.branch, self.branch)  # noqa

        # Store repository parent
        self.parent = repository.parent

        # List all revisions, sorted by local id
        self.revisions = self.list_revisions(repository)
        if not self.revisions:
            logger.info('Skipping merge test : no patch revisions.')
            return False

        # Run test only when needed
        if not self.is_needed():
            logger.info('Skipping merge test : same parent', revisions=self.revisions, branch=self.branch, parent=self.parent)  # noqa
            return False

        # Create a new branch to work on
        if self.status == '+':
            self.branch_rebased = 'uplift-{}-{}'.format(
                self.branch.decode('utf-8'),
                self.bugzilla_id
            ).encode('utf-8')
            repository.create_branch(self.branch_rebased)

        parent = self.parent  # Start from repo parent
        for revision, num in self.revisions:
            assert isinstance(parent, str)

            # Try to merge revision in repository
            # Only when previous merge test passed
            previous = self.results.get(parent)
            if previous is None or previous.status != MergeStatus.Failed:
                logger.info('Attempting new graft', revision=revision, num=num, group=self.group)  # noqa
                try:
                    message = repository.merge(revision)
                    result = MergeResult(revision, MergeStatus.Merged, message, parent)
                except MergeSkipped as e:
                    result = MergeResult(revision, MergeStatus.Skipped, str(e), parent)
                except Exception as e:
                    result = MergeResult(revision, MergeStatus.Failed, str(e), parent)

            else:
                # Create default invalid result
                # And do not try to run the merge test
                # as the previous one failed
                msg = u'Graft skipped: parent merge failed'
                result = MergeResult(revision, MergeStatus.Failed, msg, parent)
                logger.info('Skipped graft', revision=revision, num=num, group=self.group)  # noqa

            # Rewrite commit message to append RelMan reviewer nickname
            if result.status == MergeStatus.Merged and self.status == '+' and self.reviewer_nick:
                repository.amend(' a={}'.format(self.reviewer_nick))

            # Save result in backend
            self.save_result(result)

            # Next parent is current revision (commit chain)
            parent = revision.decode('utf-8')

        # Always cleanup
        repository.cleanup()

        return True

    def save_result(self, result):
        '''
        Store a new patch status on backend
        '''
        assert isinstance(result, MergeResult)
        assert isinstance(result.parent, str)
        revision = result.revision.decode('utf-8')

        # Store result
        self.results[revision] = result

        # Skip for approved patches
        if self.status == '+':
            return

        parent = result.parent.decode('utf-8') if isinstance(result.parent, bytes) else result.parent

        # Publish as a new patch status
        data = {
            'group': self.group,
            'revision': revision,
            'revision_parent': parent,
            'status': result.status.value,
            'branch': self.branch.decode('utf-8'),
            'message': result.message,
        }
        try:
            api_client.create_patch_status(self.bugzilla_id, data)
            logger.info('Created new patch status', **data)
        except Exception as err:
            logger.error('Failed to create patch status', err=err)
