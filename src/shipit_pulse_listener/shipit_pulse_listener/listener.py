from cli_common.pulse import run_consumer
from cli_common.log import get_logger
from shipit_pulse_listener.hook import Hook
import asyncio

logger = get_logger(__name__)


class HookStaticAnalysis(Hook):
    """
    Taskcluster hook handling the static analysis
    """
    def __init__(self, configuration):
        assert 'hookId' in configuration
        super().__init__(
            'project-releng',
            configuration['hookId'],
            'exchange/mozreview/',
            'mozreview.commits.published',
        )

    def parse_payload(self, payload):
        """
        Extract revisions from payload
        """
        # Filter on repo url
        repository_url = payload.get('repository_url')
        if not repository_url:
            raise Exception('Missing repository url in payload')
        if repository_url != 'https://reviewboard-hg.mozilla.org/gecko':
            logger.warn('Skipping this message, invalid repository url', url=repository_url)  # noqa
            return

        # Extract commits
        commits = [
            '{rev}:{review_request_id}:{diffset_revision}'.format(**c)
            for c in payload.get('commits', [])
        ]
        logger.info('Received new commits', commits=commits)
        return {
            'COMMITS': ' '.join(commits),
        }


class HookRiskAssessment(Hook):
    """
    Taskcluster hook handling the risk assessment
    """
    def __init__(self, configuration):
        assert 'hookId' in configuration
        super().__init__(
            'project-releng',
            configuration['hookId'],
            'exchange/hgpushes/v2',
        )

    def parse_payload(self, payload):
        """
        Extract revisions from payload
        """
        # Use only changesets
        if payload.get('type') != 'changegroup.1':
            return

        # TODO: filter on pushlog ?
        data = payload.get('data')
        assert isinstance(data, dict)
        assert 'heads' in data

        logger.info('Received new pushes', revisions=data['heads'])
        return {
            # Most of the time only one revision is pushed
            # http://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/notifications.html#changegroup-1  # noqa
            'REVISIONS': ' '.join(data['heads'])
        }


class PulseListener(object):
    """
    Listen to pulse messages and trigger new tasks
    """
    def __init__(self, pulse_user, pulse_password, pulse_listener_hooks):

        self.pulse_user = pulse_user
        self.pulse_password = pulse_password
        self.pulse_listener_hooks = pulse_listener_hooks

    def run(self):

        # Build hooks for each conf
        hooks = [
            self.build_hook(conf)
            for conf in self.pulse_listener_hooks
        ]

        # Run hooks pulse listeners together
        # but only use hoks with active definitions
        consumers = [
            hook.connect_pulse(self.pulse_user, self.pulse_password)
            for hook in hooks
            if hook.connect_taskcluster()
        ]
        run_consumer(asyncio.gather(*consumers))

    def build_hook(self, conf):
        """
        Build a new hook instance according to configuration
        """
        assert isinstance(conf, dict)
        assert 'type' in conf
        classes = {
            'static-analysis': HookStaticAnalysis,
            'risk-assessment': HookRiskAssessment,
        }
        hook_class = classes.get(conf['type'])
        if hook_class is None:
            raise Exception('Unsupported hook {}'.format(conf['hook']))

        return hook_class(conf)
