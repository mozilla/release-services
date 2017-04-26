from cli_common.log import get_logger
from cli_common.taskcluster import TaskclusterClient
from cli_common.mercurial import robust_checkout, MOZILLA_CENTRAL
from mocoda.compiledb import react as mocoda_react
import os

logger = get_logger(__name__)


class Bot(object):
    """
    Risk assessment analysis
    """
    def __init__(self, client_id=None, access_token=None):
        # Load taskcluster client (may be useful later on)
        self.taskcluster = TaskclusterClient(client_id, access_token)

        # Load mozconfig from env
        self.mozconfig_path = os.environ.get('MOZCONFIG')
        assert self.mozconfig_path is not None, \
            'Missing MOZCONFIG in env'
        assert os.path.exists(self.mozconfig_path), \
            'Invalid MOZCONFIG in {}'.format(self.mozconfig_path)

    def run(self, work_dir, merge_revision):
        """
        Main workflow
        """
        if not os.path.isdir(work_dir):
            os.makedirs(work_dir)

        # Clone mozilla central
        repo_dir = os.path.join(work_dir, 'central')
        logger.info('Clone Mozilla Central', dir=repo_dir)
        robust_checkout(MOZILLA_CENTRAL, repo_dir)

        # Setup mocoda environment
        tmp_dir = os.path.join(work_dir, 'tmp')
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir)
        os.environ['MOCODA_ROOT'] = repo_dir
        os.environ['MOCODA_TMPDIR'] = tmp_dir

        # Run mocoda react
        logger.info('Mocoda react', revision=merge_revision)
        mocoda_react(merge_revision)
