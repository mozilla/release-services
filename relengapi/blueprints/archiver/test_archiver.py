# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import mock
import moto

from nose.tools import eq_
from relengapi.blueprints.archiver.test_util import EXPECTED_TASK_STATUS_FAILED_RESPONSE
from relengapi.blueprints.archiver.test_util import EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE
from relengapi.blueprints.archiver.test_util import create_s3_items
from relengapi.blueprints.archiver.test_util import fake_200_response
from relengapi.blueprints.archiver.test_util import fake_failed_task_status
from relengapi.blueprints.archiver.test_util import fake_successful_task_status
from relengapi.blueprints.archiver.test_util import setup_buckets

from relengapi.lib.testing.context import TestContext


cfg = {
    'RELENGAPI_CELERY_LOG_LEVEL': 'DEBUG',

    'AWS': {
        'access_key_id': 'aa',
        'secret_access_key': 'ss',
    },

    'ARCHIVER_S3_BUCKETS': {
        'us-east-1': 'archiver-bucket-1',
        'us-west-2': 'archiver-bucket-2'
    },
    'ARCHIVER_HGMO_URL_TEMPLATE': "https://hg.mozilla.org/{repo}/archive/{rev}.{suffix}/{subdir}",

    'CELERY_BROKER_URL': 'memory://',
    'CELERY_BACKEND': 'cache',
    "CELERY_CACHE_BACKEND": 'memory',
    'CELERY_ALWAYS_EAGER': True,
}

test_context = TestContext(config=cfg)


@moto.mock_s3
@test_context
def test_accepted_response_when_missing_s3_key(app, client):
    setup_buckets(app, cfg)
    with mock.patch("relengapi.blueprints.archiver.tasks.requests.get") as get, \
            mock.patch("relengapi.blueprints.archiver.tasks.requests.head") as head:
        # don't actually hit hg.m.o, we just care about starting a subprocess and
        # returning a 202 accepted
        get.return_value = fake_200_response()
        head.return_value = fake_200_response()
        resp = client.get('/archiver/hgmo/mozilla-central/9213957d166d?'
                          'subdir=testing/mozharness&preferred_region=us-west-2')
    eq_(resp.status_code, 202, resp.status)


@moto.mock_s3
@test_context
def test_redirect_response_when_found_s3_key(app, client):
    setup_buckets(app, cfg)
    rev, repo, subdir, suffix = '203e1025a826', 'mozilla-central', 'testing/mozharness', 'tar.gz'
    key = '{repo}-{rev}.{suffix}'.format(repo=repo, rev=rev, suffix=suffix)
    if subdir:
        key += '/{}'.format(subdir)
    create_s3_items(app, cfg, key=key)

    resp = client.get(
        '/archiver/hgmo/{repo}/{rev}?subdir={subdir}&suffix={suffix}'.format(
            rev=rev, repo=repo, subdir=subdir, suffix=suffix
        )
    )
    eq_(resp.status_code, 302, resp.status)


@moto.mock_s3
@test_context
def test_task_status_when_failed(app, client):
    expected_response = EXPECTED_TASK_STATUS_FAILED_RESPONSE
    with mock.patch("relengapi.blueprints.archiver.create_and_upload_archive") as caua:
        caua.AsyncResult.side_effect = fake_failed_task_status
        response = client.get('/archiver/status/{task_id}'.format(task_id=123))
    eq_(cmp(json.loads(response.data)['result'], expected_response), 0,
        "a failed task status check does not equal expected status.")


@moto.mock_s3
@test_context
def test_task_status_when_success(app, client):
    expected_response = EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE
    with mock.patch("relengapi.blueprints.archiver.create_and_upload_archive") as caua:
        caua.AsyncResult.return_value = fake_successful_task_status(expected_response)
        response = client.get('/archiver/status/{task_id}'.format(task_id=123))
    eq_(cmp(json.loads(response.data)['result'], expected_response), 0,
        "A successful task status check does not equal expected status.")
