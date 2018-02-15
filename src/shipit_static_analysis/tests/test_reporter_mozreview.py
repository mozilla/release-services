# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import httpretty
import pytest
import re


def test_conf(mock_mozreview):
    '''
    Test mozreview reporter configuration
    '''
    from shipit_static_analysis.report.mozreview import MozReviewReporter

    # Missing emails conf
    with pytest.raises(AssertionError):
        MozReviewReporter({}, 'test_tc', 'token_tc')

    # Valid auth
    conf = {
        'username': 'devbot',
        'api_key': 'deadbeef123',
        'url': 'http://mozreview.test',
    }
    r = MozReviewReporter(conf, 'test_tc', 'token_tc')
    assert r.api is not None


def test_review_publication(mock_mozreview, mock_issues, mock_phabricator):
    '''
    Test publication of a single review
    '''
    from shipit_static_analysis.report.mozreview import MozReviewReporter
    from shipit_static_analysis.revisions import MozReviewRevision

    # Add mock files listing
    httpretty.register_uri(
        httpretty.POST,
        re.compile('http://mozreview.test/api/review-requests/(\d+)/diffs/(\w+)/files/'),
        body='{}',
    )

    # Publish issues on mozreview
    conf = {
        'username': 'devbot',
        'api_key': 'deadbeef123',
        'url': 'http://mozreview.test',
    }
    r = MozReviewReporter(conf, 'test_tc', 'token_tc')
    mrev = MozReviewRevision('abcdef:12345:1')
    out = r.publish(mock_issues, mrev, diff_url=None)
    assert out is None  # no publication (no clang-tidy)


def test_comment(mock_mozreview):
    '''
    Test comment creation for specific issues
    '''
    from shipit_static_analysis.clang.tidy import ClangTidyIssue
    from shipit_static_analysis.clang.format import ClangFormatIssue
    from shipit_static_analysis.lint import MozLintIssue
    from shipit_static_analysis.report.base import Reporter

    # Init dummy reporter
    class TestReporter(Reporter):
        def __init__(self):
            pass
    reporter = TestReporter()

    # Build clang tidy fake issue, while forcing publication status
    header = ('test.cpp', 1, 1, 'error', 'Dummy message', 'test-check')
    clang_tidy_publishable = ClangTidyIssue(header, '/tmp')
    clang_tidy_publishable.is_publishable = lambda: True
    assert clang_tidy_publishable.is_publishable()
    issues = [clang_tidy_publishable, ]

    assert reporter.build_comment(issues) == '''
Code analysis found 1 defect in this patch:
 - 1 defect found by clang-tidy

You can run this analysis locally with:
 - `./mach static-analysis check path/to/file.cpp` (C/C++)


If you see a problem in this automated review, please report it here: http://bit.ly/2y9N9Vx
'''

    # Now add a clang-format issue
    clang_format_publishable = ClangFormatIssue('/tmp/test.cpp', '', '', [1, 2], 'delete', 1, 2, 3, 4)
    clang_format_publishable.is_publishable = lambda: True
    assert clang_tidy_publishable.is_publishable()
    issues.append(clang_format_publishable)

    assert reporter.build_comment(issues) == '''
Code analysis found 2 defects in this patch:
 - 1 defect found by clang-format
 - 1 defect found by clang-tidy

You can run this analysis locally with:
 - `./mach clang-format -p path/to/file.cpp` (C/C++)
 - `./mach static-analysis check path/to/file.cpp` (C/C++)


If you see a problem in this automated review, please report it here: http://bit.ly/2y9N9Vx
'''

    # Now add a mozlint issue
    mozlint_publishable = MozLintIssue('/tmp', 'test.cpp', 1, 'error', 1, 'test', 'Dummy test', 'dummy rule')
    mozlint_publishable.is_publishable = lambda: True
    assert mozlint_publishable.is_publishable()
    issues.append(mozlint_publishable)

    assert reporter.build_comment(issues) == '''
Code analysis found 3 defects in this patch:
 - 1 defect found by clang-format
 - 1 defect found by clang-tidy
 - 1 defect found by mozlint

You can run this analysis locally with:
 - `./mach clang-format -p path/to/file.cpp` (C/C++)
 - `./mach static-analysis check path/to/file.cpp` (C/C++)
 - `./mach lint path/to/file` (JS/Python)


If you see a problem in this automated review, please report it here: http://bit.ly/2y9N9Vx
'''
