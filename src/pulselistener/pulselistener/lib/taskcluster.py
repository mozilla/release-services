# -*- coding: utf-8 -*-

from cli_common.log import get_logger
from cli_common.taskcluster import get_service

logger = get_logger(__name__)


class TaskclusterHook(object):
    '''
    Taskcluster service to create new tasks
    '''
    QUEUE_IN = 'hook:in'
    QUEUE_OUT = 'hook:out'

    def __init__(self, group_id, hook_id, client_id=None, access_token=None):
        self.group_id = group_id
        self.hook_id = hook_id
        self.hooks = get_service('hooks', client_id, access_token)

    def register(self, bus):
        self.bus = bus
        self.bus.add_queue(TaskclusterHook.QUEUE_IN)
        self.bus.add_queue(TaskclusterHook.QUEUE_OUT)

    async def create_tasks(self):

        while self.bus.is_alive():
            env = await self.bus.receive(TaskclusterHook.QUEUE_IN)

            logger.info('Creating new task', env=env)
            task = self.hooks.triggerHook(self.group_id, self.hook_id, env)
            task_id = task['status']['taskId']
            logger.info('Triggered a new task', id=task_id)

            await self.bus.send(TaskclusterHook.QUEUE_OUT, {
                'group_id': self.group_id,
                'hook_id': self.hook_id,
                'task_id': task_id,
            })
