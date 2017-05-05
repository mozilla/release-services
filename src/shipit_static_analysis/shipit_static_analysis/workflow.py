from cli_common.taskcluster import TaskclusterClient
from cli_common.log import get_logger
from cli_common.utils import run_command, run_gecko_command
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
        # Force cleanup to reset tip
        # otherwise previous pull are there
        self.hg.update(rev=b'tip', clean=True)

        # Get the tip revision
        tip = self.hg.identify(id=True).decode('utf-8').strip()

        # Pull revision from review
        logger.info('Pull from review', revision=revision)
        self.hg.pull(source=REPO_REVIEW, rev=revision, update=True, force=True)

        # Find modified files by this revision
        changeset = '{}:{}'.format(revision, tip)
        status = self.hg.status(change=[changeset, ])
        modified_files = [f.decode('utf-8') for _, f in status]
        logger.info('Modified files', files=modified_files)

        # mach configure
        run_gecko_command(['./mach', 'configure'], self.repo_dir)

        # Build CompileDB backend
        cmd = ['./mach', 'build-backend', '--backend=CompileDB']
        run_gecko_command(cmd, self.repo_dir)

        # Build exports
        run_gecko_command(['./mach', 'build', 'pre-export'], self.repo_dir)
        run_gecko_command(['./mach', 'build', 'export'], self.repo_dir)

        # Run static analysis through run-clang-tidy.py
        checks = [
            '-*',
            'modernize-loop-convert',
            'modernize-use-auto',
            'modernize-use-default',
            'modernize-raw-string-literal',
            'modernize-use-bool-literals',
            'modernize-use-override',
            'modernize-use-nullptr',
        ]
        cmd = [
            'run-clang-tidy.py',
            '-j', '18',
            '-p', 'obj-x86_64-pc-linux-gnu/',
            '-checks={}'.format(','.join(checks)),
        ] + modified_files
        clang_output = run_command(cmd, self.repo_dir)

        # TODO Analyse clang output
        logger.info('Clang output', output=clang_output)
