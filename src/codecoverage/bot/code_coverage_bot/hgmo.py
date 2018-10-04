# -*- coding: utf-8 -*-
import os
import signal
import subprocess

import requests

from cli_common.log import get_logger

logger = get_logger(__name__)


class HGMO(object):

    PID_FILE = 'hgmo.pid'

    def __init__(self, repo_dir):
        self.repo_dir = repo_dir
        self.pid_file = os.path.join(os.getcwd(),
                                     HGMO.PID_FILE)

    def __get_pid(self):
        with open(self.pid_file, 'r') as In:
            pid = In.read()
            return int(pid)

    def __enter__(self):
        proc = subprocess.Popen(['hg', 'serve',
                                 '--hgmo',
                                 '--daemon',
                                 '--pid-file', self.pid_file],
                                cwd=self.repo_dir)
        proc.wait()

        logger.info('hgmo is running', pid=self.__get_pid())

        return self

    def __exit__(self, type, value, traceback):
        pid = self.__get_pid()
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        os.remove(self.pid_file)
        logger.info('hgmo has been killed')

    def get_pushes(self, startID=None, changeset=None):
        assert startID is not None or changeset is not None

        params = {
            'version': 2,
            'full': 1
        }

        if startID is not None:
            params['startID'] = startID

        if changeset is not None:
            params['changeset'] = changeset

        r = requests.get('http://localhost:8000/json-pushes', params=params)

        r.raise_for_status()
        return r.json()

    def get_push_changesets(self, changeset):
        push_data = self.get_pushes(changeset=changeset)

        return sum((data['changesets'] for data in push_data['pushes'].values()), [])

    def get_annotate(self, revision, path):
        r = requests.get('http://localhost:8000/json-annotate/{}/{}'.format(revision, path))

        r.raise_for_status()
        annotate_data = r.json()

        if 'not found in manifest' in annotate_data:
            # The file was removed.
            return None

        return annotate_data['annotate']
