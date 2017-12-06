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
