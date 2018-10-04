# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import responses


@responses.activate
def test_phabricator(tmpdir, mock_phabricator):
    '''
    Test Phabricator reporter
    '''
    from static_analysis_bot.report.phabricator import PhabricatorReporter
    from static_analysis_bot.revisions import PhabricatorRevision
    from static_analysis_bot.clang.tidy import ClangTidyIssue

    def _check_comment(request):
        assert request.body == 'FAIL'
        # payload = json.loads(request.body)

    responses.add_callback(
        responses.POST,
        'http://phabricator.test/api/differential.createcomment',
        callback=_check_comment,
    )

    with mock_phabricator as api:
        revision = PhabricatorRevision('PHID-DIFF-abcdef', api)
        reporter = PhabricatorReporter()
        reporter.setup_api(api)

    issue_parts = ('test.cpp', '42', '51', 'error', 'dummy message', 'dummy-check')
    issues = [
      ClangTidyIssue(issue_parts, revision)
    ]

    reporter.publish(issues, revision)

    # TODO: How to intercept the Phabricator review comment?
