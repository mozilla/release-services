# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime
from datetime import timedelta

import structlog
from taskcluster.utils import slugId
from taskcluster.utils import stringDate

from pulselistener import taskcluster

logger = structlog.get_logger(__name__)

GROUP_MD = '''

## {}

{:.2f}% of all tasks ({}/{})

'''
TASK_MD = '* [{0}](https://tools.taskcluster.net/task-inspector/#{0})'
TASKCLUSTER_NAMESPACE = 'project.releng.services.tasks.{task_id}'


class Monitoring(object):
    '''
    A simple monitoring tool sending emails through TC
    every X seconds
    '''
    def __init__(self, queue_name, emails, period):
        assert isinstance(queue_name, str)
        assert isinstance(period, int)
        assert period > 0
        assert isinstance(emails, list)
        assert len(emails) > 0
        self.queue_name = queue_name
        self.period = period
        self.stats = {}
        self.emails = emails

        # Setup Taskcluster services
        self.notify = taskcluster.get_service('notify')
        self.queue = taskcluster.get_service('queue')
        self.index = taskcluster.get_service('index')

    def register(self, bus):
        self.bus = bus
        self.bus.add_queue(self.queue_name)

    def next_report(self):
        '''
        Calc report times
        '''
        report_date = datetime.utcnow()
        while True:
            report_date += timedelta(seconds=self.period)
            yield report_date

    async def run(self):
        '''
        Watch task status by using an async queue
        to communicate with other processes
        A report is sent periodically about failed tasks
        '''
        for report_date in self.next_report():
            while datetime.utcnow() < report_date:
                # Monitor next task in queue
                await self.check_task()

                # Sleep a bit before trying a new task
                await asyncio.sleep(1)

            # Send report when timeout is reached
            self.send_report()

    async def check_task(self):
        '''
        Check next task status in queue
        '''
        # Get next task from queue
        group_id, hook_id, task_id = await self.bus.receive(self.queue_name)

        # Get its status
        try:
            status = self.queue.status(task_id)
        except Exception as e:
            logger.warn('Taskcluster queue status failure for {} : {}'.format(task_id, e))
            return

        task_status = status['status']['state']

        if task_status in ('failed', 'completed', 'exception'):

            # Retry tasks in exception
            if task_status == 'exception':
                await self.retry_task(group_id, hook_id, task_id)

            # Lookup the failed details
            if task_status == 'failed' and self.is_restartable(task_id):
                logger.info('Failed task is restartable', task_id=task_id)
                await self.retry_task(group_id, hook_id, task_id)

            # Add to report and stop processing that task
            if hook_id not in self.stats:
                self.stats[hook_id] = {'failed': [], 'completed': [], 'exception': []}
            self.stats[hook_id][task_status].append(task_id)
            logger.info('Got a task status', id=task_id, status=task_status)
        else:
            # Push back into queue so it get checked later on
            await self.bus.send(self.queue_name, (group_id, hook_id, task_id))

    def is_restartable(self, task_id):
        '''
        A task is restartable if its indexed state using task id
        has a monitoring_restart field set to True
        '''
        # Load the indexed data
        task_path = TASKCLUSTER_NAMESPACE.format(task_id=task_id)
        try:
            index = self.index.findTask(task_path)
        except Exception as e:
            logger.info('Task not found in index', task=task_id, error=str(e))
            return False

        # Restart when monitoring_restart is set
        return index['data'].get('monitoring_restart') is True

    async def retry_task(self, group_id, hook_id, task_id):
        '''
        Retry a Taskcluster task by:
        - fetching its definition
        - updating its dates & retry count
        - creating a new task
        Do NOT use rerunTask as it's deprecated AND not recommended
        https://docs.taskcluster.net/docs/reference/platform/taskcluster-queue/references/api#rerunTask
        '''
        # Fetch task definition
        definition = self.queue.task(task_id)

        # Update timestamps
        date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        now = datetime.utcnow()
        created = datetime.strptime(definition['created'], date_format)
        deadline = datetime.strptime(definition['deadline'], date_format)
        expires = datetime.strptime(definition['expires'], date_format)
        definition['created'] = stringDate(now)
        definition['deadline'] = stringDate(now + (deadline - created))
        definition['expires'] = stringDate(now + (expires - created))

        # Decrement retries count
        definition['retries'] -= 1
        if definition['retries'] < 0:
            logger.warn('Will not retry task, no more retries left', task_id=task_id, group_id=group_id, hook_id=hook_id)
            return

        # Trigger a new task with the updated definition
        new_task_id = slugId()
        logger.info('Retry task', old_task=task_id, new_task=new_task_id)
        self.queue.createTask(new_task_id, definition)

        # Enqueue task to check later
        await self.bus.send(self.queue_name, (group_id, hook_id, new_task_id))

        return new_task_id

    def send_report(self):
        '''
        Build a report using current stats and send it through
        Taskcluster Notify
        '''
        assert self.notify is not None

        if not self.stats:
            return

        contents = []

        # Build markdown
        for hook_id, tasks_per_status in sorted(self.stats.items()):
            total = sum([len(tasks) for tasks in tasks_per_status.values()])
            if len(tasks_per_status['completed']) == total:
                continue

            content = '# {} tasks for the last period\n'.format(hook_id)
            for status, tasks in sorted(tasks_per_status.items()):
                nb_tasks = len(tasks)
                content += GROUP_MD.format(
                    status,
                    100.0 * nb_tasks / total,
                    nb_tasks,
                    total,
                )
                content += '\n'.join([
                    TASK_MD.format(task)
                    for task in tasks
                ])
            contents.append(content)

        if len(contents):
            # Send to admins
            logger.info('Sending email to admins')
            for email in self.emails:
                self.notify.email({
                    'address': email,
                    'subject': 'Pulse listener tasks',
                    'content': '\n\n'.join(contents),
                    'template': 'fullscreen',
                })

        # Reset stats
        self.stats = {}
