# -*- coding: utf-8 -*-

import requests

from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from cli_common.utils import retry
from code_coverage_bot import hgmo
from code_coverage_bot.secrets import secrets

logger = get_logger(__name__)


class ResultNotReadyException(Exception):
    pass


class Notifier(object):
    def __init__(self, repo_dir, revision, client_id, access_token):
        self.repo_dir = repo_dir
        self.revision = revision
        self.notify_service = get_service('notify', client_id, access_token)

    def get_coverage_summary(self, changeset):
        backend_host = secrets[secrets.BACKEND_HOST]

        r = requests.get('{}/coverage/changeset_summary/{}'.format(backend_host, changeset))
        r.raise_for_status()

        if r.status_code == 202:
            raise ResultNotReadyException()

        return r.json()

    def notify(self):
        content = ''

        # Get pushlog and ask the backend to generate the coverage by changeset
        # data, which will be cached.
        with hgmo.HGMO(self.repo_dir) as url:
            url += '/json-pushes'
            r = requests.get(url, params={'changeset': self.revision,
                                          'version': 2,
                                          'full': 1})

        r.raise_for_status()
        push_data = r.json()

        changesets = sum((data['changesets'] for data in push_data['pushes'].values()), [])

        for changeset in changesets:
            desc = changeset['desc'].split('\n')[0]

            if any(text in desc for text in ['r=merge', 'a=merge']):
                continue

            rev = changeset['node']

            try:
                coverage = retry(lambda: self.get_coverage_summary(rev))
            except (requests.exceptions.HTTPError, ResultNotReadyException):
                logger.warn('Failure to retrieve coverage summary')
                continue

            if coverage['commit_covered'] < 0.2 * coverage['commit_added']:
                content += '* [{}](https://firefox-code-coverage.herokuapp.com/#/changeset/{}): {} covered out of {} added.\n'.format(desc, rev, coverage['commit_covered'], coverage['commit_added'])  # noqa

        if content == '':
            return
        elif len(content) > 102400:
            # Content is 102400 chars max
            content = content[:102000] + '\n\n... Content max limit reached!'

        for email in secrets[secrets.EMAIL_ADDRESSES]:
            self.notify_service.email({
                'address': email,
                'subject': 'Coverage patches for {}'.format(self.revision),
                'content': content,
                'template': 'fullscreen',
            })
