import taskcluster
import re
import logging

logger = logging.getLogger(__name__)


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

    def build_options(self, service_endpoint):
        """
        Build Taskcluster credentials options
        """

        if self.client_id and self.access_token:
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

    def get_secrets_service(self):
        """
        Configured Secrets Service
        """
        return taskcluster.Secrets(
            self.build_options('secrets/v1')
        )

    def get_hooks_service(self):
        """
        Configured Hooks Service
        """
        return taskcluster.Hooks(
            self.build_options('hooks/v1')
        )

    def get_queue_service(self):
        """
        Configured Queue Service
        """
        return taskcluster.Queue(
            self.build_options('queue/v1')
        )

    def get_notify_service(self):
        """
        Configured Queue Service
        """
        return taskcluster.Notify(
            self.build_options('notify/v1')
        )

    def get_secrets(self, path, required=[]):
        """
        Get secrets from a specific path
        and check mandatory ones
        """
        secrets = self.get_secrets_service().get(path)
        secrets = secrets['secret']
        for req in required:
            if req not in secrets:
                raise Exception('Missing value {} in Taskcluster secret value {}'.format(req, path))  # noqa

        return secrets

    def notify_email(self, address, subject, content, template='simple'):
        """
        Send an email through Taskcluster notification service
        """
        return self.get_notify_service().email({
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
