# -*- coding: utf-8 -*-
import asyncio

import requests
import structlog
from libmozdata.phabricator import BuildState

from pulselistener.hook import Hook
from pulselistener.hook import PulseHook
from pulselistener.lib.pulse import run_consumer
from pulselistener.lib.utils import retry
from pulselistener.mercurial import MercurialWorker
from pulselistener.monitoring import task_monitoring
from pulselistener.phabricator import PhabricatorBuild
from pulselistener.phabricator import PhabricatorBuildState
from pulselistener.web import WebServer

logger = structlog.get_logger(__name__)


class HookPhabricator(Hook):
    '''
    Taskcluster hook handling the static analysis
    for Phabricator differentials
    '''
    def __init__(self, configuration):
        assert 'hookId' in configuration
        super().__init__(
            configuration.get('hookGroupId', 'project-releng'),
            configuration['hookId'],
        )

        # Connect to Phabricator API
        assert 'phabricator_api' in configuration
        self.api = configuration['phabricator_api']

        # Load secure projects
        projects = self.api.search_projects(slugs=['secure-revision'])
        self.secure_projects = {
            p['phid']: p['fields']['name']
            for p in projects
        }
        logger.info('Loaded secure projects', projects=self.secure_projects.values())

        # Phabricator secure revision retries configuration
        self.phabricator_retries = configuration.get('phabricator_retries', 5)
        self.phabricator_sleep = configuration.get('phabricator_sleep', 10)
        assert isinstance(self.phabricator_retries, int)
        assert isinstance(self.phabricator_sleep, int)
        logger.info('Will retry Phabricator secure revision queries', retries=self.phabricator_retries, sleep=self.phabricator_sleep)  # noqa

        self.risk_analysis_reviewers = configuration.get('risk_analysis_reviewers', [])

    async def build_consumer(self, *args, **kwargs):
        '''
        Main consumer, running queued builds from the web server
        '''
        assert self.web_queue is not None, 'Missing web server queue'

        def wait_build():
            return self.web_queue.get()

        loop = asyncio.get_event_loop()

        while True:
            build = await loop.run_in_executor(None, wait_build)

            # Process next build in queue
            await self.run_build(build)

    def should_run_risk_analysis(self, build):
        '''
        Check if we should trigger a risk analysis for this revision.
        '''
        # Run risk analysis when the revision is being reviewed by one
        # of some specific reviewers.
        reviewers = build.rev['attachments']['reviewers']['reviewers']
        for reviewer in reviewers:
            user_data = self.api.load_user(user_phid=reviewer['reviewerPHID'])
            if any(reviewer == user_data['fields']['username'] for reviewer in self.risk_analysis_reviewers):
                return True

        return False

    async def run_build(self, build):
        '''
        Start asynchronously new builds when their revision become public
        '''
        assert isinstance(build, PhabricatorBuild)

        # Check visibility of builds in queue
        # The build state is updated to public/secured there
        if build.state == PhabricatorBuildState.Queued:
            build.check_visibility(self.api, self.secure_projects, self.phabricator_retries, self.phabricator_sleep)

        if build.state == PhabricatorBuildState.Public:
            # Push to try public builds
            try:
                logger.info('Triggering task from webhook', build=build)

                # Enqueue push to try
                # TODO: better integration with mercurial queue
                # to get the revisions produced
                await self.mercurial_queue.put(build)

            except Exception as e:
                logger.error('Failed to queue task from webhook', error=str(e))

            try:
                if self.should_run_risk_analysis(build):
                    task = self.hooks.triggerHook('project-relman', 'bugbug-classify-patch', {'DIFF_ID': build.diff_id})
                    task_id = task['status']['taskId']
                    logger.info('Triggered a new risk analysis task', id=task_id)

                    # Send task to monitoring
                    await task_monitoring.add_task('project-relman', 'bugbug-classify-patch', task_id)

            except Exception as e:
                logger.error('Failed to trigger risk analysis task', error=str(e))

            # Report public bug as working
            self.api.update_build_target(build.target_phid, BuildState.Work)
            logger.info('Published public build as working', build=str(build))

        elif build.state == PhabricatorBuildState.Secured:
            # We cannot send any update on a Secured build
            # as the bot has no edit access on it
            logger.info('Secured revision, skipping.', build=build.target_phid)

        else:
            # By default requeue build until it's marked secured or public
            self.web_queue.put(build)


class HookCodeCoverage(PulseHook):
    '''
    Taskcluster hook handling the code coverage
    '''
    def __init__(self, configuration):
        assert 'hookId' in configuration
        self.triggered_groups = set()
        super().__init__(
            configuration.get('hookGroupId', 'project-releng'),
            configuration['hookId'],
            'exchange/taskcluster-queue/v1/task-group-resolved',
            '#'
        )

    def is_coverage_task(self, task):
        return any(task['task']['metadata']['name'].startswith(s) for s in ['build-linux64-ccov', 'build-win64-ccov'])

    def get_build_task_in_group(self, group_id):
        if group_id in self.triggered_groups:
            logger.info('Received duplicated groupResolved notification', group=group_id)
            return None

        def maybe_trigger(tasks):
            for task in tasks:
                if self.is_coverage_task(task):
                    self.triggered_groups.add(group_id)
                    return task

            return None

        list_url = 'https://queue.taskcluster.net/v1/task-group/{}/list'.format(group_id)

        def retrieve_coverage_task():
            r = requests.get(list_url, params={
                'limit': 200
            })
            r.raise_for_status()
            reply = r.json()
            task = maybe_trigger(reply['tasks'])

            while task is None and 'continuationToken' in reply:
                r = requests.get(list_url, params={
                    'limit': 200,
                    'continuationToken': reply['continuationToken']
                })
                r.raise_for_status()
                reply = r.json()
                task = maybe_trigger(reply['tasks'])

            return task

        try:
            return retry(retrieve_coverage_task)
        except requests.exceptions.HTTPError:
            return None

    def parse(self, body):
        '''
        Extract revisions from payload
        '''
        taskGroupId = body['taskGroupId']

        build_task = self.get_build_task_in_group(taskGroupId)
        if build_task is None:
            return None

        repository = build_task['task']['payload']['env']['GECKO_HEAD_REPOSITORY']

        if repository not in ['https://hg.mozilla.org/mozilla-central', 'https://hg.mozilla.org/try']:
            logger.warn('Received groupResolved notification for a coverage task in an unexpected branch', repository=repository)
            return None

        logger.info('Received groupResolved notification for coverage builds', repository=repository, revision=build_task['task']['payload']['env']['GECKO_HEAD_REV'], group=taskGroupId)  # noqa

        return [{
            'REPOSITORY': repository,
            'REVISION': build_task['task']['payload']['env']['GECKO_HEAD_REV'],
        }]


class PulseListener(object):
    '''
    Listen to pulse messages and trigger new tasks
    '''
    def __init__(self,
                 pulse_user,
                 pulse_password,
                 hooks_configuration,
                 repositories,
                 phabricator_api,
                 cache_root,
                 publish_phabricator=False,
                 taskcluster_client_id=None,
                 taskcluster_access_token=None,
                 ):

        self.pulse_user = pulse_user
        self.pulse_password = pulse_password
        self.hooks_configuration = hooks_configuration
        self.taskcluster_client_id = taskcluster_client_id
        self.taskcluster_access_token = taskcluster_access_token
        self.phabricator_api = phabricator_api

        task_monitoring.setup()

        # Build mercurial worker & queue
        self.mercurial = MercurialWorker(
            self.phabricator_api,
            publish_phabricator=publish_phabricator,
            repositories=repositories,
            cache_root=cache_root,
        )

        # Create web server
        self.webserver = WebServer()

    def run(self):

        # Build hooks for each conf
        hooks = [
            self.build_hook(conf)
            for conf in self.hooks_configuration
        ]
        if not hooks:
            raise Exception('No hooks created')

        # Run hooks pulse listeners together
        # but only use hooks with active definitions
        def _connect(hook):
            return hook.connect_queues(
                mercurial_queue=self.mercurial.queue if self.mercurial else None,
                web_queue=self.webserver.queue,
            )
        consumers = [
            hook.build_consumer(self.pulse_user, self.pulse_password)
            for hook in hooks
            if _connect(hook)
        ]

        # Add monitoring task
        consumers.append(task_monitoring.run())

        # Add mercurial task
        if self.mercurial is not None:
            consumers.append(self.mercurial.run())

        # Start the web server in its own process
        web_process = self.webserver.start()

        # Run all tasks concurrently
        run_consumer(asyncio.gather(*consumers))

        web_process.join()

    def build_hook(self, conf):
        '''
        Build a new hook instance according to configuration
        '''
        assert isinstance(conf, dict)
        assert 'type' in conf
        conf['phabricator_api'] = self.phabricator_api
        classes = {
            'static-analysis-phabricator': HookPhabricator,
            'code-coverage': HookCodeCoverage,
        }
        hook_class = classes.get(conf['type'])
        if hook_class is None:
            raise Exception('Unsupported hook {}'.format(conf['type']))

        return hook_class(conf)

    def add_build(self, build_target_phid):
        '''
        Fetch a phabricator build and push it in the mercurial queue
        '''
        assert build_target_phid.startswith('PHID-HMBT-')
        if self.mercurial is None:
            logger.warn('Skip adding build, mercurial worker is disabled', build=build_target_phid)
            return

        # Load the diff from the target
        container = self.phabricator_api.find_target_buildable(build_target_phid)
        diffs = self.phabricator_api.search_diffs(diff_phid=container['fields']['objectPHID'])

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.mercurial.queue.put((build_target_phid, diffs[0])))
        logger.info('Pushed build in queue', build=build_target_phid)
