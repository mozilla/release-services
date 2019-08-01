# -*- coding: utf-8 -*-
import enum
import time

import structlog
from libmozdata.phabricator import BuildState
from libmozdata.phabricator import UnitResult
from libmozdata.phabricator import UnitResultState

logger = structlog.get_logger(__name__)


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

    def check_visibility(self, api, secure_projects, max_retries=5, sleep=10):
        '''
        Check the visibility of the revision, by retrying N times with a specified time
        This method is executed regularly by the hook to check on the status evolution
        as the BMO daemon can take several minutes to update the status
        '''
        if self.retries_left is None:
            self.retries_left = max_retries

        # Only when queued
        if self.state != PhabricatorBuildState.Queued:
            return False

        # Check this build has some retries left
        if self.retries_left <= 0:
            return False

        # Check this build has been awaited between tries
        now = time.time()
        if self.last_try is not None and now - self.last_try < sleep:
            return False

        # Now we can check if this revision is public
        self.retries_left -= 1
        self.last_try = now
        logger.info('Checking visibility status', build=str(self), retries_left=self.retries_left)
        try:

            # Load revision with projects
            self.rev = api.load_revision(rev_id=self.revision_id, attachments={'projects': True, 'reviewers': True})
            if not self.rev:
                raise Exception('Not found')

            # Check against secure projects
            projects = set(self.rev['attachments']['projects']['projectPHIDs'])
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
            if self.retries_left <= 0:
                self.state = PhabricatorBuildState.Secured
                logger.info('Revision is marked as secure', build=str(self))

            return False

        self.state = PhabricatorBuildState.Public
        logger.info('Revision is public', build=str(self))
        return True


class PhabricatorCodeReview(object):
    '''
    Actions related to Phabricator for the code review events
    '''
    def __init__(self, api, publish=False):
        # TODO: this should be the only place with Phabricator API calls
        self.api = api
        self.publish = publish
        logger.info('Phabricator publication is {}'.format(self.publish and 'enabled' or 'disabled'))

    def publish_results(self, payload):
        assert self.publish is True, 'Publication disabled'
        mode, build, extras = payload
        logger.debug('Publishing a Phabricator build update', mode=mode, build=build)

        if mode == 'fail:general':
            failure = UnitResult(
                namespace='code-review',
                name='general',
                result=UnitResultState.Broken,
                details='WARNING: An error occured in the code review bot.\n\n```{}```'.format(extras['message']),
                format='remarkup',
                duration=extras.get('duration', 0)
            )
            self.api.update_build_target(build.target_phid, BuildState.Fail, unit=[failure])

        elif mode == 'fail:mercurial':
            failure = UnitResult(
                namespace='code-review',
                name='mercurial',
                result=UnitResultState.Fail,
                details='WARNING: The code review bot failed to apply your patch.\n\n```{}```'.format(extras['message']),
                format='remarkup',
                duration=extras.get('duration', 0)
            )
            self.api.update_build_target(build.target_phid, BuildState.Fail, unit=[failure])

        elif mode == 'success':
            self.api.create_harbormaster_uri(build.target_phid, 'treeherder', 'Treeherder Jobs', extras['treeherder_url'])

        elif mode == 'work':
            self.api.update_build_target(build.target_phid, BuildState.Work)
            logger.info('Published public build as working', build=str(build))

        else:
            logger.warning('Unsupported publication', mode=mode, build=build)

        return True
