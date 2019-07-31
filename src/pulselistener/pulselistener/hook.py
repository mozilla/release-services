# -*- coding: utf-8 -*-
import json

import structlog

from pulselistener import taskcluster
from pulselistener.config import QUEUE_MONITORING
from pulselistener.lib.bus import MessageBus
from pulselistener.lib.pulse import create_consumer

logger = structlog.get_logger(__name__)


class Hook(object):
    '''
    A taskcluster hook, used to build a task
    '''
    def __init__(self, group_id, hook_id, bus):
        self.group_id = group_id
        self.hook_id = hook_id
        self.hooks = taskcluster.get_service('hooks')
        self.mercurial_queue = None
        self.routes = []
        assert isinstance(bus, MessageBus)
        self.bus = bus

    def connect_queues(self, mercurial_queue):
        '''
        Save queues to communicate across processes
        '''
        self.mercurial_queue = mercurial_queue

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
        await self.bus.send(QUEUE_MONITORING, (self.group_id, self.hook_id, task_id))

        return task_id


class PulseHook(Hook):
    '''
    A hook triggered by a Pulse message
    '''
    def __init__(self, group_id, hook_id, pulse_queue, pulse_route, bus):
        super().__init__(group_id, hook_id, bus)
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
