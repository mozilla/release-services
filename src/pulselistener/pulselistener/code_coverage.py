# -*- coding: utf-8 -*-
import asyncio

import requests

from cli_common.log import get_logger
from cli_common.pulse import run_consumer
from cli_common.utils import retry
from pulselistener.lib.bus import MessageBus
from pulselistener.lib.monitoring import Monitoring
from pulselistener.lib.pulse import PulseListener
from pulselistener.lib.taskcluster import TaskclusterHook

logger = get_logger(__name__)


class CodeCoverage(object):
    '''
    Taskcluster hook handling the code coverage
    '''
    def __init__(self, config, taskcluster_client_id=None, taskcluster_access_token=None, **kwargs):
        self.triggered_groups = set()

        # Start pulse listener
        self.pulse = PulseListener(
            'exchange/taskcluster-queue/v1/task-group-resolved',
            '#',
            config['PULSE_USER'],
            config['PULSE_PASSWORD'],
        )

        # Start Taskcluster hook integration
        self.hook = TaskclusterHook(
            'project-releng',
            'services-{APP_CHANNEL}-codecoverage/bot'.format(**config),
            taskcluster_client_id,
            taskcluster_access_token,
        )

        # Start Taskcluster monitoring
        self.monitoring = Monitoring(
            config['ADMINS'],
            7 * 3600,
            taskcluster_client_id,
            taskcluster_access_token,
        )

        # Create message bus
        self.bus = MessageBus()
        self.pulse.register(self.bus)
        self.hook.register(self.bus)
        self.monitoring.register(self.bus)

    def run(self):
        logger.info('Running code coverage events...')

        run_consumer(asyncio.gather(
            # New pulse messages are stored in pulse queue
            self.pulse.start(),

            # Convert pulse messages with parse()
            # to build a usable Taskcluster environment
            self.bus.run(PulseListener.QUEUE_OUT, TaskclusterHook.QUEUE_IN, self.parse),

            # Create a new task for every new env
            self.hook.create_tasks(),

            # Finally add created tasks to monitoring
            self.monitoring.start(),
        ))

    def is_coverage_task(self, task):
        return any(
            task['task']['metadata']['name'].startswith(s)
            for s in ['build-linux64-ccov', 'build-win64-ccov']
        )

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
            logger.info('No Coverage task found', group_id=group_id)
            return None

    def parse(self, body):
        '''
        Extract revisions from payload
        '''
        taskGroupId = body['taskGroupId']

        build_task = self.get_build_task_in_group(taskGroupId)
        if build_task is None:
            logger.info('No build task')
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
