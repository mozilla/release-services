import hglib
import os
import re
from shipit_bot_uplift import log


logger = log.get_logger('shipit_bot')
REGEX_TIP = re.compile(r'(\w+)\s*(tip)? (\w+)')


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
        assert isinstance(branch, bytes)

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

        # Check branch has been successfull checkout
        identify = self.client.identify().decode('utf-8')
        parent, _, current_branch = REGEX_TIP.search(identify).groups()
        assert current_branch == branch.decode('utf-8'), \
            'Current branch {} is not expected branch {}'.format(current_branch, branch)  # noqa
        logger.info('Checkout success', branch=branch, tip=parent)

        return parent

    def is_mergeable(self, revision):
        """
        Test if a revision is mergeable on current branch
        """
        # Use revision in bytes (needed by hglib)
        if isinstance(revision, int):
            revision = str(revision).encode('utf-8')
        assert isinstance(revision, bytes)

        logger.info('Merge test', revision=revision)

        # 4) `hg graft --tool :merge REV [REV ...]`
        cmd = [
            b'graft',
            b'--tool', b':merge',
            revision,
        ]
        try:
            self.client.rawcommand(cmd)
            logger.info('Merge success', revision=revision)
        except hglib.error.CommandError as e:
            logger.warning('Auto merge failed', revision=revision, error=e)  # noqa
            message = '{} {}'.format(
                e.out.decode('utf-8'),
                e.err.decode('utf-8')
            )
            message = message.replace('\r', '\n')
            return False, message

        # If `hg graft` exits code 0, there are no merge conflicts.
        return True, 'merge success'

    def cleanup(self, parent):
        """
        Cleanup the client state, used after a graft
        """
        try:
            self.client.update(rev=parent, clean=True)
        except hglib.error.CommandError as e:
            logger.warning('Cleanup failed', error=e)

        # Check parent revision got reverted
        assert parent in self.client.identify().decode('utf-8'), \
            'Failed to revert to parent revision'


if __name__ == '__main__':
    import tempfile
    repo = Repository(
        'https://hg.mozilla.org/mozilla-unified',
        os.path.join(tempfile.gettempdir(), 'mozilla-unified')
    )
    repo.checkout('beta')
