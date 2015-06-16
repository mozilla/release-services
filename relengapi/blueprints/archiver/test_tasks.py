# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import moto
import requests
import tempfile

from relengapi.blueprints.archiver.tasks import create_and_upload_archive
from relengapi.blueprints.archiver.tasks import upload_url_archive_to_s3
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


@moto.mock_s3
@test_context
def test_invalid_hg_url(app, client):
    setup_buckets(app, cfg['SUBREPO_MOZHARNESS_CFG'])
    rev, repo, suffix, key, = 'foo', 'mozilla-central', 'tar.gz', 'mozilla-central-foo.tar.gz'
    config = cfg['SUBREPO_MOZHARNESS_CFG']
    with app.app_context():
        task = create_and_upload_archive.apply_async(args=[config, rev, repo, suffix, key],
                                                     task_id='9ebd530c5843')
    assert "Url not found." in task.info.get('status', {}), "invalid hg url was not caught!"


@moto.mock_s3
@test_context
def test_s3_urls_exist_for_each_region(app, client):
    setup_buckets(app, cfg['SUBREPO_MOZHARNESS_CFG'])
    rev, repo, suffix, key, = ('203e1025a826', 'mozilla-central', 'tar.gz',
                               'mozilla-central-foo.tar.gz')
    config = cfg['SUBREPO_MOZHARNESS_CFG']
    with app.app_context():
        task = create_and_upload_archive.apply_async(args=[config, rev, repo, suffix, key],
                                                     task_id='9ebd530c5843')
    expected_regions = [b["REGION"] for b in cfg["SUBREPO_MOZHARNESS_CFG"]["S3_BUCKETS"]]
    all_regions_have_s3_urls = [
        task.info.get("s3_urls", {}).get(region) for region in expected_regions
    ]
    assert all(all_regions_have_s3_urls), "s3 urls not uploaded for each region!"


@moto.mock_s3
@test_context
def test_hg_and_s3_archives_match(app, client):
    setup_buckets(app, cfg['SUBREPO_MOZHARNESS_CFG'])
    bucket = cfg['SUBREPO_MOZHARNESS_CFG']["S3_BUCKETS"][0]

    src_url = "http://hg.mozilla.org/mozilla-central/archive/203e1025a826.tar.gz/testing/mozharness"
    with app.app_context():
        s3_url = upload_url_archive_to_s3(key="203e1025a826", url=src_url, region=bucket["REGION"],
                                          bucket=bucket["NAME"], suffix='tar.gz')

    src_resp = requests.get(src_url)
    s3_resp = requests.get(s3_url)
    src_file = tempfile.NamedTemporaryFile(mode="wb")
    s3_file = tempfile.NamedTemporaryFile(mode="wb")
    with open(src_file.name, "wb") as srcf:
        srcf.write(src_resp.content)
        with open(s3_file.name, "wb") as s3f:
            s3f.write(s3_resp.content)
            assert cmp(srcf, s3f), "s3 archive based on hg archive does not match!"
