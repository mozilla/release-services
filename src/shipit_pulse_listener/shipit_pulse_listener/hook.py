# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from taskcluster.utils import slugId
from shipit_pulse_listener import task_monitoring
from cli_common.taskcluster import get_service
from cli_common.pulse import create_consumer
from cli_common.log import get_logger
import copy
import json


logger = get_logger(__name__)


class Hook(object):
    '''
    A taskcluster hook, used to build a task
    '''
    def __init__(self, group_id, hook_id, pulse_queue, pulse_route):
        self.group_id = group_id
        self.hook_id = hook_id
        self.pulse_queue = pulse_queue
        self.pulse_route = pulse_route
        self.queue = None  # TC queue
        self.hooks = None  # TC hooks

    def connect_taskcluster(self, client_id=None, access_token=None):
        '''
        Save hooks and queue services for later use
        '''
        # Get taskcluster hooks
        self.hooks = get_service('hooks', client_id, access_token)

        # Get taskcluster queue
        self.queue = get_service('queue', client_id, access_token)

        return True

    def connect_pulse(self, pulse_user, pulse_password):
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
        if env is None:
            logger.warn('Skipping message, no task created', hook=self.hook_id)
        else:
            await self.create_task(extra_env=env)

        # Ack the message so it is removed from the broker's queue
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    def parse_payload(self, payload):
        '''
        Analyse payload content to extract needed environment
        variables to trigger a new task
        '''
        raise NotImplementedError

    def parse_deadline(self, deadline):
        parts = deadline.split(' ')

        num = int(parts[0])
        unit = parts[1]

        if unit.startswith('second'):
            return timedelta(seconds=num)
        elif unit.startswith('minute'):
            return timedelta(minutes=num)
        elif unit.startswith('hour'):
            return timedelta(minutes=num * 60)
        elif unit.startswith('day'):
            return timedelta(days=num)
        else:
            raise Exception('Error while parsing: ' % deadline)

    async def create_task(self, extra_env={}):
        '''
        Create a new task on Taskcluster
        '''
        assert self.hooks is not None
        assert self.queue is not None

        logger.info('Loading task definition', hook=self.hook_id, group=self.group_id)
        try:
            hook_definition = self.hooks.hook(self.group_id, self.hook_id)
        except Exception as e:
            logger.warn('Failed to fetch task definition', hook=self.hook_id, group=self.group_id, err=e)
            return False

        # Update the env in task
        task_definition = copy.deepcopy(hook_definition['task'])
        task_definition['payload']['env'].update(extra_env)

        # Build task id
        task_id = slugId().decode('utf-8')

        # Set dates
        now = datetime.utcnow()
        task_definition['created'] = now
        task_definition['deadline'] = now + self.parse_deadline(hook_definition['deadline'])
        logger.info('Creating a new task', id=task_id, name=task_definition['metadata']['name'])  # noqa

        # Create a new task
        self.queue.createTask(task_id, task_definition)

        # Send task to monitoring
        await task_monitoring.add_task(self.group_id, self.hook_id, task_id)

        return task_id
