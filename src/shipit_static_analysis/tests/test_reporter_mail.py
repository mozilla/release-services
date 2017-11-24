# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import responses
import pytest
import json


@responses.activate
def test_conf(mock_config):
    '''
    Test mail reporter configuration
    '''
    from shipit_static_analysis.report.mail import MailReporter

    # Missing emails conf
    with pytest.raises(AssertionError):
        MailReporter({}, 'test_tc', 'token_tc')

    # Missing emails
    conf = {
        'emails': [],
    }
    with pytest.raises(AssertionError):
        MailReporter(conf, 'test_tc', 'token_tc')

    # Valid emails
    conf = {
        'emails': [
            'test@mozilla.com',
        ],
    }
    r = MailReporter(conf, 'test_tc', 'token_tc')
    assert r.emails == ['test@mozilla.com', ]

    conf = {
        'emails': [
            'test@mozilla.com',
            'test2@mozilla.com',
            'test3@mozilla.com',
        ],
    }
    r = MailReporter(conf, 'test_tc', 'token_tc')
    assert r.emails == ['test@mozilla.com', 'test2@mozilla.com', 'test3@mozilla.com']


@responses.activate
def test_mail(mock_config, mock_issues):
    '''
    Test mail sending through Taskcluster
    '''
    from shipit_static_analysis.report.mail import MailReporter
    from shipit_static_analysis.config import settings
    settings.setup('test')  # app channel used in title

    def _check_email(request):
        payload = json.loads(request.body)

        assert payload['subject'] == '[test] New Static Analysis Review #12345'
        assert payload['address'] == 'test@mozilla.com'
        assert payload['template'] == 'fullscreen'
        assert payload['content'].startswith('3 Publishable issues on Mozreview')

        return (200, {}, '')  # ack

    # Add mock taskcluster email to check output
    responses.add_callback(
        responses.POST,
        'https://notify.taskcluster.net/v1/email',
        callback=_check_email,
    )

    # Publish email
    conf = {
        'emails': [
            'test@mozilla.com',
        ],
    }
    r = MailReporter(conf, 'test_tc', 'token_tc')
    r.publish(mock_issues, '12345', '1', diff_url=None)
