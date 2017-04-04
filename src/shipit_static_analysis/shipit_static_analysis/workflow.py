from cli_common.taskcluster import TaskclusterClient
from cli_common.log import get_logger
import subprocess
import hglib
import os

logger = get_logger(__name__)

REPO_CENTRAL = b'https://hg.mozilla.org/mozilla-central'
REPO_REVIEW = b'https://reviewboard-hg.mozilla.org/gecko'


class Workflow(object):
    """
    Static analysis workflow
    """
    taskcluster = None

    def __init__(self, secrets_path, cache_root, client_id=None, client_token=None):  # noqa
        self.cache_root = cache_root
        assert os.path.isdir(self.cache_root), \
            "Cache root {} is not a dir.".format(self.cache_root)

        # Load secrets
        # TODO: use it later for publications on mozreview
        self.taskcluster = TaskclusterClient(client_id, client_token)
        self.taskcluster.get_secrets(secrets_path)

        # Clone mozilla-central
        self.repo_dir = os.path.join(self.cache_root, 'static-analysis')
        shared_dir = os.path.join(self.cache_root, 'static-analysis-shared')
        logger.info('Clone mozilla central', dir=self.repo_dir)
        cmd = hglib.util.cmdbuilder('robustcheckout',
                                    REPO_CENTRAL,
                                    self.repo_dir,
                                    purge=True,
                                    sharebase=shared_dir,
                                    branch=b'tip')

        cmd.insert(0, hglib.HGPATH)
        proc = hglib.util.popen(cmd)
        out, err = proc.communicate()
        if proc.returncode:
            raise hglib.error.CommandError(cmd, proc.returncode, out, err)

        # Open new hg client
        self.hg = hglib.open(self.repo_dir)

    def run(self, revision):
        """
        Run the static analysis workflow:
         * Pull revision from review
         * Checkout revision
         * Run static analysis
        """

        # Pull revision from review
        logger.info('Pull from review', revision=revision)
        self.hg.pull(source=REPO_REVIEW, rev=revision, update=True, force=True)

        # Run mach configure
        cmd = [
            './mach', 'configure'
        ]
        proc = subprocess.Popen(cmd, cwd=self.repo_dir)
        exit = proc.wait()

        print('Exit', exit)
