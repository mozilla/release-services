from cli_common.pulse import run_consumer
from cli_common.taskcluster import TaskclusterClient
from cli_common.log import get_logger
from shipit_pulse_listener.hook import Hook
import asyncio

logger = get_logger(__name__)


class HookStaticAnalysis(Hook):
    """
    Taskcluster hook handling the static analysis
    """
    def __init__(self, branch):
        super().__init__(
            'project-releng',
            'services-{}-shipit-static-analysis-bot'.format(branch),
            'exchange/mozreview/',
            'mozreview.commits.published',
        )

    def parse_payload(self, payload):
        """
        Start new tasks for every bugzilla id
        """
        # Filter on repo url
        landing_repository_url = payload.get('landing_repository_url')
        if not landing_repository_url:
            raise Exception('Missing landinf repository url in payload')
        if 'reviewboard-hg.mozilla.org' not in landing_repository_url:
            logger.warn('Skipping this message, invalid landing repository url', url=landing_repository_url)  # noqa
            return

        # Extract commits
        commits = [c['rev'] for c in payload.get('commits', [])]
        logger.info('Received new commits', commits=commits)
        return {
            'REVISIONS': ' '.join(commits),
        }


class HookRiskAssessment(Hook):
    """
    Taskcluster hook handling the risk assessment
    """
    def __init__(self, branch):
        super().__init__(
            'project-releng',
            'services-{}-shipit-risk-assessment-bot'.format(branch),
            'exchange/hgpushes/v1',
        )

    def parse_payload(self, payload):
        """
        Start new tasks for every bugzilla id
        """
        bugzilla_id = payload.get('id')
        if not bugzilla_id:
            raise Exception('Missing bugzilla id')
        logger.info('Received new Bugzilla message', bz_id=bugzilla_id)

        return {
            'REVISION': bugzilla_id,
        }


class PulseListener(object):
    """
    Listen to pulse messages and trigger new tasks
    """
    def __init__(self, secrets_path, client_id=None, access_token=None):
        self.taskcluster = TaskclusterClient(client_id, access_token)

        # Fetch pulse credentials from TC secrets
        logger.info('Using secrets', path=secrets_path)
        required = ('PULSE_USER', 'PULSE_PASSWORD',)
        self.secrets = self.taskcluster.get_secrets(secrets_path, required)

    def run(self, branch):

        # Build hooks for branch
        hooks = [
            HookStaticAnalysis(branch),
            HookRiskAssessment(branch),
        ]

        # Run hooks pulse listeners together
        # but only use hoks with active definitions
        consumers = [
            hook.connect_pulse(self.secrets)
            for hook in hooks
            if hook.connect_taskcluster(self.taskcluster)
        ]
        run_consumer(asyncio.gather(*consumers))
