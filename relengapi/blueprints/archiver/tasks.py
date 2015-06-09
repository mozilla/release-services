# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os
import requests
import tempfile
import urllib2

from boto.s3.key import Key

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
    temp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".{}".format(suffix), delete=False)
    data = urllib2.urlopen(url).read()
    with open(temp_file.name, "wb") as tmpf:
        tmpf.write(data)
    k.set_contents_from_filename(temp_file.name)
    os.unlink(temp_file.name)  # clean up tmp file

    return s3.generate_url(expires_in=GET_EXPIRES_IN, method='GET', bucket=bucket, key=key)


@celery.task(bind=True)
def create_and_upload_archive(self, cfg, rev, repo, suffix, key):
    """
    A celery task that downloads an archive if it exists from a src location and attempts to upload
    the archive to a supported bucket in each supported region.

    Throughout this process, update the state of the task and finally return the location of the
    s3 urls if successful.
    """
    return_status = "Task completed! Check 's3_urls' for upload locations."
    s3_urls = {}
    src_url = cfg['URL_SRC_TEMPLATE'].format(repo=repo, rev=rev, suffix=suffix)

    self.update_state(state='PROGRESS',
                      meta={'status': 'ensuring archive origin location exists.', 'src_url': src_url})
    resp = requests.get(src_url)
    if resp.status_code == 200:
        self.update_state(state='PROGRESS',
                          meta={'status': 'uploading archive to s3 buckets', 'src_url': src_url})
        for bucket in cfg['S3_BUCKETS']:
            s3_urls[bucket['REGION']] = upload_url_archive_to_s3(key, src_url, bucket['REGION'],
                                                                 bucket['NAME'], suffix)
        if not any(s3_urls.values()):
            return_status = "Could not upload any archives to s3. Check logs for errors."
            log.warning(return_status)
    else:
        return_status = "Can't find archive given branch, rev, and suffix. Does url {} exist? " \
                        "Request Response code: {}".format(src_url, resp.status_code)
        log.warning(return_status)

    return {
        'status': return_status,
        'src_url': src_url,
        's3_urls': s3_urls,
    }
