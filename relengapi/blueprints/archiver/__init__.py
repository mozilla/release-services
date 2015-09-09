# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
from random import randint

import sqlalchemy as sa
import structlog
from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import url_for

from relengapi.blueprints.archiver import tables
from relengapi.blueprints.archiver.tasks import TASK_TIME_OUT
from relengapi.blueprints.archiver.tasks import create_and_upload_archive
from relengapi.blueprints.archiver.types import MozharnessArchiveTask
from relengapi.lib import api
from relengapi.lib import badpenny
from relengapi.lib.time import now

bp = Blueprint('archiver', __name__)
logger = structlog.get_logger()

GET_EXPIRES_IN = 300
PENDING_EXPIRES_IN = 60
FINISHED_STATES = ['SUCCESS', 'FAILURE', 'REVOKED']


def delete_tracker(tracker):
    session = current_app.db.session('relengapi')
    logger.info("deleting tracker with id: {}".format(tracker.task_id),
                archiver_task=tracker.task_id)
    session.delete(tracker)
    session.commit()


def update_tracker_state(tracker, state):
    session = current_app.db.session('relengapi')
    logger.info("updating tracker with id: {} to state: {}".format(tracker.id, state),
                archiver_task=tracker.task_id, archiver_task_state=state)
    try:
        tracker.state = state
        session.commit()
    except sa.exc.IntegrityError:
        session.rollback()


@badpenny.periodic_task(seconds=TASK_TIME_OUT)
def cleanup_old_tasks(job_status):
    """delete any tracker task if it is older than the time a task can live for."""
    session = current_app.db.session('relengapi')
    expiry_cutoff = now() - datetime.timedelta(seconds=TASK_TIME_OUT)
    table = tables.ArchiverTask
    for tracker in session.query(table).order_by(table.created_at):
        if tracker.created_at < expiry_cutoff:
            delete_tracker(tracker)
        else:
            break


def renew_tracker_pending_expiry(tracker):
    pending_expires_at = now() + datetime.timedelta(seconds=PENDING_EXPIRES_IN)
    session = current_app.db.session('relengapi')
    logger.info("renewing tracker {} with pending expiry: {}".format(
                tracker.id, pending_expires_at), archiver_task=tracker.task_id)
    tracker.pending_expires_at = pending_expires_at
    session.commit()


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
    task_tracker = tables.ArchiverTask.query.filter(tables.ArchiverTask.task_id == task_id).first()
    log = logger.bind(archiver_task=task_id, archiver_task_state=task.state)
    log.info("checking status of task id {}: current state {}".format(task_id, task.state))
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

    # archiver does not create any custom states, so we can assume to have only the defaults:
    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#task-states
    # therefore, delete our state_id tracker from the db if the celery state is in a final state:
    # e.g. not RETRY, STARTED, or PENDING
    if task_tracker:
        if task.state in FINISHED_STATES:
            delete_tracker(task_tracker)
        elif task.state == "PENDING" and task_tracker.pending_expires_at < now():
            log.info("Task {} has expired from pending too long. Re-creating task".format(task.id))
            renew_tracker_pending_expiry(task_tracker)  # let exceptions bubble up before moving on
            create_and_upload_archive.apply_async(args=[task_tracker.src_url, task_tracker.s3_key],
                                                  task_id=task.id)
            response['state'] = 'RETRY'
            response['status'] = 'Task has expired from pending for too long. Re-creating task.'
        elif task_tracker.state != task.state:
            update_tracker_state(task_tracker, task.state)

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
    # allow for the short hash and full hash to be passed
    rev = rev[0:12]
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
    session = current_app.db.session('relengapi')

    # first, see if the key exists
    if not s3.get_bucket(bucket).get_key(key):
        task_id = key.replace('/', '_')  # keep things simple and avoid slashes in task url
        # can't use unique support:
        # api.pub.build.mozilla.org/docs/development/databases/#unique-row-support-get-or-create
        # because we want to know when the row doesn't exist before creating it
        tracker = tables.ArchiverTask.query.filter(tables.ArchiverTask.task_id == task_id).first()
        if tracker and tracker.state in FINISHED_STATES:
            log = logger.bind(archiver_task=task_id, archiver_task_state=tracker.state)
            log.info('Task tracker: {} exists but finished with state: '
                     '{}'.format(task_id, tracker.state))
            # remove tracker and try celery task again
            delete_tracker(tracker)
            tracker = None
        if not tracker:
            log = logger.bind(archiver_task=task_id)
            log.info("Creating new celery task and task tracker for: {}".format(task_id))
            task = create_and_upload_archive.apply_async(args=[src_url, key], task_id=task_id)
            if task and task.id:
                pending_expires_at = now() + datetime.timedelta(seconds=PENDING_EXPIRES_IN)
                session.add(tables.ArchiverTask(task_id=task.id, s3_key=key, created_at=now(),
                                                pending_expires_at=pending_expires_at,
                                                src_url=src_url, state="PENDING"))
                session.commit()
            else:
                return {}, 500
        return {}, 202, {'Location': url_for('archiver.task_status', task_id=task_id)}

    logger.info("generating GET URL to {}, expires in {}s".format(key, GET_EXPIRES_IN))
    # return 302 pointing to s3 url with archive
    signed_url = s3.generate_url(
        method='GET', expires_in=GET_EXPIRES_IN,
        bucket=bucket, key=key
    )
    return redirect(signed_url)
