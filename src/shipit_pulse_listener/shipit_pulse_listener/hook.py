# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from taskcluster.utils import slugId
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
    def __init__(self, group_id, hook_id, pulse_queue, pulse_route='#'):
        self.group_id = group_id
        self.hook_id = hook_id
        self.pulse_queue = pulse_queue
        self.pulse_route = pulse_route
        self.queue = None  # TC queue

    def connect_taskcluster(self, client_id=None, access_token=None):
        '''
        Load the hook's task definition through Taskcluster
        Save queue service for later use
        '''
        logger.info('Loading task definition', hook=self.hook_id, group=self.group_id)  # noqa
        try:
            service = get_service('hooks', client_id, access_token)
            hook_payload = service.hook(self.group_id, self.hook_id)
            self.task_definition = hook_payload['task']
        except Exception as e:
            logger.warn('Failed to fetch task definition', hook=self.hook_id, group=self.group_id, err=e)  # noqa
            return False

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

        # Extract bugzilla id from body
        body = json.loads(body.decode('utf-8'))
        if 'payload' not in body:
            raise Exception('Missing payload in body')
        payload = body['payload']

        # Parse payload
        env = self.parse_payload(payload)
        if env is None:
            logger.warn('Skipping message, no task created', hook=self.hook_id)
        else:
            self.create_task(extra_env=env)

        # Ack the message so it is removed from the broker's queue
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    def parse_payload(self, payload):
        '''
        Analyse payload content to extract needed environment
        variables to trigger a new task
        '''
        raise NotImplementedError

    def create_task(self, ttl=5, extra_env={}):
        '''
        Create a new task on Taskcluster
        '''
        assert self.queue is not None

        # Update the env in task
        task_definition = copy.deepcopy(self.task_definition)
        task_definition['payload']['env'].update(extra_env)

        # Build task id
        task_id = slugId().decode('utf-8')

        # Set dates
        now = datetime.utcnow()
        task_definition['created'] = now
        task_definition['deadline'] = now + timedelta(seconds=ttl * 3600)
        logger.info('Creating a new task', id=task_id, name=task_definition['metadata']['name'])  # noqa

        # Create a new task
        return self.queue.createTask(task_id, task_definition)
