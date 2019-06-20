# -*- coding: utf-8 -*-
import collections
import enum
import time

from libmozdata.phabricator import PhabricatorAPI

from cli_common.log import get_logger

logger = get_logger(__name__)

PhabricatorPatch = collections.namedtuple('Diff', 'id, phid, patch, base_revision, commits')


class PhabricatorBuildState(enum.Enum):
    Queued = 1
    Secured = 2
    Public = 3


class PhabricatorBuild(object):
    '''
    A Phabricator buildable, triggered by HarborMaster
    '''
    def __init__(self, request):
        self.diff_id = int(request.rel_url.query.get('diff', 0))
        self.repo_phid = request.rel_url.query.get('repo')
        self.revision_id = int(request.rel_url.query.get('revision', 0))
        self.target_phid = request.rel_url.query.get('target')
        self.diff = None
        self.stack = []

        # State
        self.state = PhabricatorBuildState.Queued
        self.retries_left = None
        self.last_try = None

        if not self.diff_id or not self.repo_phid or not self.revision_id or not self.target_phid:
            raise Exception('Invalid webhook parameters')
        assert isinstance(self.revision_id, int), 'Revision should be an integer'
        assert isinstance(self.target_phid, str), 'Target should be a string'
        assert self.target_phid.startswith('PHID-HMBT-'), 'Invalid target format'

    def __str__(self):
        return 'Revison {} - {}'.format(self.revision_id, self.target_phid)


class Phabricator(object):
    '''
    Phabricator service connected through bus
    '''
    QUEUE_PUBLISH = 'phabricator:publish'

    def __init__(self, url, api_key, retries=5, sleep=10):
        assert isinstance(retries, int)
        assert isinstance(sleep, int)

        # Connect to Phabricator API
        self.api = PhabricatorAPI(url=url, api_key=api_key)

        # Load secure projects
        projects = self.api.search_projects(slugs=['secure-revision'])
        self.secure_projects = {
            p['phid']: p['fields']['name']
            for p in projects
        }
        logger.info('Loaded secure projects', projects=self.secure_projects.values())

        # Phabricator secure revision retries configuration
        self.retries = 5
        self.sleep = 10
        logger.info('Will retry Phabricator secure revision queries', retries=self.retries, sleep=self.sleep)

    def register(self, bus):
        self.bus = bus
        self.bus.add_queue(Phabricator.QUEUE_PUBLISH)

    def check_visibility(self, build):
        '''
        Check the visibility of the revision, by retrying N times with a specified time
        This method is executed regularly by the hook to check on the status evolution
        as the BMO daemon can take several minutes to update the status
        '''
        assert isinstance(build, PhabricatorBuild)
        if build.retries_left is None:
            build.retries_left = self.retries

        # Only when queued
        if build.state != PhabricatorBuildState.Queued:
            return False

        # Check this build has some retries left
        if build.retries_left <= 0:
            return False

        # Check this build has been awaited between tries
        now = time.time()
        if build.last_try is not None and now - build.last_try < self.sleep:
            return False

        # Now we can check if this revision is public
        build.retries_left -= 1
        build.last_try = now
        logger.info('Checking visibility status', build=str(build), retries_left=build.retries_left)
        try:
            self.load_build_assets(build)
            build.state = PhabricatorBuildState.Public
            logger.info('Revision is public', build=str(build))
        except Exception as e:
            logger.info('Revision not accessible', build=str(build), error=str(e))

            # Mark as secured when no retries are left
            if build.retries_left <= 0:
                build.state = PhabricatorBuildState.Secured
                logger.info('Revision is marked as secure', build=str(build))

            return False

        return True

    def load_build_assets(self, build):
        '''
        Load a stack of patches for a public Phabricator build
        without hitting a local mercurial repository
        '''
        assert isinstance(build, PhabricatorBuild)

        # Load revision with projects
        rev = self.api.load_revision(rev_id=build.revision_id, attachments={'projects': True})
        if not rev:
            raise Exception('Not found')

        # Check against secure projects
        projects = set(rev['attachments']['projects']['projectPHIDs'])
        if projects.intersection(self.secure_projects):
            raise Exception('Secure revision')

        # Load full diff
        if build.diff is None:
            diffs = self.api.search_diffs(diff_id=build.diff_id)
            if not diffs:
                raise Exception('Diff not found')
            build.diff = diffs[0]

        # Diff PHIDs from our patch to its base
        def add_patch(diff):
            # Build a nicer Diff instance with associated commit & patch
            assert isinstance(diff, dict)
            assert 'id' in diff
            assert 'phid' in diff
            assert 'baseRevision' in diff
            patch = self.api.load_raw_diff(diff['id'])
            diffs = self.api.search_diffs(
                diff_phid=diff['phid'],
                attachments={
                    'commits': True,
                }
            )
            commits = diffs[0]['attachments']['commits'].get('commits', [])
            return PhabricatorPatch(diff['id'], diff['phid'], patch, diff['baseRevision'], commits)

        # Stack always has the top diff
        build.stack = [
            add_patch(build.diff)
        ]

        parents = self.api.load_parents(build.diff['revisionPHID'])
        if parents:

            # Load all parent diffs
            for parent in parents:
                logger.info('Loading parent diff {}'.format(parent))

                # Sort parent diffs by their id to load the most recent patch
                parent_diffs = sorted(
                    self.api.search_diffs(revision_phid=parent),
                    key=lambda x: x['id'],
                )
                last_diff = parent_diffs[-1]

                # Add most recent patch to stack
                build.stack.insert(0, add_patch(last_diff))

    async def publish(self):
        '''
        Publish results on Phabricator
        * working
        * treeherder_link
        * failure through unit result
        '''
        while self.bus.is_alive():
            payload = await self.bus.receive(Phabricator.QUEUE_PUBLISH)
            mode, build = payload[0], payload[1]
            assert isinstance(build, PhabricatorBuild)
            if mode == 'working':
                # Publish build as working
                self.api.update_build_target(build.target_phid, PhabricatorBuildState.Work)
                logger.info('Published public build as working', build=str(build))

            elif mode == 'failure':
                # Report a failure as a unit test
                self.api.update_build_target(build.target_phid, PhabricatorBuildState.Fail, unit=[payload[2]])

            elif mode == 'treeherder_link':
                # Add a treeherder link on the build
                self.api.create_harbormaster_uri(build.target_phid, 'treeherder', 'Treeherder Jobs', payload[2])

            else:
                logger.warn('Unsupported publish action: {}'.format(mode))
