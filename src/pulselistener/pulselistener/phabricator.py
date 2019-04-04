# -*- coding: utf-8 -*-
import enum
import time

from cli_common.log import get_logger

logger = get_logger(__name__)


class PhabricatorBuildState(enum.Enum):
    Queued = 1
    Secured = 2
    Public = 3


class PhabricatorBuild(object):
    '''
    A Phabricator buildable, triggered by HarborMaster
    '''
    def __init__(self, request, retries=5, sleep=10):
        self.diff_id = int(request.rel_url.query.get('diff', 0))
        self.repo_phid = request.rel_url.query.get('repo')
        self.revision_id = int(request.rel_url.query.get('revision', 0))
        self.target_phid = request.rel_url.query.get('target')
        self.diff = None

        # State
        self.state = PhabricatorBuildState.Queued
        self.retries = retries
        self.sleep = sleep
        self.last_try = None

        if not self.diff_id or not self.repo_phid or not self.revision_id or not self.target_phid:
            raise Exception('Invalid webhook parameters')
        assert isinstance(self.revision_id, int), 'Revision should be an integer'
        assert isinstance(self.target_phid, str), 'Target should be a string'
        assert self.target_phid.startswith('PHID-HMBT-'), 'Invalid target format'

    def __str__(self):
        return 'Revison {} - {}'.format(self.revision_id, self.target_phid)

    def check_visibility(self, api, secure_projects):
        '''
        Check the visibility of the revision, by retrying N times with a specified time
        This method is executed regularly by the hook to check on the status evolution
        as the BMO daemon can take several minutes to update the status
        '''
        # Only when queued
        if self.state != PhabricatorBuildState.Queued:
            return False

        # Check this build has some retries left
        if self.retries <= 0:
            return False

        # Check this build has been awaited between tries
        now = time.time()
        if self.last_try is not None and now - self.last_try < self.sleep:
            return False

        # Now we can check if this revision is public
        self.retries -= 1
        self.last_try = now
        logger.info('Checking visibility status', build=str(self), retries_left=self.retries)
        try:

            # Load revision with projects
            rev = api.load_revision(rev_id=self.revision_id, attachments={'projects': True})
            if not rev:
                raise Exception('Not found')

            # Check against secure projects
            projects = set(rev['attachments']['projects']['projectPHIDs'])
            if projects.intersection(secure_projects):
                raise Exception('Secure revision')

            # Load full diff
            diffs = api.search_diffs(diff_id=self.diff_id)
            if not diffs:
                raise Exception('Diff not found')
            self.diff = diffs[0]
        except Exception as e:
            logger.info('Revision not accessible', build=str(self), error=str(e))

            # Mark as secured when no retries are left
            if self.retries <= 0:
                self.state = PhabricatorBuildState.Secured
                logger.info('Revision is marked as secure', build=str(self))

            return False

        self.state = PhabricatorBuildState.Public
        logger.info('Revision is public', build=str(self))
        return True
