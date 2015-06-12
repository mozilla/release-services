# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os
import requests
import tempfile

from boto.s3.key import Key
from random import randint

from celery.task import current
from flask import current_app
from relengapi.lib import celery

log = logging.getLogger(__name__)

GET_EXPIRES_IN = 300


def upload_url_archive_to_s3(key, url, region, bucket, suffix):
    """
    Given a src url, upload contents to an s3 bucket by a given key.
    """
    s3 = current_app.aws.connect_to('s3', region)
    k = Key(s3.get_bucket(bucket))
    k.key = key

    # rather than worrying about pointers and seeking, let's avail of a named temp file that is
    # allowed to persist after the file is closed. Finally, when are finished, we can clean up
    # the temp file
    resp = requests.get(url)
    temp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".{}".format(suffix), delete=False)
    with open(temp_file.name, "wb") as tmpf:
        tmpf.write(resp.content)
    k.set_contents_from_filename(temp_file.name)
    os.unlink(temp_file.name)  # clean up tmp file

    return s3.generate_url(expires_in=GET_EXPIRES_IN, method='GET', bucket=bucket, key=key)


@celery.task(bind=True, track_started=True, max_retries=3)
def create_and_upload_archive(self, cfg, rev, repo, suffix, key):
    """
    A celery task that downloads an archive if it exists from a src location and attempts to upload
    the archive to a supported bucket in each supported region.

    Throughout this process, update the state of the task and finally return the location of the
    s3 urls if successful.
    """
    status = "Task completed! Check 's3_urls' for upload locations."
    s3_urls = {}
    src_url = cfg['URL_SRC_TEMPLATE'].format(repo=repo, rev=rev, suffix=suffix)

    resp = requests.head(src_url)
    if resp.status_code == 200:
        try:
            for bucket in cfg['S3_BUCKETS']:
                s3_urls[bucket['REGION']] = upload_url_archive_to_s3(key, src_url, bucket['REGION'],
                                                                     bucket['NAME'], suffix)
        except Exception as exc:
            # set a jitter enabled delay
            # where an aggressive delay would result in: 7s, 49s, and 343s
            # and a gentle delay would result in: 4s, 16s, and 64s
            delay = randint(4, 7) ** (current.request.retries + 1)  # retries == 0 on first attempt
            current.retry(exc=exc, countdown=delay)
        if not any(s3_urls.values()):
            status = "Could not upload any archives to s3. Check logs for errors."
        log.warning(status)
    else:
        status = "Url not found. Does it exist? url: '{}', response: '{}' ".format(src_url,
                                                                                   resp.status_code)
        log.warning(status)
    return {
        'status': status,
        'src_url': src_url,
        's3_urls': s3_urls,
    }
