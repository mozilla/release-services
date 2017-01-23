import hglib
import os
from releng_common import log


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

    def update(self):
        """
        Initially clone the repository
        or try to update it
        """
        config = [
            # Use purge extension
            b'extensions.purge=',
        ]

        # Use CA certs from OS env (docker)
        cacert = os.environ.get('SSL_CERT_FILE')
        if cacert:
            config.append('web.cacerts={}'.format(cacert).encode('utf-8'))
            logger.debug('Using cacert', path=cacert)

        try:
            # Update local copy
            self.client = hglib.open(self.directory, configs=config)
            logger.info('Updating existing local repository...')
            self.client.update()
        except Exception:
            # Initial clone, with a manual command to support ca certs
            logger.info('No local repository found in cache, cloning...')
            clone_cfg = cacert and 'web.cacerts={}'.format(cacert) or None
            cmd = hglib.util.cmdbuilder('clone',
                                        self.url,
                                        self.directory,
                                        uncompressed=True,
                                        config=clone_cfg)
            cmd.insert(0, hglib.HGPATH)
            proc = hglib.util.popen(cmd)
            out, err = proc.communicate()
            if proc.returncode:
                raise hglib.error.CommandError(cmd, proc.returncode, out, err)

            self.client = hglib.open(self.directory, configs=config)

        # Make sure purge extension is available
        assert (b'extensions', b'purge', b'') in self.client.config(), \
            'Missing mercurial purge extension'

    def is_mergeable(self, revision, branch):
        """
        Test if a revision is mergeable on a branch
        """
        logger.info('Merge test', revision=revision, branch=branch)

        # Switch branch
        # 1) `hg pull` the destination changeset
        # and the changeset(s) you wish to test
        self.client.update(branch)

        # 2) `hg purge --all --dirs`
        self.client.rawcommand([b'purge', b'--all', b'--dirs'])

        # 3) `hg update --clean DESTREV`
        self.client.rawcommand([b'update', b'--clean'])

        # 4) `hg graft --tool :merge REV [REV ...]`
        cmd = [
            b'graft',
            b'--tool', b':merge',
            revision,
        ]
        try:
            self.client.rawcommand(cmd)
            logger.info('Merge success', revision=revision, branch=branch)

            # TODO: rollback ?
        except hglib.error.CommandError as e:
            logger.warning('Auto merge failed for {} on {}'.format(revision, branch), error=e)  # noqa

            # Clean your mess
            self.client.rawcommand([b'update', b'--clean'])
            self.client.rawcommand([b'purge'])

            return False

        # If `hg graft` exits code 0, there are no merge conflicts.
        return True
