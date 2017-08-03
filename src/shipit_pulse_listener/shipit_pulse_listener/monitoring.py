# -*- coding: utf-8 -*-
from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from datetime import datetime, timedelta
import asyncio

logger = get_logger(__name__)

GROUP_MD = '''

## {}

{:.2f}% of all tasks ({}/{})

'''
TASK_MD = '* [{0}](https://tools.taskcluster.net/task-inspector/#{0})'


class Monitoring(object):
    '''
    A simple monitoring tool sending emails through TC
    every X seconds
    '''
    def __init__(self, period):
        assert isinstance(period, int)
        assert period > 0
        self.period = period
        self.stats = {}
        self.emails = []

        # TC services
        self.notify = None
        self.queue = None

        # Setup monitoring queue
        self.tasks = asyncio.Queue()

    def connect_taskcluster(self, client_id=None, access_token=None):
        '''
        Load notification service
        '''
        self.notify = get_service('notify', client_id, access_token)
        self.queue = get_service('queue', client_id, access_token)

    async def add_task(self, group_id, hook_id, task_id):
        '''
        Add a task to watch in async queue
        '''
        await self.tasks.put((group_id, hook_id, task_id))

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
        A report is send every hour about failed tasks
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
        assert self.queue is not None

        # Read tasks in queue
        group_id, hook_id, task_id = await self.tasks.get()

        # Get its status
        try:
            status = self.queue.status(task_id)
        except Exception as e:
            logger.warn('Taskcluster queue status failure for {} : {}'.format(task_id, e))
            return

        task_status = status['status']['state']

        if task_status in ('failed', 'completed', 'exception'):
            # Add to report
            stat_name = '{}.{}.{}'.format(group_id, hook_id, task_status)
            if stat_name not in self.stats:
                self.stats[stat_name] = []
            self.stats[stat_name].append(task_id)
            logger.info('Got a task status', id=task_id, status=task_status)
        else:
            # Push back into queue so it get checked later on
            await self.tasks.put((group_id, hook_id, task_id))

    def send_report(self):
        '''
        Build a report using current stats and send it through
        Taskcluster Notify
        '''
        assert self.notify is not None

        if not self.stats:
            return

        # Build markdown
        total = sum([len(s) for s in self.stats.values()])
        content = '# Pulse listener tasks for the last hour\n'
        for group_name, tasks in self.stats.items():
            nb_tasks = len(tasks)
            content += GROUP_MD.format(
                group_name,
                100.0 * nb_tasks / total,
                nb_tasks,
                total,
            )
            content += '\n'.join([
                TASK_MD.format(task)
                for task in tasks
            ])

        # Send to admins
        logger.info('Sending email to admins')
        for email in self.emails:
            self.notify.email({
                'address': email,
                'subject': 'Pulse listener tasks',
                'content': content,
                'template': 'fullscreen',
            })

        # Reset stats
        self.stats = {}
