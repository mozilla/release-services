# -*- coding: utf-8 -*-
from shipit_bot_uplift.api import api_client
from collections import OrderedDict, namedtuple
from cli_common.log import get_logger


logger = get_logger(__name__)

# Status can be: merged, failed, skipped
MergeResult = namedtuple('MergeResult', 'status, message, parent')


class MergeTest(object):
    """
    A merge test for a set of patches
    against a branch
    """
    def __init__(self, bugzilla_id, branch, patches):
        self.bugzilla_id = bugzilla_id
        self.branch = branch
        self.patches = patches
        self.parent = None  # Current parent revision
        self.revisions = None  # Listed revisions from patches
        self.results = OrderedDict()  # all the graft results
        self.group = 1  # Group used for every result

    def is_needed(self):
        """
        Check if running this test is needed:
         * on initial test (no patch status)
         * when branch parent has changed
        """
        assert self.parent is not None
        assert self.revisions is not None

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
            logger.warn('No patch status', bz_id=self.bugzilla_id)
            return True  # initial test
        last_status = patch_statuses[0]

        # Update group
        self.group = int(last_status['group']) + 1

        # Run new test when parent has changed
        return self.parent != last_status['revision_parent']

    def is_valid(self):
        """
        Check if all revisions are valid
        """
        assert len(self.results) > 0, \
            "Merge test must be run before using is_valid"
        return all([r.status == 'merged' for r in self.results.values()])

    def list_revisions(self, repository):
        """
        List patch revisions, ordered in time
        Mercurial graft tests will be run in this order
        """
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
        """
        Run full merge test on repository
        We assume the repository is already on correct branch
        """
        assert repository.branch == self.branch, \
            "Repository is not on correct branch ({}/{})".format(repository.branch, self.branch)  # noqa

        # Store repository parent
        self.parent = repository.parent

        # List all revisions, sorted by local id
        self.revisions = self.list_revisions(repository)
        if not self.revisions:
            logger.warn('Skiping merge test : no patch revisions.')
            return False

        # Run test only when needed
        if not self.is_needed():
            logger.info('Skiping merge test : same parent', revisions=self.revisions, branch=self.branch, parent=self.parent)  # noqa
            return False

        parent = self.parent  # Start from repo parent
        for revision, num in self.revisions:
            logger.info('Attempting new graft', revision=revision, num=num, group=self.group)  # noqa

            # Try to merge revision in repository
            # Only when previous merge test passed
            previous = self.results.get(parent)
            if previous is None or previous.status == 'merged':
                merged, message = repository.is_mergeable(revision)
                status = merged and 'merged' or 'failed'
                result = MergeResult(status, message, parent)
            else:
                # Create default invalid result
                # And do not try to run the merge test
                # as the previous one failed
                msg = u'Graft skipped: parent merge failed'
                result = MergeResult('skipped', msg, parent)

            # Save result in backend
            self.save_result(revision, result)

            # Next parent is current revision (commit chain)
            parent = revision

        return True

    def save_result(self, revision, result):
        """
        Store a new patch status on backend
        """
        assert isinstance(result, MergeResult)

        # Publish as a new patch status
        data = {
            'group': self.group,
            'revision': revision.decode('utf-8'),
            'revision_parent': result.parent,
            'status': result.status,
            'branch': self.branch.decode('utf-8'),
            'message': result.message,
        }
        try:
            api_client.create_patch_status(self.bugzilla_id, data)
            logger.info('Created new patch status', **data)
        except Exception as err:
            logger.error('Failed to create patch status', err=err)

        # Store result
        self.results[revision] = result
