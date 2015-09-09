from __future__ import absolute_import

from StringIO import StringIO

import mock
import requests
from boto.s3.key import Key

EXPECTED_TASK_STATUS_FAILED_RESPONSE = {
    "s3_urls": {},
    "src_url": "",
    "state": "FAILURE",
    "status": "{u'exc_message': u'fp is at EOF. Use rewind option or seek() to data start.'"
              ", u'exc_type': u'AttributeError'}"
}

EXPECTED_TASK_STATUS_INCOMPLETE_RESPONSE = {
    "s3_urls": {},
    "src_url": "",
    "state": "STARTED",
    "status": "no task status at this point",
}

EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE = {
    "s3_urls": {
        "us-east-1": "https://archiver-us-east-1.s3.amazonaws.com/mozilla-central-9213957d1.tar.gz",
        "us-west-2": "https://archiver-us-west-2.s3.amazonaws.com/mozilla-central-9213957d1.tar.gz",
    },
    "src_url": "https://hg.mozilla.org/mozilla-central/archive/9213957d1.tar.gz/testing/mozharness",
    "state": "SUCCESS",
    "status": "Task completed! Check 's3_urls' for upload locations."
}


EXPECTED_TASK_STATUS_PENDING_RESPONSE = {
    "s3_urls": {
        "us-east-1": "https://archiver-us-east-1.s3.amazonaws.com/mozilla-central-9213957d1.tar.gz",
        "us-west-2": "https://archiver-us-west-2.s3.amazonaws.com/mozilla-central-9213957d1.tar.gz",
    },
    "src_url": "https://hg.mozilla.org/mozilla-central/archive/9213957d1.tar.gz/testing/mozharness",
    "state": "PENDING",
    "status": "no task status at this point",
}


def setup_buckets(app, cfg):
    for region, bucket in cfg['ARCHIVER_S3_BUCKETS'].iteritems():
        s3 = app.aws.connect_to('s3', region)
        s3.create_bucket(bucket)


def create_s3_items(app, cfg, key):
    for region, bucket in cfg['ARCHIVER_S3_BUCKETS'].iteritems():
        s3 = app.aws.connect_to('s3', region)
        b = s3.get_bucket(bucket)
        k = Key(b)
        k.key = key
        k.set_contents_from_string("Help, I'm trapped in an alternate s3 dimension.")


def fake_200_response():
    response = mock.Mock()
    response.status_code = 200
    response.headers = {
        'Content-Type': 'application/x-gzip',
        'Content-Disposition': 'attachment; filename=mozilla-central-9213957d166d.tar.gz'
    }
    response.raw = StringIO("Debugging is twice as hard as writing the code in the first place. "
                            "Therefore, if you write the code as cleverly as possible, you are, "
                            "by definition, not smart enough to debug it. --Brian W. Kernighan")
    return response


def fake_404_response():
    response = mock.Mock()
    response.status_code = 404
    response.raise_for_status.side_effect = requests.exceptions.HTTPError('does not exist yo!')
    return response


def fake_failed_task_status():
    task = mock.Mock()
    task.state = EXPECTED_TASK_STATUS_FAILED_RESPONSE['state']
    task.info = EXPECTED_TASK_STATUS_FAILED_RESPONSE['status']
    return task


def fake_successful_task_status():
    task = mock.Mock()
    task.state = EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE['state']
    task.info = {
        'src_url': EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE['src_url'],
        's3_urls': EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE['s3_urls'],
        'status': EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE['status'],
    }
    return task


def fake_expired_task_status():
    task = mock.Mock()
    task.state = EXPECTED_TASK_STATUS_PENDING_RESPONSE['state']
    task.info = {
        'src_url': EXPECTED_TASK_STATUS_PENDING_RESPONSE['src_url'],
        's3_urls': EXPECTED_TASK_STATUS_PENDING_RESPONSE['s3_urls'],
        'status': EXPECTED_TASK_STATUS_PENDING_RESPONSE['status'],
    }
    return task


def fake_incomplete_task_status():
    task = mock.Mock()
    task.state = EXPECTED_TASK_STATUS_INCOMPLETE_RESPONSE['state']
    task.status = {
        'status': EXPECTED_TASK_STATUS_INCOMPLETE_RESPONSE['status'],
    }
    return task
