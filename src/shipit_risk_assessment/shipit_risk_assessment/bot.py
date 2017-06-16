# -*- coding: utf-8 -*-
from cli_common.log import get_logger
from cli_common.mercurial import robust_checkout, MOZILLA_CENTRAL
from mocoda.compiledb import react as mocoda_react
import os

logger = get_logger(__name__)


class Bot(object):
    '''
    Risk assessment analysis
    '''
    def __init__(self, work_dir):

        # Load mozconfig from env
        self.mozconfig_path = os.environ.get('MOZCONFIG')
        assert self.mozconfig_path is not None, \
            'Missing MOZCONFIG in env'
        assert os.path.exists(self.mozconfig_path), \
            'Invalid MOZCONFIG in {}'.format(self.mozconfig_path)

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

    def run(self, revision):
        '''
        Run mocoda react on a revision
        '''
        logger.info('Mocoda react', revision=revision)
        mocoda_react(revision)
