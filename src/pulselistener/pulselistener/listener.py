# -*- coding: utf-8 -*-
import asyncio

import requests
import structlog

from pulselistener import taskcluster
from pulselistener.config import QUEUE_CODE_REVIEW
from pulselistener.config import QUEUE_MERCURIAL
from pulselistener.config import QUEUE_MONITORING
from pulselistener.config import QUEUE_PHABRICATOR_RESULTS
from pulselistener.config import QUEUE_PULSE_CODECOV
from pulselistener.lib.bus import MessageBus
from pulselistener.lib.monitoring import Monitoring
from pulselistener.lib.pulse import PulseListener
from pulselistener.lib.pulse import run_consumer
from pulselistener.lib.utils import retry
from pulselistener.lib.web import WebServer
from pulselistener.mercurial import MercurialWorker
from pulselistener.phabricator import PhabricatorBuild
from pulselistener.phabricator import PhabricatorBuildState
from pulselistener.phabricator import PhabricatorCodeReview

logger = structlog.get_logger(__name__)


class HookPhabricator(object):
    '''
    Taskcluster hook handling the static analysis
    for Phabricator differentials
    '''
    def __init__(self, configuration, bus):
        assert 'hookId' in configuration
        self.hooks = taskcluster.get_service('hooks')
        self.bus = bus

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

    async def run(self):
        '''
        Main consumer, running queued builds from the web server
        '''
        while True:
            # Get next build from Webserver code review queue
            build = await self.bus.receive(QUEUE_CODE_REVIEW)
            assert isinstance(build, PhabricatorBuild)

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
                await self.bus.send(QUEUE_MERCURIAL, build)

            except Exception as e:
                logger.error('Failed to queue task from webhook', error=str(e))

            try:
                if self.should_run_risk_analysis(build):
                    task = self.hooks.triggerHook('project-relman', 'bugbug-classify-patch', {'DIFF_ID': build.diff_id})
                    task_id = task['status']['taskId']
                    logger.info('Triggered a new risk analysis task', id=task_id)

                    # Send task to monitoring
                    await self.bus.send(QUEUE_MONITORING, ('project-relman', 'bugbug-classify-patch', task_id))

            except Exception as e:
                logger.error('Failed to trigger risk analysis task', error=str(e))

            # Report public bug as working
            await self.bus.send(QUEUE_PHABRICATOR_RESULTS, ('work', build, {}))

        elif build.state == PhabricatorBuildState.Secured:
            # We cannot send any update on a Secured build
            # as the bot has no edit access on it
            logger.info('Secured revision, skipping.', build=build.target_phid)

        else:
            # By default requeue build until it's marked secured or public
            await self.bus.send(QUEUE_CODE_REVIEW, build)


class HookCodeCoverage(object):
    '''
    Taskcluster hook handling the code coverage
    '''
    def __init__(self, configuration, bus):
        assert 'hookId' in configuration
        self.triggered_groups = set()
        self.group_id = configuration.get('hookGroupId', 'project-releng')
        self.hook_id = configuration['hookId']
        self.bus = bus

        # Setup TC services
        self.queue = taskcluster.get_service('queue')
        self.hooks = taskcluster.get_service('hooks')

    async def run(self):
        '''
        Main consumer, running queued payloads from the pulse listener
        '''
        while True:
            # Get next payload from pulse messages
            payload = await self.bus.receive(QUEUE_PULSE_CODECOV)

            # Parse the payload to extract a new task's environment
            envs = self.parse(payload)
            if envs is None:
                continue

            for env in envs:
                # Trigger new tasks
                task = self.hooks.triggerHook(self.group_id, self.hook_id, env)
                task_id = task['status']['taskId']
                logger.info('Triggered a new code coverage task', id=task_id)

                # Send task to monitoring
                await self.bus.send(QUEUE_MONITORING, (self.group_id, self.hook_id, task_id))

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

        def retrieve_coverage_task(limit=200):
            reply = self.queue.listTaskGroup(
                group_id,
                limit=limit,
            )
            task = maybe_trigger(reply['tasks'])

            while task is None and reply.get('continuationToken') is not None:
                reply = self.queue.listTaskGroup(
                    group_id,
                    limit=limit,
                    continuationToken=reply['continuationToken'],
                )
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


class EventListener(object):
    '''
    Listen to external events and trigger new tasks
    '''
    def __init__(self,
                 pulse_user,
                 pulse_password,
                 hooks_configuration,
                 repositories,
                 phabricator_api,
                 cache_root,
                 taskcluster_client_id=None,
                 taskcluster_access_token=None,
                 ):

        self.hooks_configuration = hooks_configuration
        self.taskcluster_client_id = taskcluster_client_id
        self.taskcluster_access_token = taskcluster_access_token
        self.phabricator_api = phabricator_api

        # Create message bus shared amongst process
        self.bus = MessageBus()

        # Build mercurial worker & queue
        self.mercurial = MercurialWorker(
            QUEUE_MERCURIAL,
            QUEUE_PHABRICATOR_RESULTS,
            self.phabricator_api,
            repositories=repositories,
            cache_root=cache_root,
        )
        self.mercurial.register(self.bus)

        # Create web server
        self.webserver = WebServer(QUEUE_CODE_REVIEW)
        self.webserver.register(self.bus)

        # Setup monitoring for newly created tasks
        self.monitoring = Monitoring(QUEUE_MONITORING, taskcluster.secrets['ADMINS'], 7 * 3600)
        self.monitoring.register(self.bus)

        # Create pulse listener for code coverage
        self.pulse = PulseListener(
            QUEUE_PULSE_CODECOV,
            'exchange/taskcluster-queue/v1/task-group-resolved',
            '#',
            pulse_user,
            pulse_password,
        )
        self.pulse.register(self.bus)

        # Phabricator publication
        self.phabricator = PhabricatorCodeReview(
            api=phabricator_api,
            publish=taskcluster.secrets['PHABRICATOR'].get('publish', False),
        )
        self.bus.add_queue(QUEUE_PHABRICATOR_RESULTS)

    def run(self):

        # Build hooks for each conf
        hooks = [
            self.build_hook(conf)
            for conf in self.hooks_configuration
        ]
        if not hooks:
            raise Exception('No hooks created')

        consumers = [
            hook.run()
            for hook in hooks
        ]

        # Add monitoring task
        consumers.append(self.monitoring.run())

        # Add pulse task
        consumers.append(self.pulse.run())

        # Add mercurial task
        consumers.append(self.mercurial.run())

        # Publish results on Phabricator
        if self.phabricator.publish:
            consumers.append(
                self.bus.run(self.phabricator.publish_results, QUEUE_PHABRICATOR_RESULTS)
            )

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

        return hook_class(conf, self.bus)
