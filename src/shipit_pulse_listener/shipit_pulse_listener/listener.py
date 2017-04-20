from datetime import datetime, timedelta
from taskcluster.utils import slugId
from cli_common.pulse import create_consumer, run_consumer
from cli_common.taskcluster import TaskclusterClient
from cli_common.log import get_logger
import copy
import json
import re

logger = get_logger(__name__)

HOOK_REGEX = re.compile(r'([\w\-_]+):([\w\-_]+)')


class PulseListener(object):
    """
    Listen to pulse messages and trigger new tasks
    """
    def __init__(self, secrets_path, client_id=None, access_token=None):
        self.taskcluster = TaskclusterClient(client_id, access_token)
        self.tasks = []

        # Fetch pulse credentials from TC secrets
        logger.info('Using secrets', path=secrets_path)
        required = ('PULSE_USER', 'PULSE_PASSWORD', 'PULSE_QUEUE')
        secrets = self.taskcluster.get_secrets(secrets_path, required)

        # Use pulse consumer from bot_common
        self.consumer = create_consumer(
            secrets['PULSE_USER'],
            secrets['PULSE_PASSWORD'],
            secrets['PULSE_QUEUE'],
            secrets.get('PULSE_TOPIC', '#'),
            self.got_message
        )

    def load_hooks(self, hooks):
        """
        Load task payloads from hooks definitiions
        """
        assert len(hooks) > 0, \
            'Missing hooks definitions'

        service = self.taskcluster.get_hooks_service()
        for hook in hooks:

            # Get hook definitions
            result = HOOK_REGEX.search(hook)
            if result is None:
                logger.warn('Invalid hook definition', definition=hook)
                continue

            hookGroupId, hookId = result.groups()
            logger.info('Using hook definition', group=hookGroupId, id=hookId)

            # Get task payload from hook
            hook_payload = service.hook(hookGroupId, hookId)
            self.tasks.append(hook_payload['task'])

        if not self.tasks:
            raise Exception('No tasks to run.')

    def run(self, hooks):

        # Load hook group/id combos
        self.load_hooks(hooks)

        # Run forever consumer below
        logger.info('Listening for new messages...')
        run_consumer(self.consumer)

    async def got_message(self, channel, body, envelope, properties):
        """
        Pulse consumer callback
        """
        assert isinstance(body, bytes), \
            'Body is not in bytes'

        # Extract bugzilla id from body
        body = json.loads(body.decode('utf-8'))
        if 'payload' not in body:
            raise Exception('Missing payload in body')
        bugzilla_id = body['payload'].get('id')
        if not bugzilla_id:
            raise Exception('Missing bugzilla id')
        logger.info('Received new Bugzilla message', bz_id=bugzilla_id)

        # Start new tasks for every bugzilla id
        env = {
            'BUGZILLA_ID': bugzilla_id,
        }
        for task in self.tasks:
            self.run_task(copy.deepcopy(task), extra_env=env)

        # Ack the message so it is removed from the broker's queue
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    def run_task(self, task_definition, ttl=5, extra_env={}):
        """
        Create a new task on Taskcluster
        """
        assert isinstance(task_definition, dict)

        # Update the env in task
        task_definition['payload']['env'].update(extra_env)

        # Get taskcluster queue
        queue = self.taskcluster.get_queue_service()

        # Build task id
        task_id = slugId().decode('utf-8')

        # Set dates
        now = datetime.utcnow()
        task_definition['created'] = now
        task_definition['deadline'] = now + timedelta(seconds=ttl * 3600)
        logger.info('Creating a new task', id=task_id, name=task_definition['metadata']['name'])  # noqa

        # Create a new task
        return queue.createTask(task_id, task_definition)
