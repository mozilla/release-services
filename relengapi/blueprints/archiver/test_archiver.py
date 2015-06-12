# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import moto
from boto.s3.key import Key
from nose.tools import eq_

from relengapi.lib.testing.context import TestContext


cfg = {
    'RELENGAPI_CELERY_LOG_LEVEL': 'DEBUG',

    'AWS': {
        'access_key_id': 'aa',
        'secret_access_key': 'ss',
    },

    'SUBREPO_MOZHARNESS_CFG': {
        'S3_BUCKETS': [
            {'REGION': 'us-east-1', 'NAME': 'archiver-bucket-1'},
            {'REGION': 'us-west-2', 'NAME': 'archiver-bucket-2'}
        ],
        "URL_SRC_TEMPLATE": "http://hg.mozilla.org/{repo}/archive/{rev}.{suffix}/testing/mozharness"
    },
    'CELERY_BROKER_URL': 'memory://',
    'CELERY_BACKEND': 'cache',
    "CELERY_CACHE_BACKEND": 'memory',
    'CELERY_ALWAYS_EAGER': True,
}

test_context = TestContext(config=cfg)


def setup_buckets(app, cfg):
    for bucket in cfg['S3_BUCKETS']:
        s3 = app.aws.connect_to('s3', bucket["REGION"])
        s3.create_bucket(bucket["NAME"])


def create_s3_items(app, cfg, key):
    for bucket in cfg['S3_BUCKETS']:
        s3 = app.aws.connect_to('s3', bucket["REGION"])
        b = s3.get_bucket(bucket["NAME"])
        k = Key(b)
        k.key = key
        k.set_contents_from_string("Help, I'm trapped in an alternate s3 dimension.")


@moto.mock_s3
@test_context
def test_accepted_response_when_missing_s3_key(app, client):
    setup_buckets(app, cfg['SUBREPO_MOZHARNESS_CFG'])
    resp = client.get('/archiver/mozharness/9ebd530c5843?repo=mozilla-central&region=us-east-1')
    eq_(resp.status_code, 202, resp.status)


@moto.mock_s3
@test_context
def test_redirect_response_when_found_s3_key(app, client):
    setup_buckets(app, cfg['SUBREPO_MOZHARNESS_CFG'])
    create_s3_items(app, cfg['SUBREPO_MOZHARNESS_CFG'], key='mozilla-central-9ebd530c5843.tar.gz')

    resp = client.get('/archiver/mozharness/9ebd530c5843?repo=mozilla-central&region=us-east-1')
    eq_(resp.status_code, 302, resp.status)


@moto.mock_s3
@test_context
def test_unsupported_region(app, client):
    setup_buckets(app, cfg['SUBREPO_MOZHARNESS_CFG'])

    resp = client.get('/archiver/mozharness/9ebd530c5843?repo=mozilla-central&region=us-SXSW-5')
    eq_(resp.status_code, 404, resp.status)
