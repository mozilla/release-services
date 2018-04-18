# -*- coding: utf-8 -*-
# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import json

import responses


@responses.activate
def test_mail(mock_taskcluster_credentials):
    '''
    Test uplift merge failures email report
    '''
    from shipit_bot_uplift.report import Report
    from shipit_bot_uplift.merge import MergeTest

    def _check_email(request):
        payload = json.loads(request.body)

        assert payload['subject'] == '[test] Uplift bot detected 2 merge failures to beta, esr52'
        assert payload['address'] == 'test@mozilla.com'
        assert payload['template'] == 'fullscreen'
        assert payload['content'].startswith('# Failed automated merge test')

        return (200, {}, '')  # ack

    # Add mock taskcluster email to check output
    responses.add_callback(
        responses.POST,
        'https://notify.taskcluster.net/v1/email',
        callback=_check_email,
    )

    report = Report(['test@mozilla.com'])
    report.add_invalid_merge(MergeTest('123456', 'beta', []))
    report.add_invalid_merge(MergeTest('123456', 'esr52', []))
    report.send('test')
