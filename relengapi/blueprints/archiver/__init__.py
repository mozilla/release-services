# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os

from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import url_for
from relengapi.blueprints.archiver.tasks import create_and_upload_archive
from relengapi.blueprints.archiver.types import MozharnessArchiveTask
from relengapi.lib import api
from werkzeug.exceptions import NotFound

bp = Blueprint('archiver', __name__)
log = logging.getLogger(__name__)

GET_EXPIRES_IN = 300

@bp.route('/status/<task_id>')
@api.apimethod(MozharnessArchiveTask, unicode)
def task_status(task_id):
    """
    Check and return the current state of the create_and_upload_archive celery task with task id
    of <task_id>.

    If the task is unknown, state will be PENDING. Once the task starts it will be updated to
    PROGRESS and finally, if it completes, it will be either SUCCESS (no exceptions), or FAILURE.

    See update_state() within create_and_upload_archive and
    http://celery.readthedocs.org/en/latest/reference/celery.states.html for more details.

    If state is SUCCESS, it is safe to check response['s3_urls'] for the archives submitted to s3
    """
    task = create_and_upload_archive.AsyncResult(task_id)
    task_info = task.info or {}
    response = {
        'state': task.state,
        'src_url': task_info.get('src_url', ''),
        's3_urls': task_info.get('s3_urls', {})
    }
    if task.state != 'FAILURE':
        response['status'] = task_info.get('status', 'no status available at this point.')
    else:
        # something went wrong
        response['status'] = str(task.info)  # this is the exception raised

    return MozharnessArchiveTask(**response)


@bp.route('/mozharness/<rev>')
@api.apimethod(None, unicode, unicode, unicode, unicode, status_code=302)
def get_mozharness_archive(rev, repo="mozilla-central", region='us-west-2', suffix='tar.gz'):
    cfg = current_app.config['SUBREPO_MOZHARNESS_CFG']
    return get_archive_from_repo(cfg, rev, repo, region, suffix)


def get_archive_from_repo(cfg, rev, repo, region, suffix):
    """
    A generic getter for retrieving an s3 location of an archive where the archive is based off a
    given repo name, revision, and possibly sub-dir.

    sub-dir: hg.mozilla.org supports archives of sub directories within a repository. This
    flexibility allows for creating archives of only a portion of what would normally be an entire
    repo archive.

    logic flow:
     If their is already a key based on given args, a re-direct link is given for the
    s3 location. If the key does not exist, download the archive from src url, upload it to and
    return all s3 url locations.

     When the key does not exist, the remaining work will be assigned to a celery background task
    with a url location returned immediately for obtaining task state updates.
    """
    bucket_region = None
    bucket_name = None
    for bucket in cfg['S3_BUCKETS']:
        if region in bucket['REGION']:
            bucket_region = bucket['REGION']
            bucket_name = bucket['NAME']

    # sanity check
    if not bucket_name or not bucket_region:
        valid_regions = str([bucket['REGION'] for bucket in cfg['S3_BUCKETS']])
        log.warning('Unsupported region given: "{}" Valid Regions "{}"'.format(region, valid_regions))
        raise NotFound

    s3 = current_app.aws.connect_to('s3', bucket_region)
    bucket = s3.get_bucket(bucket_name)
    key = '{repo}-{rev}.{suffix}'.format(repo=os.path.basename(repo), rev=rev, suffix=suffix)

    # first, see if the key exists
    if not bucket.get_key(key):
        task_id = rev
        if create_and_upload_archive.AsyncResult(task_id).state != 'PROGRESS':
            # task is currently not in progress so start one.
            create_and_upload_archive.apply_async(args=[cfg, rev, repo, suffix, key], task_id=task_id)
        return {}, 202, {'Location': url_for('archiver.task_status', task_id=task_id)}

    log.info("generating GET URL to {}, expires in {}s".format(rev, GET_EXPIRES_IN))
    # return 302 pointing to s3 url with archive
    signed_url = s3.generate_url(
        method='GET', expires_in=GET_EXPIRES_IN,
        bucket=bucket_name, key=key
    )
    return redirect(signed_url)

