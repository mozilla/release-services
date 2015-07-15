# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import datetime
import json
import mock
import moto
import pytz

from nose.tools import eq_
from relengapi.blueprints.archiver import TASK_TIME_OUT
from relengapi.blueprints.archiver import cleanup_old_tasks
from relengapi.blueprints.archiver import delete_tracker
from relengapi.blueprints.archiver import tables
from relengapi.blueprints.archiver import update_tracker_state
from relengapi.blueprints.archiver.test_util import EXPECTED_TASK_STATUS_FAILED_RESPONSE
from relengapi.blueprints.archiver.test_util import EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE
from relengapi.blueprints.archiver.test_util import create_s3_items
from relengapi.blueprints.archiver.test_util import fake_200_response
from relengapi.blueprints.archiver.test_util import fake_failed_task_status
from relengapi.blueprints.archiver.test_util import fake_incomplete_task_status
from relengapi.blueprints.archiver.test_util import fake_successful_task_status
from relengapi.blueprints.archiver.test_util import setup_buckets
from relengapi.lib import time

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

test_context = TestContext(config=cfg, databases=['relengapi'])


def create_fake_tracker_row(app, id, created_at=None, src_url='https://foo.com', state="PENDING"):
    if not created_at:
        created_at = time.now()
    session = app.db.session('relengapi')
    session.add(
        tables.ArchiverTask(task_id=id, created_at=created_at, src_url=src_url, state=state)
    )
    session.commit()


@moto.mock_s3
@test_context
def test_accepted_response_when_missing_s3_key(app, client):
    setup_buckets(app, cfg)
    with mock.patch("relengapi.blueprints.archiver.tasks.requests.get") as get, \
            mock.patch("relengapi.blueprints.archiver.tasks.requests.head") as head:
        # don't actually hit hg.m.o, we just care about starting a subprocess and
        # returning a 202 accepted
        get.return_value = fake_200_response()
        head.return_value = fake_200_response()
        resp = client.get('/archiver/hgmo/mozilla-central/9213957d166d?'
                          'subdir=testing/mozharness&preferred_region=us-west-2')
    eq_(resp.status_code, 202, resp.status)


@moto.mock_s3
@test_context
def test_redirect_response_when_found_s3_key(app, client):
    setup_buckets(app, cfg)
    rev, repo, subdir, suffix = '203e1025a826', 'mozilla-central', 'testing/mozharness', 'tar.gz'
    key = '{repo}-{rev}.{suffix}'.format(repo=repo, rev=rev, suffix=suffix)
    if subdir:
        key += '/{}'.format(subdir)
    create_s3_items(app, cfg, key=key)

    resp = client.get(
        '/archiver/hgmo/{repo}/{rev}?subdir={subdir}&suffix={suffix}'.format(
            rev=rev, repo=repo, subdir=subdir, suffix=suffix
        )
    )
    eq_(resp.status_code, 302, resp.status)


@moto.mock_s3
@test_context
def test_task_status_when_failed(app, client):
    expected_response = EXPECTED_TASK_STATUS_FAILED_RESPONSE
    with mock.patch("relengapi.blueprints.archiver.create_and_upload_archive") as caua:
        caua.AsyncResult.return_value = fake_failed_task_status()
        response = client.get('/archiver/status/{task_id}'.format(task_id=123))
    eq_(cmp(json.loads(response.data)['result'], expected_response), 0,
        "a failed task status check does not equal expected status.")


@moto.mock_s3
@test_context
def test_task_status_when_success(app, client):
    expected_response = EXPECTED_TASK_STATUS_SUCCESSFUL_RESPONSE
    with mock.patch("relengapi.blueprints.archiver.create_and_upload_archive") as caua:
        caua.AsyncResult.return_value = fake_successful_task_status()
        response = client.get('/archiver/status/{task_id}'.format(task_id=123))
    eq_(cmp(json.loads(response.data)['result'], expected_response), 0,
        "A successful task status check does not equal expected status.")


@moto.mock_s3
@test_context
def test_tracker_delete(app, client):
    with app.app_context():
        create_fake_tracker_row(app, 'foo')
        tracker = tables.ArchiverTask.query.filter(tables.ArchiverTask.task_id == 'foo').first()
        eq_(tracker.task_id, "foo", "original tracker did not persist")
        delete_tracker(tracker)
        tracker = tables.ArchiverTask.query.filter(tables.ArchiverTask.task_id == 'foo').first()
        eq_(tracker, None, "tracker was not deleted")


@moto.mock_s3
@test_context
def test_tracker_update(app, client):
    with app.app_context():
        create_fake_tracker_row(app, 'foo')
        tracker = tables.ArchiverTask.query.filter(tables.ArchiverTask.task_id == 'foo').first()
        eq_(tracker.state, "PENDING", "original tracker state did not persist")
        update_tracker_state(tracker, "SUCCESS")
        eq_(tracker.state, "SUCCESS", "original tracker state was not updated.")


@moto.mock_s3
@test_context
def test_tracker_added_when_celery_task_is_created(app, client):
    setup_buckets(app, cfg)
    with mock.patch("relengapi.blueprints.archiver.tasks.requests.get") as get, \
            mock.patch("relengapi.blueprints.archiver.tasks.requests.head") as head:
        # don't actually hit hg.m.o, we just care about starting a subprocess and
        # returning a 202 accepted
        get.return_value = fake_200_response()
        head.return_value = fake_200_response()
        client.get('/archiver/hgmo/mozilla-central/9213957d166d?'
                   'subdir=testing/mozharness&preferred_region=us-west-2')
        with app.app_context():
            expected_tracker_id = "mozilla-central-9213957d166d.tar.gz_testing_mozharness"
            tracker = tables.ArchiverTask.query.filter(
                tables.ArchiverTask.task_id == expected_tracker_id
            ).first()
            eq_(tracker.task_id, expected_tracker_id, "tracker was not created for celery task")


@moto.mock_s3
@test_context
def test_tracker_is_updated_when_task_state_changes_but_is_not_complete(app, client):
    with app.app_context():
        task_id = 'foo'
        session = app.db.session('relengapi')
        session.add(tables.ArchiverTask(task_id=task_id, created_at=time.now(),
                                        src_url='https://foo.com', state="PENDING"))
        session.commit()
        with mock.patch("relengapi.blueprints.archiver.create_and_upload_archive") as caua:
            caua.AsyncResult.return_value = fake_incomplete_task_status()
            client.get('/archiver/status/{task_id}'.format(task_id=task_id))
        tracker = tables.ArchiverTask.query.filter(tables.ArchiverTask.task_id == task_id).first()
        eq_(tracker.state, "STARTED", "tracker not updated even though celery task state changed.")


@moto.mock_s3
@test_context
def test_tracker_is_deleted_when_task_status_shows_task_complete(app, client):
    with app.app_context():
        task_id = 'foo'
        session = app.db.session('relengapi')
        session.add(tables.ArchiverTask(task_id=task_id, created_at=time.now(),
                                        src_url='https://foo.com', state="PENDING"))
        session.commit()
        with mock.patch("relengapi.blueprints.archiver.create_and_upload_archive") as caua:
            caua.AsyncResult.return_value = fake_successful_task_status()
            client.get('/archiver/status/{task_id}'.format(task_id=task_id))
        tracker = tables.ArchiverTask.query.filter(tables.ArchiverTask.task_id == task_id).first()
        eq_(tracker, None, "tracker was not deleted even though celery task completed.")


@moto.mock_s3
@test_context
def test_tracker_is_deleted_when_task_is_complete_but_s3_url_not_present(app, client):
    now = datetime.datetime(2015, 7, 14, 23, 19, 42, tzinfo=pytz.UTC)  # freeze time
    older_time = now - datetime.timedelta(seconds=TASK_TIME_OUT + 10)
    old_task_id = "mozilla-central-9213957d166d.tar.gz_testing_mozharness"
    create_fake_tracker_row(app, old_task_id, created_at=older_time, state="SUCCESS")
    setup_buckets(app, cfg)
    with mock.patch("relengapi.blueprints.archiver.tasks.requests.get") as get, \
            mock.patch("relengapi.blueprints.archiver.tasks.requests.head") as head, \
            mock.patch('relengapi.blueprints.archiver.now') as time_traveller:
        time_traveller.return_value = now
        # don't actually hit hg.m.o, we just care about starting a subprocess and
        # returning a 202 accepted
        get.return_value = fake_200_response()
        head.return_value = fake_200_response()

        with app.app_context():
            old_task = tables.ArchiverTask.query.filter(
                tables.ArchiverTask.task_id == old_task_id
            ).first()
            eq_(old_task.created_at, older_time,
                "old_task tracker created_at column doesn't match expected")
            # now query api for an archive that would match an id with a tracker still in the db.
            # Since the task tracker will show as complete yet there is still no s3 url, the current
            # old tracker should be deleted and a new one created along with a new celery task
            client.get('/archiver/hgmo/mozilla-central/9213957d166d?'
                       'subdir=testing/mozharness&preferred_region=us-west-2')
            tracker = tables.ArchiverTask.query.filter(
                tables.ArchiverTask.task_id == old_task_id
            ).first()
            eq_(tracker.created_at, now, "old completed tracker was never re-created")
            eq_(tracker.state, "PENDING", "old completed tracker was never re-created")


@moto.mock_s3
@test_context
def test_task_tracker_badpenny_cleanup(app, client):
    now = datetime.datetime(2015, 7, 14, 23, 19, 42, tzinfo=pytz.UTC)  # freeze time
    with app.app_context():
        session = app.db.session('relengapi')
        with mock.patch('relengapi.blueprints.archiver.now') as time_traveller:
            time_traveller.return_value = now

            # create some tasks
            expired_time1 = now - datetime.timedelta(seconds=TASK_TIME_OUT + 10)
            expired_time2 = now - datetime.timedelta(seconds=TASK_TIME_OUT + 20)
            valid_time1 = now - datetime.timedelta(seconds=TASK_TIME_OUT - 10)
            create_fake_tracker_row(app, 'expired_task1', created_at=expired_time1)
            create_fake_tracker_row(app, 'expired_task2', created_at=expired_time2)
            create_fake_tracker_row(app, 'valid_task1', created_at=valid_time1)
            # ensure they were created
            eq_(session.query(tables.ArchiverTask).count(), 3,
                "couldn't create fake task trackers for testing.")
            # force run badpenny clean up job
            cleanup_old_tasks()
            eq_(session.query(tables.ArchiverTask).count(), 1,
                "expected only one tracker task to persist after cleaning up old tasks")
            tracker = session.query(tables.ArchiverTask).first()
            eq_(tracker.task_id, 'valid_task1',
                "remaining tracker did not match expected.")
