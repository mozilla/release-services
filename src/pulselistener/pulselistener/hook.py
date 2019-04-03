# -*- coding: utf-8 -*-
import json

from cli_common.log import get_logger
from cli_common.pulse import create_consumer
from cli_common.taskcluster import get_service
from pulselistener import task_monitoring

logger = get_logger(__name__)


class Hook(object):
    '''
    A taskcluster hook, used to build a task
    '''
    def __init__(self, group_id, hook_id):
        self.group_id = group_id
        self.hook_id = hook_id
        self.hooks = None  # TC hooks
        self.mercurial_queue = None
        self.routes = []

    def connect_taskcluster(self, client_id=None, access_token=None):
        '''
        Save hooks and queue services for later use
        '''
        # Get taskcluster hooks
        self.hooks = get_service('hooks', client_id, access_token)

        return True

    def connect_mercurial_queue(self, queue):
        '''
        Save local queue to mercurial worker
        '''
        self.mercurial_queue = queue

        return True

    def build_consumer(self, *args, **kwargs):
        '''
        Create a consumer runtime for a new thread
        '''
        raise NotImplementedError

    async def create_task(self, extra_env={}):
        '''
        Create a new task on Taskcluster
        '''
        assert self.hooks is not None

        task = self.hooks.triggerHook(self.group_id, self.hook_id, extra_env)
        task_id = task['status']['taskId']
        logger.info('Triggered a new task', id=task_id)

        # Send task to monitoring
        await task_monitoring.add_task(self.group_id, self.hook_id, task_id)

        return task_id


class PulseHook(Hook):
    '''
    A hook triggered by a Pulse message
    '''
    def __init__(self, group_id, hook_id, pulse_queue, pulse_route):
        super().__init__(group_id, hook_id)
        self.pulse_queue = pulse_queue
        self.pulse_route = pulse_route

    def parse(self, payload):
        '''
        Analyse payload content to extract needed environment
        variables to trigger a new task
        '''
        raise NotImplementedError

    def build_consumer(self, pulse_user, pulse_password):
        '''
        Create the pulse consumer triggering the hook
        '''
        # Use pulse consumer from bot_common
        consumer = create_consumer(
            pulse_user,
            pulse_password,
            self.pulse_queue,
            self.pulse_route,
            self.got_message
        )
        logger.info('Listening for new messages', queue=self.pulse_queue, route=self.pulse_route)  # noqa
        return consumer

    async def got_message(self, channel, body, envelope, properties):
        '''
        Generic Pulse consumer callback
        '''
        assert isinstance(body, bytes), \
            'Body is not in bytes'

        body = json.loads(body.decode('utf-8'))

        # Parse payload
        env = self.parse(body)
        if env is not None:
            if isinstance(env, list):
                for e in env:
                    await self.create_task(extra_env=e)
            else:
                raise Exception('Unsupported env type')

        # Ack the message so it is removed from the broker's queue
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
