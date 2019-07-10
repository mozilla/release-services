# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib
import json
import os
import random
import re
import time
import urllib.parse
import uuid

import fakeredis
import pytest
import responses
import zstandard as zstd

import codecoverage_backend.backend

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture(autouse=True, scope='function')
def mock_secrets():
    '''
    Provide configuration through mock Taskcluster secrets
    '''
    from codecoverage_backend import taskcluster

    taskcluster.options = {
        'rootUrl': 'http://taskcluster.test',
    }
    taskcluster.secrets = {
        'REDIS_URL': 'redis://unitest:1234',
        'APP_CHANNEL': 'test',
        'GOOGLE_CLOUD_STORAGE': {
            'token_uri': 'secret',
            'client_email': 'xxx@mozilla.test',
            'private_key': 'somethingHere',
            'bucket': 'unittest',
        }
    }


@pytest.fixture
def app(mock_secrets):
    '''
    Load codecoverage_backend app in test mode
    '''

    app = codecoverage_backend.backend.build_flask_app(
        project_name='Test',
        app_name='test',
        openapi=os.path.join(os.path.dirname(__file__), '../codecoverage_backend/api.yml')
    )

    with app.app.app_context():
        yield app.app


@pytest.fixture
def client(app):
    yield app.test_client()


@pytest.fixture
def mock_bucket(mock_secrets):
    '''
    Mock a GCP bucket & blobs
    '''
    class MockBlob(object):
        def __init__(self, name, content=None, exists=False):
            self.name = name
            if content is not None:
                assert isinstance(content, bytes)

                # Auto zstandard compression
                if self.name.endswith('.zstd'):
                    compressor = zstd.ZstdCompressor()
                    self._content = compressor.compress(content)
                else:
                    self._content = content
            else:
                self._content = None
            self._exists = exists

        def exists(self):
            return self._exists

        def download_to_filename(self, path):
            assert self._exists and self._content
            with open(path, 'wb') as f:
                f.write(self._content)

    class MockBucket(object):
        _blobs = {}

        def add_mock_blob(self, name, coverage=0.0):
            content = json.dumps({
                'coveragePercent': coverage,
                'children': {}
            }).encode('utf-8')
            self._blobs[name] = MockBlob(name, content, exists=True)

        def blob(self, name):
            if name in self._blobs:
                return self._blobs[name]
            return MockBlob(name)

    return MockBucket()


@pytest.fixture
def mock_cache(mock_secrets, mock_bucket, tmpdir):
    '''
    Mock a GCPCache instance, using fakeredis and a mocked GCP bucket
    '''
    from codecoverage_backend.gcp import GCPCache

    class MockCache(GCPCache):

        def __init__(self):
            self.redis = fakeredis.FakeStrictRedis()
            self.reports_dir = tmpdir.mkdtemp()
            self.bucket = mock_bucket

    return MockCache()


@pytest.fixture
def mock_hgmo():
    '''
    Mock HGMO responses for pushes
    '''
    headers = {
        'content-type': 'application/json'
    }
    max_push = 1000

    def _test_rev(request):
        # The push id is in the first 3 characters of the revision requested
        revision = request.path_url[17:]
        assert len(revision) == 32
        resp = {
            'pushid': int(revision[:3]),
        }
        return (200, headers, json.dumps(resp))

    def _changesets(push_id):

        # random changesets
        changesets = [
            uuid.uuid4().hex
            for _ in range(random.randint(2, 20))
        ]

        # Add the MD5 hash of the push id to test specific cases
        changesets.append(hashlib.md5(str(push_id).encode('utf-8')).hexdigest())

        return changesets

    def _test_pushes(request):
        '''
        Build pushes list, limited to a maximum push id
        '''
        query = urllib.parse.parse_qs(urllib.parse.urlparse(request.path_url).query)
        assert int(query['version'][0]) == 2
        start = 'startID' in query and int(query['startID'][0]) or (max_push - 8)
        end = 'endID' in query and int(query['endID'][0]) or max_push
        assert end > start
        now = time.time()
        resp = {
            'lastpushid': max_push,
            'pushes': {
                push: {
                    'changesets': _changesets(push),
                    'date': int((now % 1000000) + push * 10),  # fake timestamp
                }
                for push in range(start, end + 1)
                if push <= max_push
            }
        }
        return (200, headers, json.dumps(resp))

    with responses.RequestsMock(assert_all_requests_are_fired=False) as resps:
        resps.add_callback(
            responses.GET,
            re.compile('https://hg.mozilla.org/(.+)/json-rev/(.+)'),
            callback=_test_rev,
        )
        resps.add_callback(
            responses.GET,
            re.compile('https://hg.mozilla.org/(.+)/json-pushes'),
            callback=_test_pushes,
        )
        yield resps


@pytest.fixture
def mock_covdir_report():
    '''
    Path to the covdir mock in repository
    '''
    return os.path.join(FIXTURES_DIR, 'covdir.json')
