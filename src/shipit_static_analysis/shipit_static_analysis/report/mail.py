# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from cli_common import log
from shipit_static_analysis.report.base import Reporter
from shipit_static_analysis.config import settings
from cli_common.taskcluster import get_service

logger = log.get_logger(__name__)


EMAIL_HEADER = '''{nb_publishable} Publishable issues on Mozreview

Review Url: {review_url}
Diff Url: {diff_url}
'''


class MailReporter(Reporter):
    '''
    Send an email to admins through Taskcluster service
    '''
    def __init__(self, configuration, client_id, access_token):
        self.emails, = self.requires(configuration, 'emails')
        assert len(self.emails) > 0, 'Missing emails data'

        # Load TC services & secrets
        self.notify = get_service(
            'notify',
            client_id=client_id,
            access_token=access_token,
        )

        logger.info('Mail report enabled', emails=self.emails)

    def publish(self, issues, revision, diff_url=None):
        '''
        Send an email to administrators
        '''
        content = EMAIL_HEADER.format(
            review_url=revision.url,
            diff_url=diff_url or 'no clang-format diff',
            nb_publishable=sum([i.is_publishable() for i in issues]),
        )
        content += '\n\n'.join([i.as_markdown() for i in issues])
        if len(content) > 102400:
            # Content is 102400 chars max
            content = content[:102000] + '\n\n... Content max limit reached!'
        subject = '[{}] New Static Analysis {}'.format(settings.app_channel, revision)
        for email in self.emails:
            self.notify.email({
                'address': email,
                'subject': subject,
                'content': content,
                'template': 'fullscreen',
            })
