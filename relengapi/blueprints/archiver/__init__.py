# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from random import randint

from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import url_for
from relengapi.blueprints.archiver.tasks import create_and_upload_archive
from relengapi.blueprints.archiver.types import MozharnessArchiveTask
from relengapi.lib import api

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
    STARTED and finally, if it completes, it will be either SUCCESS (no exceptions), or FAILURE.

    See update_state() within create_and_upload_archive and
    http://celery.readthedocs.org/en/latest/reference/celery.states.html for more details.

    If state is SUCCESS, it is safe to check response['s3_urls'] for the archives submitted to s3
    """
    task = create_and_upload_archive.AsyncResult(task_id)
    task_info = task.info or {}
    response = {
        'state': task.state,
    }
    if task.state != 'FAILURE':
        response['status'] = task_info.get('status', 'no status available at this point.')
        response['src_url'] = task_info.get('src_url', '')
        response['s3_urls'] = task_info.get('s3_urls', {})
    else:
        # something went wrong
        response['status'] = str(task.info)  # this is the exception raised
        response['src_url'] = ''
        response['s3_urls'] = {}

    return MozharnessArchiveTask(**response)


@bp.route('/hgmo/<path:repo>/<rev>')
@api.apimethod(None, unicode, unicode, unicode, unicode, unicode, status_code=302)
def get_hgmo_archive(repo, rev, subdir=None, suffix='tar.gz', preferred_region=None):
    """
    An archiver for hg.mozilla.org related requests. Uses relengapi.blueprints.archiver.get_archive

    :param repo: the repo location off of hg.mozilla.org/
    :param rev: the rev associated with the repo
    :param subdir: optional subdir path to only archive a portion of the repo
    :param suffix: the archive extension type. defaulted to tar.gz
    :param preferred_region: the preferred s3 region to use
    """
    src_url = current_app.config['ARCHIVER_HGMO_URL_TEMPLATE'].format(
        repo=repo, rev=rev, suffix=suffix, subdir=subdir or ''
    )
    # though slightly odd to append the archive suffix extension with a subdir, this:
    #   1) allows us to have archives based on different subdir locations from the same repo and rev
    #   2) is aligned with the hg.mozilla.org format
    key = '{repo}-{rev}.{suffix}'.format(repo=repo, rev=rev, suffix=suffix)
    if subdir:
        key += '/{}'.format(subdir)
    return get_archive(src_url, key, preferred_region)


def get_archive(src_url, key, preferred_region):
    """
    A generic getter for retrieving an s3 location of an archive where the archive is based off a
    src_url.

    sub-dir: hg.mozilla.org supports archives of sub directories within a repository. This
    flexibility allows for creating archives of only a portion of what would normally be an entire
    repo archive.

    logic flow:
     If their is already a key within s3, a re-direct link is given for the
    s3 location. If the key does not exist, download the archive from src url, upload it to s3
    for each region supported and return all uploaded s3 url locations.

     When the key does not exist, the remaining work will be assigned to a celery background task
    with a url location returned immediately for obtaining task state updates.
    """
    buckets = current_app.config['ARCHIVER_S3_BUCKETS']
    random_region = buckets.keys()[randint(0, len(buckets.keys()) - 1)]
    # use preferred region if available otherwise choose a valid one at random
    region = preferred_region if preferred_region and preferred_region in buckets else random_region
    bucket = buckets[region]
    s3 = current_app.aws.connect_to('s3', region)

    # first, see if the key exists
    if not s3.get_bucket(bucket).get_key(key):
        task_id = key.replace('/', '_')  # keep things simple and avoid slashes in task url
        if create_and_upload_archive.AsyncResult(task_id).state != 'STARTED':
            # task is currently not in progress so start one.
            create_and_upload_archive.apply_async(args=[src_url, key], task_id=task_id)
        return {}, 202, {'Location': url_for('archiver.task_status', task_id=task_id)}

    log.info("generating GET URL to {}, expires in {}s".format(key, GET_EXPIRES_IN))
    # return 302 pointing to s3 url with archive
    signed_url = s3.generate_url(
        method='GET', expires_in=GET_EXPIRES_IN,
        bucket=bucket, key=key
    )
    return redirect(signed_url)
