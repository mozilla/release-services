import taskcluster
import re
from cli_common.log import get_logger

logger = get_logger(__name__)

with open(taskcluster._client_importer.__file__) as f:
    TASKCLUSTER_SERVICES = [
        line.split(' ')[1][1:]
        for line in f.read().split('\n')
        if line
    ]


class TaskclusterClient(object):
    """
    Simple taskcluster client interface
    """
    def __init__(self, client_id=None, access_token=None):
        """
        Build Taskcluster credentials options
        """
        self.client_id = client_id
        self.access_token = access_token

    def get_options(self, service_endpoint):
        """
        Build Taskcluster credentials options
        """

        if self.client_id is not None and self.access_token is not None:
            # Use provided credentials
            tc_options = {
                'credentials': {
                    'clientId': self.client_id,
                    'accessToken': self.access_token,
                }
            }

        else:
            # Get taskcluster proxy host
            # as /etc/hosts is not used in the Nix image (?)
            hosts = self.read_hosts()
            if 'taskcluster' not in hosts:
                raise Exception('Missing taskcluster in /etc/hosts')

            # Load secrets from TC task context
            # with taskclusterProxy
            base_url = 'http://{}/{}'.format(
                hosts['taskcluster'],
                service_endpoint
            )
            logger.info('Taskcluster Proxy enabled', url=base_url)
            tc_options = {
                'baseUrl': base_url
            }

        return tc_options

    def get_service(self, service):
        """
        Configured Hooks Service
        """
        if service not in TASKCLUSTER_SERVICES:
            raise Exception('Service `{}` does not exists.'.format(service))

        return getattr(taskcluster, service.capitalize())(
            self.get_options(service + '/v1')
        )

    def get_secrets(self, path, required=[]):
        """
        Get secrets from a specific path
        and check mandatory ones
        """
        secrets = self.get_service('secrets').get(path)
        secrets = secrets['secret']
        for req in required:
            if req not in secrets:
                raise Exception('Missing value {} in Taskcluster secret value {}'.format(req, path))  # noqa

        return secrets

    def get_hook_artifact(self, hook_group_id, hook_id, artifact_name):
        """
        Load an artifact from the last execution of an hook
        """

        # Get last run from hook
        hooks = self.get_service('hooks')
        hook_status = hooks.getHookStatus(hook_group_id, hook_id)
        last_fire = hook_status.get('lastFire')
        if last_fire is None:
            raise Exception('Hook did not fire')
        task_id = last_fire['taskId']

        # Get successful run for this task
        queue = self.get_service('queue')
        task_status = queue.status(task_id)
        if task_status['status']['state'] != 'completed':
            raise Exception('Task {} is not completed'.format(task_id))
        run_id = None
        for run in task_status['status']['runs']:
            if run['state'] == 'completed':
                run_id = run['runId']
                break
        if run_id is None:
            raise Exception('No completed run found')

        # Load artifact from task run
        return queue.getArtifact(task_id, run_id, artifact_name)

    def notify_email(self, address, subject, content, template='simple'):
        """
        Send an email through Taskcluster notification service
        """
        return self.get_service('notify').email({
            'address': address,
            'subject': subject,
            'content': content,
            'template': template,
        })

    def read_hosts(self):
        """
        Read /etc/hosts to get hostnames
        on a Nix env (used for taskclusterProxy)
        Only reads ipv4 entries to avoid duplicates
        """
        out = {}
        regex = re.compile('([\w:\-\.]+)')
        for line in open('/etc/hosts').readlines():
            if ':' in line:  # only ipv4
                continue
            x = regex.findall(line)
            if not x:
                continue
            ip, names = x[0], x[1:]
            out.update(dict(zip(names, [ip] * len(names))))

        return out
