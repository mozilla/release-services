# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import

import mock
import moto

from relengapi.blueprints.archiver.tasks import create_and_upload_archive
from relengapi.blueprints.archiver.test_util import fake_200_response
from relengapi.blueprints.archiver.test_util import fake_404_response
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
def test_invalid_hg_url(app):
    setup_buckets(app, cfg)
    rev, repo, suffix = 'fakeRev', 'mozilla-central', 'tar.gz'
    key = '{repo}-{rev}.{suffix}'.format(repo=repo, rev=rev, suffix=suffix)
    src_url = cfg['ARCHIVER_HGMO_URL_TEMPLATE'].format(repo=repo, rev=rev, suffix=suffix,
                                                       subdir='testing/mozharness')
    with app.app_context():
        with mock.patch("relengapi.blueprints.archiver.tasks.requests.get") as get:
            get.return_value = fake_404_response()
            task = create_and_upload_archive.apply_async(args=[src_url, key],
                                                         task_id=key.replace('/', '_'))
    assert "Could not get a valid response from src_url" in task.info.get('status', {}), \
        "invalid hg url was not caught!"


@moto.mock_s3
@test_context
def test_successful_upload_archive_response(app):
    setup_buckets(app, cfg)
    rev, repo, subdir, suffix = '203e1025a826', 'mozilla-central', 'testing/mozharness', 'tar.gz'
    key = '{repo}-{rev}.{suffix}'.format(repo=repo, rev=rev, suffix=suffix)
    if subdir:
        key += '/{}'.format(subdir)
    src_url = cfg['ARCHIVER_HGMO_URL_TEMPLATE'].format(repo=repo, rev=rev, suffix=suffix,
                                                       subdir='testing/mozharness')
    with app.app_context():
        with mock.patch("relengapi.blueprints.archiver.tasks.requests.get") as get, \
                mock.patch("relengapi.blueprints.archiver.tasks.requests.head") as head:
            get.return_value = fake_200_response()
            head.return_value = fake_200_response()
            task = create_and_upload_archive.apply_async(args=[src_url, key],
                                                         task_id=key.replace('/', '_'))
    expected_regions = [region for region in cfg['ARCHIVER_S3_BUCKETS']]
    all_regions_have_s3_urls = [
        task.info.get("s3_urls", {}).get(region) for region in expected_regions
    ]
    assert all(all_regions_have_s3_urls), "s3 urls not uploaded for each region!"
    assert task.info.get('src_url') == src_url, "src url doesn't match upload response!"
    assert task.state == "SUCCESS", "completed task's state isn't SUCCESS!"
