# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import responses
import itertools
import httpretty
import os.path
import pytest
import hglib
import time
import json
import re

MOCK_DIR = os.path.join(os.path.dirname(__file__), 'mocks')


@responses.activate
@pytest.fixture(scope='session')
def mock_config():
    '''
    Mock configuration for bot
    '''
    path = os.path.join(MOCK_DIR, 'config.yaml')
    responses.add(
        responses.GET,
        'https://hg.mozilla.org/mozilla-central/raw-file/tip/tools/clang-tidy/config.yaml',
        body=open(path).read(),
        content_type='text/plain',
    )

    from shipit_static_analysis.config import settings
    settings.setup('test')
    return settings


@pytest.fixture
def mock_repository(tmpdir):
    '''
    Create a dummy mercurial repository
    '''
    # Init repo
    repo_dir = str(tmpdir.mkdir('repo').realpath())
    hglib.init(repo_dir)

    # Init clean client
    client = hglib.open(repo_dir)
    client.directory = repo_dir

    # Add test.txt file
    path = os.path.join(repo_dir, 'test.txt')
    with open(path, 'w') as f:
        f.write('Hello World\n')

    # Initiall commit
    client.add(path.encode('utf-8'))
    client.commit(b'Hello World', user=b'Tester')

    return client


@pytest.fixture
def mock_issues():
    '''
    Build a list of dummy issues
    '''

    class MockIssue(object):
        def __init__(self, nb):
            self.nb = nb

        def as_markdown(self):
            return str(self.nb)

        def as_text(self):
            return str(self.nb)

        def is_publishable(self):
            return self.nb % 2 == 0

    return [
        MockIssue(i)
        for i in range(5)
    ]


@pytest.fixture(scope='session')
def mock_mozreview():
    '''
    Mock mozreview authentication process
    Need to use httpretty as mozreview uses low level urlopen
    '''
    api_url = 'http://mozreview.test/api/'
    auth_url = api_url + 'extensions/mozreview.extension.MozReviewExtension/bugzilla-api-key-logins/'

    def _response(name):
        path = os.path.join(MOCK_DIR, 'mozreview_{}.json'.format(name))
        assert os.path.exists(path)
        return open(path).read()

    # Start httpretty session
    httpretty.enable()

    # API Root endpoint
    httpretty.register_uri(
        httpretty.GET,
        api_url,
        body=_response('root'),
        content_type='application/vnd.reviewboard.org.bugzilla-api-key-logins+json',
    )

    # Initial query to get auth endpoints
    httpretty.register_uri(
        httpretty.GET,
        auth_url,
        body=_response('auth'),
        content_type='application/vnd.reviewboard.org.bugzilla-api-key-logins+json',
    )

    def _check_credentials(request, uri, headers):

        # Dirty multipart form data "parser"
        form = dict(re.findall(r'name="([\w_]+)"\r\n\r\n(\w+)\r\n', request.body.decode('utf-8')))
        assert form['username'] == 'devbot'
        assert form['api_key'] == 'deadbeef123'

        body = json.dumps({
            'stat': 'ok',
            'bugzilla_api_key_login': {
                'email': 'devbot@mozilla.org',
            },
        })
        return (201, headers, body)

    # Initial query to get auth endpoints
    httpretty.register_uri(
        httpretty.POST,
        auth_url,
        status_code=201,
        body=_check_credentials,
        content_type='application/vnd.reviewboard.org.bugzilla-api-key-logins+json',
    )

    # Pass context to test runtime
    yield

    # Close httpretty session
    httpretty.disable()


@pytest.fixture
def mock_phabricator():
    '''
    Mock phabricator authentication process
    '''
    def _response(name):
        path = os.path.join(MOCK_DIR, 'phabricator_{}.json'.format(name))
        assert os.path.exists(path)
        return open(path).read()

    responses.add(
        responses.POST,
        'http://phabricator.test/api/user.whoami',
        body=_response('auth'),
        content_type='application/json',
    )

    responses.add(
        responses.POST,
        'http://phabricator.test/api/differential.diff.search',
        body=_response('diff_search'),
        content_type='application/json',
    )

    responses.add(
        responses.POST,
        'http://phabricator.test/api/differential.revision.search',
        body=_response('revision_search'),
        content_type='application/json',
    )

    responses.add(
        responses.POST,
        'http://phabricator.test/api/differential.query',
        body=_response('diff_query'),
        content_type='application/json',
    )

    responses.add(
        responses.POST,
        'http://phabricator.test/api/differential.getrawdiff',
        body=_response('diff_raw'),
        content_type='application/json',
    )


@pytest.fixture(scope='session')
def mock_stats(mock_config):
    '''
    Mock Datadog authentication and stats management
    '''
    from shipit_static_analysis import stats

    # Configure Datadog with a dummy token
    # and an ultra fast flushing cycle
    stats.auth('test_token')
    stats.api.stop()
    stats.api.start(flush_interval=0.001)
    assert not stats.api._disabled
    assert stats.api._is_auto_flushing

    class MemoryReporter(object):
        '''
        A reporting class that reports to memory for testing.
        Used in datadog unit tests:
        https://github.com/DataDog/datadogpy/blob/master/tests/unit/threadstats/test_threadstats.py
        '''
        def __init__(self, api):
            self.metrics = []
            self.events = []
            self.api = api

        def flush_metrics(self, metrics):
            self.metrics += metrics

        def flush_events(self, events):
            self.events += events

        def flush(self):
            # Helper for unit tests to force flush
            self.api.flush(time.time() + 20)

        def get_metrics(self, metric_name):
            return list(itertools.chain(*[
                m['points']
                for m in self.metrics
                if m['metric'] == metric_name
            ]))

    # Gives reporter access to unit tests to access metrics
    stats.api.reporter = MemoryReporter(stats.api)
    yield stats.api.reporter


@pytest.fixture
def mock_revision():
    '''
    Mock a mercurial revision
    '''
    from shipit_static_analysis.revisions import Revision
    rev = Revision()
    rev.mercurial = 'a6ce14f59749c3388ffae2459327a323b6179ef0'
    return rev
