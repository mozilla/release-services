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
        if client_id and access_token:
            # Use provided credentials
            self.options = {
                'credentials': {
                    'clientId': client_id,
                    'accessToken': access_token,
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
            base_url = 'http://{}/secrets/v1'.format(hosts['taskcluster'])
            logger.info('Taskcluster Proxy enabled', url=base_url)
            self.options = {
                'baseUrl': base_url
            }

    def get_secret(self, path):
        """
        Get secret from a specific path
        """
        secrets = taskcluster.Secrets(self.options).get(path)
        return secrets['secret']

    def notify_email(self, address, subject, content):
        """
        Send an email through Taskcluster notification service
        """
        notify = taskcluster.Notify(self.options)
        return notify.email({
            'address': address,
            'subject': subject,
            'content': content,
        })

    def read_hosts():
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
