# -*- coding: utf-8 -*-
import collections
import enum
import time

import structlog
from libmozdata.phabricator import PhabricatorAPI

logger = structlog.get_logger(__name__)

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
        self.state = PhabricatorBuildState.Queued

        if not self.diff_id or not self.repo_phid or not self.revision_id or not self.target_phid:
            raise Exception('Invalid webhook parameters')
        assert isinstance(self.revision_id, int), 'Revision should be an integer'
        assert isinstance(self.target_phid, str), 'Target should be a string'
        assert self.target_phid.startswith('PHID-HMBT-'), 'Invalid target format'

        # Remote objects loaded by actions below
        self.revision = None
        self.reviewers = []
        self.diff = None
        self.stack = []

    def __str__(self):
        return 'Revison {} - {}'.format(self.revision_id, self.target_phid)


class PhabricatorActions(object):
    '''
    Common Phabricator actions shared across clients
    '''
    def __init__(self, url, api_key, retries=5, sleep=10):
        self.api = PhabricatorAPI(url=url, api_key=api_key)

        # Phabricator secure revision retries configuration
        assert isinstance(retries, int)
        assert isinstance(sleep, int)
        self.retries = collections.defaultdict(lambda: (retries, None))
        self.sleep = sleep
        logger.info('Will retry Phabricator secure revision queries', retries=retries, sleep=sleep)

        # Load secure projects
        projects = self.api.search_projects(slugs=['secure-revision'])
        self.secure_projects = {
            p['phid']: p['fields']['name']
            for p in projects
        }
        logger.info('Loaded secure projects', projects=self.secure_projects.values())

    def update_state(self, build):
        '''
        Check the visibility of the revision, by retrying N times with a specified time
        This method is executed regularly by the client application to check on the status evolution
        as the BMO daemon can take several minutes to update the status
        '''
        assert isinstance(build, PhabricatorBuild)

        # Only when queued
        if build.state != PhabricatorBuildState.Queued:
            return

        # Check this build has some retries left
        retries_left, last_try = self.retries[build.target_phid]
        if retries_left <= 0:
            return

        # Check this build has been awaited between tries
        now = time.time()
        if last_try is not None and now - last_try < self.sleep:
            return

        # Now we can check if this revision is public
        retries_left -= 1
        self.retries[build.target_phid] = (retries_left, now)
        logger.info('Checking visibility status', build=str(build), retries_left=retries_left)

        if self.is_visible(build):
            build.state = PhabricatorBuildState.Public
            logger.info('Revision is public', build=str(build))

        elif retries_left <= 0:
            # Mark as secured when no retries are left
            build.state = PhabricatorBuildState.Secured
            logger.info('Revision is marked as secure', build=str(build))

        else:
            # Enqueue back to retry later
            build.state = PhabricatorBuildState.Queued

    def is_visible(self, build):
        '''
        Check the visibility of the revision by loading its details
        '''
        assert isinstance(build, PhabricatorBuild)
        assert build.state == PhabricatorBuildState.Queued
        try:
            # Load revision with projects
            build.revision = self.api.load_revision(
                rev_id=build.revision_id,
                attachments={'projects': True, 'reviewers': True}
            )
            if not build.revision:
                raise Exception('Not found')

            # Check against secure projects
            projects = set(build.revision['attachments']['projects']['projectPHIDs'])
            if projects.intersection(self.secure_projects):
                raise Exception('Secure revision')
        except Exception as e:
            logger.info('Revision not accessible', build=str(build), error=str(e))
            return False

        return True

    def load_patches_stack(self, build):
        '''
        Load a stack of patches for a public Phabricator build
        without hitting a local mercurial repository
        '''
        build.stack = self.api.load_patches_stack(build.diff_id, build.diff)

    def load_reviewers(self, build):
        '''
        Load details for reviewers found on a build
        '''
        assert isinstance(build, PhabricatorBuild)
        assert build.state == PhabricatorBuildState.Public
        assert build.revision is not None

        reviewers = build.revision['attachments']['reviewers']['reviewers']
        build.reviewers = [
            self.api.load_user(user_phid=reviewer['reviewerPHID'])
            for reviewer in reviewers
        ]
