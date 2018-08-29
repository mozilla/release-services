# -*- coding: utf-8 -*-
import os

import requests

from cli_common.command import run_check
from cli_common.taskcluster import get_service
from cli_common.utils import retry
from shipit_code_coverage.secrets import secrets


class GitHubUtils(object):

    def __init__(self, cache_root, client_id, access_token):
        self.cache_root = cache_root
        self.gecko_dev_user = secrets.get(secrets.GECKO_DEV_USER)
        self.gecko_dev_pwd = secrets.get(secrets.GECKO_DEV_PWD)
        self.hg_git_mapper = secrets[secrets.HG_GIT_MAPPER] if secrets.HG_GIT_MAPPER in secrets else 'https://mapper.mozilla-releng.net'
        self.client_id = client_id
        self.access_token = access_token

    def update_geckodev_repo(self):
        if self.gecko_dev_user is None or self.gecko_dev_pwd is None:
            return

        run_check(['git', 'config', '--global', 'http.postBuffer', '12M'])
        repo_url = 'https://%s:%s@github.com/marco-c/gecko-dev' % (self.gecko_dev_user, self.gecko_dev_pwd)
        repo_path = os.path.join(self.cache_root, 'gecko-dev')

        if not os.path.isdir(repo_path):
            retry(lambda: run_check(['git', 'clone', repo_url], cwd=self.cache_root))
        retry(lambda: run_check(['git', 'pull', 'https://github.com/mozilla/gecko-dev', 'master'], cwd=repo_path))
        retry(lambda: run_check(['git', 'push', repo_url, 'master'], cwd=repo_path))

    def post_github_status(self, commit_sha):
        if self.gecko_dev_user is None or self.gecko_dev_pwd is None:
            return

        tcGithub = get_service('github', self.client_id, self.access_token)
        tcGithub.createStatus('marco-c', 'gecko-dev', commit_sha, {
            'state': 'success',
        })

    def mercurial_to_git(self, mercurial_commit):
        def mercurial_to_git():
            r = requests.get('{}/gecko-dev/rev/hg/{}'.format(self.hg_git_mapper, mercurial_commit))

            if not r.ok:
                raise Exception('Mercurial commit is not available yet on mozilla/gecko-dev.')

            return r.text.split(' ')[0]

        return retry(mercurial_to_git, retries=30)

    def git_to_mercurial(self, github_commit):
        def mercurial_to_git():
            r = requests.get('{}/gecko-dev/rev/git/{}'.format(self.hg_git_mapper, github_commit))

            if not r.ok:
                raise Exception('Failed mapping git commit to mercurial commit.')

            return r.text.split(' ')[1]

        return retry(mercurial_to_git, retries=30)

    def update_codecoveragereports_repo(self):
        if self.gecko_dev_user is None or self.gecko_dev_pwd is None:
            return

        run_check(['git', 'config', '--global', 'http.postBuffer', '12M'])
        run_check(['git', 'config', '--global', 'user.email', 'report@upload.it'])
        run_check(['git', 'config', '--global', 'user.name', 'Report Uploader'])
        repo_url = 'https://%s:%s@github.com/marco-c/code-coverage-reports' % (self.gecko_dev_user, self.gecko_dev_pwd)
        run_check(['git', 'init'])
        run_check(['git', 'add', '*'])
        run_check(['git', 'commit', '-m', 'Coverage reports upload'])
        retry(lambda: run_check(['git', 'push', repo_url, 'master', '--force']))
