import hglib
import os
from shipit_bot_uplift import log


logger = log.get_logger('shipit_bot')


class Repository(object):
    """
    Maintains an updated mercurial repository
    """

    def __init__(self, url, directory):
        self.url = url
        self.directory = directory
        self.client = None
        logger.info('Mercurial repository', url=self.url, directory=self.directory)  # noqa

    def checkout(self, branch):
        """
        Robust Checkout of the repository
        using configured mercurial client with extensions
        """
        # Build command line
        repo_dir = os.path.join(self.directory, 'repo')
        shared_dir = os.path.join(self.directory, 'shared')
        logger.info('Updating repo', dir=repo_dir, branch=branch)
        cmd = hglib.util.cmdbuilder('robustcheckout',
                                    self.url,
                                    repo_dir,
                                    purge=True,
                                    sharebase=shared_dir,
                                    branch=branch)
        cmd.insert(0, hglib.HGPATH)

        # Run Command
        proc = hglib.util.popen(cmd)
        out, err = proc.communicate()
        if proc.returncode:
            raise hglib.error.CommandError(cmd, proc.returncode, out, err)

        # Use new high level mercurial client
        self.client = hglib.open(repo_dir)

        # Setup callback prompt
        def _cb(max_length, data):
            logger.info('Received data from HG', data=data)

            # Use new file when it exists
            if b'(c)hanged' in data:
                return b'c\n'

            # Send unresolved
            return b'u\n'
        self.client.setcbprompt(_cb)

    def is_mergeable(self, revision, branch):
        """
        Test if a revision is mergeable on a branch
        """
        # Use revision in bytes (needed by hglib)
        if isinstance(revision, int):
            revision = str(revision).encode('utf-8')
        assert isinstance(revision, bytes)

        logger.info('Merge test', revision=revision, branch=branch)

        # Switch to branch
        self.checkout(branch)

        # 4) `hg graft --tool :merge REV [REV ...]`
        cmd = [
            b'graft',
            b'--tool', b':merge',
            revision,
        ]
        try:
            self.client.rawcommand(cmd)
            logger.info('Merge success', revision=revision, branch=branch)
        except hglib.error.CommandError as e:
            logger.warning('Auto merge failed', revision=revision, branch=branch, error=e)  # noqa
            return False

        # If `hg graft` exits code 0, there are no merge conflicts.
        return True


if __name__ == '__main__':
    import tempfile
    repo = Repository(
        'https://hg.mozilla.org/mozilla-unified',
        os.path.join(tempfile.gettempdir(), 'mozilla-unified')
    )
    repo.checkout('beta')
