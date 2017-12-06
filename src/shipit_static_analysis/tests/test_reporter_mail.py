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
def test_mail(mock_issues, mock_phabricator):
    '''
    Test mail sending through Taskcluster
    '''
    from shipit_static_analysis.report.mail import MailReporter
    from shipit_static_analysis.revisions import MozReviewRevision, PhabricatorRevision
    from shipit_static_analysis.report.phabricator import PhabricatorReporter

    phab = PhabricatorReporter({
        'url': 'http://phabricator.test/api/',
        'api_key': 'deadbeef',
    })

    def _check_email(request):
        payload = json.loads(request.body)

        assert payload['subject'] in (
            '[test] New Static Analysis MozReview #12345 - 1',
            '[test] New Static Analysis Phabricator #42 - PHID-DIFF-test',
        )
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

    # Publish for mozreview
    mrev = MozReviewRevision('abcdef:12345:1')
    r.publish(mock_issues, mrev, diff_url=None)

    prev = PhabricatorRevision('42:PHID-DIFF-test', phab)
    r.publish(mock_issues, prev, diff_url=None)
