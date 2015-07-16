# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import requests
import shutil
import tempfile

from boto.s3.key import Key
from celery.task import current
from flask import current_app
from random import randint

from relengapi.lib import celery

log = logging.getLogger(__name__)

SIGNED_URL_EXPIRY = 300
TASK_EXPIRY = 1800
TASK_TIME_OUT = 3600


def upload_url_archive_to_s3(key, url, buckets):
    s3_urls = {}

    # make the source request
    resp = requests.get(url, stream=True)

    # create a temporary file for it
    tempf = tempfile.TemporaryFile()
    # copy the data, block-by-block, into that file
    resp.raw.decode_content = True
    shutil.copyfileobj(resp.raw, tempf)

    # write it out to S3
    for region in buckets:
        s3 = current_app.aws.connect_to('s3', region)
        k = Key(s3.get_bucket(buckets[region]))
        k.key = key
        k.set_metadata('Content-Type', resp.headers['Content-Type'])
        # give it the same attachment filename
        k.set_metadata('Content-Disposition', resp.headers['Content-Disposition'])
        k.set_contents_from_file(tempf, rewind=True)   # rewind points tempf back to start for us
        s3_urls[region] = s3.generate_url(expires_in=SIGNED_URL_EXPIRY, method='GET',
                                          bucket=buckets[region], key=key)

    resp.close()

    return s3_urls


@celery.task(bind=True, track_started=True, max_retries=3,
             time_limit=TASK_TIME_OUT, expires=TASK_EXPIRY)
def create_and_upload_archive(self, src_url, key):
    """
    A celery task that downloads an archive if it exists from a src location and attempts to upload
    the archive to a supported bucket in each supported region.

    Throughout this process, update the state of the task and finally return the location of the
    s3 urls if successful.

    expires after 30m if the task hasn't been picked up from the message queue

    task is killed if exceeds time_limit of an hour after it has started
    """
    status = "Task completed! Check 's3_urls' for upload locations."
    s3_urls = {}
    buckets = current_app.config['ARCHIVER_S3_BUCKETS']

    resp = requests.head(src_url)
    if resp.status_code == 200:
        try:
            s3_urls = upload_url_archive_to_s3(key, src_url, buckets)
        except Exception as exc:
            # set a jitter enabled delay
            # where an aggressive delay would result in: 7s, 49s, and 343s
            # and a gentle delay would result in: 4s, 16s, and 64s
            delay = randint(4, 7) ** (current.request.retries + 1)  # retries == 0 on first attempt
            current.retry(exc=exc, countdown=delay)
    else:
        status = "Url not found. Does it exist? url: '{}', response: '{}' ".format(src_url,
                                                                                   resp.status_code)
        log.warning(status)
    return {
        'status': status,
        'src_url': src_url,
        's3_urls': s3_urls,
    }
