# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# import json
import moto

# from relengapi.blueprints.archiver.tasks import create_and_upload_archive
# from time import sleep
#
# from nose.tools import eq_
from relengapi.lib.testing.context import TestContext

cfg = {
    'RELENGAPI_CELERY_LOG_LEVEL': 'DEBUG',
    'debug': True,

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
# test_context = TestContext()


# @test_context
# def test_hello(client):
#     print 'hi there'
#     rv = client.get('/archiver/')
#     eq_(rv.status_code, 200)
#     eq_(json.loads(rv.data)['result'], {'message': 'hello world'})


@moto.mock_s3
@test_context
def test_foo(app, client):
    app.debug = True
    s3 = app.aws.connect_to('s3', 'us-east-1')
    s3.create_bucket('archiver-bucket-1')
    s32 = app.aws.connect_to('s3', 'us-west-2')
    s32.create_bucket('archiver-bucket-2')

    # from pprint import pprint

    # with app.app_context():
    #     resp = client.get('/archiver/mozharness/9ebd530c5843')
    #     sleep(3)
    #     resp2 = client.get('/archiver/status/9ebd530c5843')
    #     for a in dir(resp):
    #         pprint(a + ' : ' + str(resp.__getattribute__(a)))
    #     for a in dir(resp2):
    #         pprint(a + ' : ' + str(resp2.__getattribute__(a)))

    # rev, repo, suffix, key, = 'foo', 'mozilla-central', 'tar.gz', 'mozilla-central-foo.tar.gz'
    # config = cfg['SUBREPO_MOZHARNESS_CFG']
    # with app.app_context():
    #     task = create_and_upload_archive.apply_async(args=[config, rev, repo, suffix, key],
    #                                                  task_id='9ebd530c5843')
    #     for a in dir(task):
    #         pprint(a + ' : ' + str(task.__getattribute__(a)))
    # eq_(task.status_code, 404, task.info)
