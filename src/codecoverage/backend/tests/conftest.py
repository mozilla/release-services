# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import glob
import hashlib
import json
import os
import random
import re
import unittest
import urllib.parse
import uuid

import fakeredis
import pytest
import responses
import zstandard as zstd

import backend_common.testing

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture(autouse=True, scope='function')
def mock_secrets():
    '''
    Provide configuration through mock Taskcluster secrets
    '''
    import cli_common.taskcluster
    cli_common.taskcluster.get_secrets = unittest.mock.Mock(return_value={
        'REDIS_URL': 'redis://unitest:1234',
        'ACTIVE_DATA': {
            'url': 'http://mock-active-data:8000',
            'user': 'test@allizom.org',
            'password': 'dummySecret',
        },
        'PHABRICATOR_TOKEN': 'api-correct',
        'APP_CHANNEL': 'test',
        'GOOGLE_CLOUD_STORAGE': {
            'token_uri': 'secret',
            'client_email': 'xxx@mozilla.test',
            'private_key': 'somethingHere',
            'bucket': 'unittest',
        }
    })


@pytest.fixture(scope='function')
def mock_secrets_bad_phabricator_token(mock_secrets):
    import codecoverage_backend.secrets as s
    old = s.PHABRICATOR_TOKEN
    s.PHABRICATOR_TOKEN = 'api-bad-token'
    yield
    s.PHABRICATOR_TOKEN = old


@pytest.fixture()
def app(mock_secrets):
    '''
    Load codecoverage_backend app in test mode
    '''
    import codecoverage_backend

    config = backend_common.testing.get_app_config({
    })
    app = codecoverage_backend.create_app(config)

    with app.app_context():
        backend_common.testing.configure_app(app)
        yield app


@pytest.fixture
async def coverage_responses(aresponses):
    with open(os.path.join(FIXTURES_DIR, 'codecov_main.json')) as f:
        aresponses.add('codecov.io',
                       '/api/gh/marco-c/gecko-dev',
                       'get',
                       aresponses.Response(text=f.read(), content_type='application/json'))

    directories = [
        {
            'path': 'hgmo_json_revs',
            'host': 'hg.mozilla.org',
            'url': lambda fname: f'/mozilla-central/json-rev/{fname}',
        },
        {
            'path': 'hgmo_json_pushes',
            'host': 'hg.mozilla.org',
            'url': lambda fname: f'/mozilla-central/json-pushes?version=2&full=1&startID={int(fname)}&endID={int(fname) + 8}',
            'match_querystring': True,
        },
        {
            'path': 'hg_git_map',
            'host': 'mapper.mozilla-releng.net',
            'url': lambda fname: f'/gecko-dev/rev/hg/{fname}',
        },
        {
            'path': 'git_hg_map',
            'host': 'mapper.mozilla-releng.net',
            'url': lambda fname: f'/gecko-dev/rev/git/{fname}',
        },
        {
            'path': 'codecov_commits',
            'host': 'codecov.io',
            'url': lambda fname: f'/api/gh/marco-c/gecko-dev/commit/{fname}',
            'status': lambda data: json.loads(data)['meta']['status'],
        },
        {
            'path': 'codecov_src',
            'host': 'codecov.io',
            'url': lambda fname: '/api/gh/marco-c/gecko-dev/src/{}'.format(fname.replace('_', '/')),
            'status': lambda data: json.loads(data)['meta']['status'],
        },
        {
            'path': 'hgmo_json_annotate',
            'host': 'hg.mozilla.org',
            'url': lambda fname: '/mozilla-central/json-annotate/{}'.format(fname.replace('_', '/')),
        },
    ]

    for directory in directories:
        dir_path = os.path.join(FIXTURES_DIR, directory['path'])
        for fname in os.listdir(dir_path):
            with open(os.path.join(dir_path, fname)) as f:
                data = f.read()
                match_querystring = directory['match_querystring'] if 'match_querystring' in directory else False
                content_type = 'application/json' if fname.endswith('.json') else 'text/plain'
                status = directory['status'](data) if 'status' in directory else 200

                aresponses.add(directory['host'],
                               directory['url'](os.path.splitext(fname)[0]),
                               'get',
                               aresponses.Response(text=data, content_type=content_type, status=status),
                               match_querystring=match_querystring)


@pytest.fixture
def hgmo_phab_rev_responses():
    rev = '2ed1506d1dc7db3d70a3feed95f1456bce05bbee'
    with open(os.path.join(FIXTURES_DIR, 'hgmo_json_revs', f'{rev}.json')) as f:
        responses.add(responses.GET,
                      f'https://hg.mozilla.org/mozilla-central/json-rev/{rev}',
                      status=200,
                      body=f.read(),
                      content_type='application/json')

    with open(os.path.join(FIXTURES_DIR, 'hgmo-json-rev-miss.json')) as f:
        responses.add(responses.GET,
                      re.compile(r'https://hg.mozilla.org/mozilla-central/json-rev/.*'),
                      status=404,
                      body=f.read(),
                      content_type='application/json')


@pytest.fixture
def phabricator_responses():
    resp = {}
    for ftype in ['hit', 'miss', 'wrong-api-key']:
        with open(os.path.join(FIXTURES_DIR, f'phabricator-{ftype}.json')) as f:
            resp[ftype] = f.read()

    def callback(request):
        headers = {'Content-Type': 'application/json'}
        query = urllib.parse.parse_qs(request.body)
        params = json.loads(query['params'][0])
        if params['__conduit__']['token'] != 'api-correct':
            return 200, headers, resp['wrong-api-key']
        elif params['constraints']['revisionPHIDs'][0] == 'PHID-DREV-esv6jbcptwuju667eiyx':
            return 200, headers, resp['hit']
        else:
            return 200, headers, resp['miss']

    responses.add_callback(
        responses.POST,
        'https://phabricator.services.mozilla.com/api/differential.diff.search',
        callback=callback,
        content_type='application/json',
    )

    responses.add(
        responses.POST,
        'https://phabricator.services.mozilla.com/api/user.whoami',
        body=json.dumps({
            'result': {
                'phid': 'PHID-USER-test1234',
                'userName': 'Tester',
                'primaryEmail': 'test@mozilla.com',
                'realName': 'Mr. Tester',
            },
            'error_code': None,
            'error_info': None
        }),
        content_type='application/json',
    )


@pytest.fixture(scope='session')
def coverage_changeset_by_file():
    with open(os.path.join(FIXTURES_DIR, 'coverage_changeset_by_file.json')) as f:
        changeset_by_file_info = json.load(f)

    for entry in changeset_by_file_info:
        entry['data'] = {int(key): value for key, value in entry['data'].items()}

    return changeset_by_file_info


def get_coverage_builds_fixtures():
    paths = glob.glob(os.path.join(FIXTURES_DIR, 'coverage_build_*.json'))
    builds = {'info': {}, 'summary': {}}
    for path in sorted(paths):
        with open(path) as f:
            build_data = json.load(f)
        builds['info'].update(build_data['info'])
        builds['summary'].update(build_data['summary'])

    return builds


@pytest.fixture(scope='session')
def coverage_builds():
    return get_coverage_builds_fixtures()


def mock_coverage_by_changeset_job_success(job_changeset):
    builds = get_coverage_builds_fixtures()

    for changeset, expected in builds['info'].items():
        if changeset == job_changeset or changeset[:12] == job_changeset[:12]:
            return expected
    raise NotImplementedError('Not implemented return values for changeset %s' % job_changeset)


@pytest.fixture
def mock_active_data(mock_secrets, aresponses):
    '''
    Mock elastic search HTTP responses
     * available revisions
     * count
    '''
    async def _search(request):
        assert request.has_body
        body = json.loads(await request.read())

        if 'aggs' in body:
            # Available revisions
            filename = 'revisions.json'

        else:
            filename = 'tests_full.json'

        payload = open(os.path.join(FIXTURES_DIR, 'active_data', filename)).read()
        return aresponses.Response(text=payload, content_type='application/json')

    # Tests count per filename/changeset
    async def _count(request):
        # By default gives empty count
        filename = 'count_empty.json'

        # Detect specific queries
        if request.has_body:
            body = json.loads(await request.read())
            terms = {
                k: v
                for t in body['query']['bool']['must']
                for k, v in t['term'].items()
            }

            if terms['source.file.name.~s~'] == 'js/src/jsutil.cpp' and terms['repo.changeset.id.~s~'] == '2d83e1843241d869a2fc5cf06f96d3af44c70e70':  # noqa
                filename = 'count_full.json'

        payload = open(os.path.join(FIXTURES_DIR, 'active_data', filename)).read()
        return aresponses.Response(text=payload, content_type='application/json')

    # Activate callbacks for coverage endpoints on mock server
    aresponses.add('mock-active-data:8000', '/coverage/_count', 'get', _count)
    aresponses.add('mock-active-data:8000', '/coverage/_search', 'get', _search)


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

        def add_mock_blob(self, name, content):
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
    from codecoverage_backend.services.gcp import GCPCache

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
        resp = {}
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
        resp = {
            'lastpushid': max_push,
            'pushes': {
                push: {
                    'changesets': _changesets(push)
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
