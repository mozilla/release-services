# -*- coding: utf-8 -*-
import hglib
import os
import re
from cli_common.log import get_logger


logger = get_logger(__name__)
REGEX_IDENTIFY = re.compile(r'([abcdef0-9]+) \(?([\w\-_]+)\)? (?:tip )?(\w+)')


class Repository(object):
    '''
    Maintains an updated mercurial repository
    '''

    def __init__(self, url, directory):
        self.url = url
        self.directory = directory
        self.remote_uri = None  # used to publish uplifts
        self.remote_ssh_config = {}
        self.client = None
        self.branch = None
        self.parent = None
        logger.info('Mercurial repository', url=self.url, directory=self.directory)  # noqa

    def checkout(self, branch):
        '''
        Robust Checkout of the repository
        using configured mercurial client with extensions
        '''
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

        # Clean update to branch
        self.client.update(branch, clean=True)

        # Check branch has been successfull checkout
        identify = self.client.identify().decode('utf-8')
        self.parent, _, current_branch = REGEX_IDENTIFY.search(identify).groups()
        assert current_branch == branch.decode('utf-8'), \
            'Current branch {} is not expected branch {}'.format(current_branch, branch)  # noqa
        logger.info('Checkout success', branch=branch, tip=self.parent)
        self.branch = branch  # store

        return self.parent

    def identify(self, revision):
        '''
        Identify a revision by retrieving its local numerical id
        '''
        if isinstance(revision, int):
            revision = str(revision).encode('utf-8')
        assert isinstance(revision, bytes)

        try:
            out = self.client.identify(num=True, rev=revision)
            return int(out)  # local id is numerical
        except hglib.error.CommandError as e:
            logger.warn('Failed to identify revision', rev=revision, error=e)

    def is_mergeable(self, revision):
        '''
        Test if a revision is mergeable on current branch
        Returns merge status and message (as tuple)
        '''
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
            message = ' '.join([
                e.out.decode('utf-8'),
                e.err.decode('utf-8')
            ])
            if 'already grafted to' in message:
                logger.info('Skipped merge', revision=revision, error=message)  # noqa
                return True, message

            message = message.replace('\r', '\n')
            logger.info('Auto merge failed', revision=revision, error=message)  # noqa
            return False, message

        # If `hg graft` exits code 0, there are no merge conflicts.
        return True, 'merge success'

    def cleanup(self):
        '''
        Cleanup the client state, used after a graft
        '''
        try:
            self.client.update(rev=self.branch, clean=True)
            self.client.branch(self.branch)
        except hglib.error.CommandError as e:
            logger.warning('Cleanup failed', error=e)

        # Check parent revision got reverted
        ids = self.client.identify().decode('utf-8')
        assert self.parent in ids or self.branch.decode('utf-8') in ids, \
            'Failed to revert to parent revision'

    def create_branch(self, branch_name):
        '''
        Always create a new branch
        Reset existing branch with same name to main branch tip
        '''
        assert isinstance(branch_name, bytes)

        branches = [
            branch
            for branch, _, _ in self.client.branches()
        ]
        if branch_name in branches:
            # Cleanup existing branch
            self.client.rawcommand([b'strip', self.branch])
            self.client.update(branch_name, clean=True)
        else:
            # New branch, created on next commit/graft
            self.client.branch(branch_name)
        logger.info('Switched to branch', branch=branch_name)

    def push(self, branch_name):
        '''
        Push a single branch to configured remote server
        through SSH
        Outputs push status
        '''
        assert isinstance(branch_name, bytes)
        assert self.remote_uri is not None
        assert isinstance(self.remote_uri, bytes)
        assert isinstance(self.remote_ssh_config, dict)

        # Build ssh config command line
        ssh_conf = 'ssh {}'.format(' '.join([
            '-o {}="{}"'.format(k, v)
            for k, v in self.remote_ssh_config.items()
        ])).encode('utf-8')

        try:
            return self.client.push(
                dest=self.remote_uri,
                rev=[branch_name, ],
                newbranch=True,
                ssh=ssh_conf,
                force=True,
            )
        except Exception as e:
            logger.error('Mercurial push failed', dest=self.remote_uri, branch=branch_name, error=e)  # noqa
            return False

    def amend(self, append_message):
        '''
        Amend the commit message from current revision
        by appending to current commit message
        '''
        assert isinstance(append_message, str)

        # Get tip revision
        tip = self.client.tip()

        # Modify it
        new_message = tip.desc + append_message.encode('utf-8')

        # Mark commit as draft
        self.client.phase(force=True, draft=True)

        # Amend the message
        logger.info('Amending last commit', message=new_message)
        return self.client.commit(message=new_message, amend=True)
