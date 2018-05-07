# -*- coding: utf-8 -*-
import os
import signal
import subprocess

from cli_common.log import get_logger

logger = get_logger(__name__)


class HGMO(object):

    PID_FILE = '/tmp/hgmo.pid'

    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

    def __get_pid(self):
        with open(HGMO.PID_FILE, 'r') as In:
            pid = In.read()
            return int(pid)

    def __enter__(self):
        proc = subprocess.Popen(['hg', 'serve',
                                 '--hgmo',
                                 '--daemon',
                                 '--pid-file', HGMO.PID_FILE],
                                cwd=self.repo_dir)
        proc.wait()

        logger.info('hgmo is running', pid=self.__get_pid())

        return 'http://localhost:8000'

    def __exit__(self, type, value, traceback):
        pid = self.__get_pid()
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        logger.info('hgmo has been killed')
