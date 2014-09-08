# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import datetime
import mock

from flask import json
from nose.tools import eq_
from relengapi.blueprints.badpenny import BadpennyJob
from relengapi.blueprints.badpenny import BadpennyTask
from relengapi.blueprints.badpenny import JsonJob
from relengapi.blueprints.badpenny import JsonTask
from relengapi.lib.permissions import p
from relengapi.testing import TestContext


dt = datetime.datetime

test_context = TestContext(databases=['relengapi'],
                           reuse_app=True)


def insert_job(app, task_id, created_at, **kwargs):
    session = app.db.session('relengapi')
    j = BadpennyJob(task_id=task_id, created_at=created_at, **kwargs)
    session.add(j)
    session.commit()
    return j


def insert_task(app, name):
    session = app.db.session('relengapi')
    t = BadpennyTask(name=name)
    session.add(t)
    session.commit()
    return t

cleanup_task = JsonTask(active=False, name="cleanup", last_success=0)
cleanup_job_1 = JsonJob(
    id=1,
    result=json.dumps({"deleted": 6}),
    successful=True,
    logs=None,
    task_name='cleanup',
    created_at=dt(1978, 6, 15),
    started_at=dt(1978, 6, 15, 12),
    completed_at=dt(1978, 6, 15, 13))
cleanup_job_2 = JsonJob(
    id=2,
    result=json.dumps({"error": "ETIMEOUT"}),
    successful=False,
    logs="Trying..\nTrying..\nTimed out :(\n",
    task_name='cleanup',
    created_at=dt(1978, 6, 16),
    started_at=dt(1978, 6, 16, 12),
    completed_at=dt(1978, 6, 16, 13))

report_task = JsonTask(active=False, name="report", last_success=1)
report_job_1 = JsonJob(
    id=3,
    result=json.dumps({}),
    successful=True,
    logs=None,
    task_name='report',
    created_at=dt(1978, 6, 2),
    started_at=dt(1978, 6, 2, 12),
    completed_at=dt(1978, 6, 2, 13))

check_task = JsonTask(active=False, name="check", last_success=-1)


def add_data(app):
    task_id = insert_task(app, 'cleanup').id
    assert insert_job(
        app,
        task_id=task_id,
        created_at=dt(1978, 6, 15),
        started_at=dt(1978, 6, 15, 12),
        completed_at=dt(1978, 6, 15, 13),
        successful=True,
        result=json.dumps({'deleted': 6})).id == cleanup_job_1.id

    assert insert_job(
        app,
        task_id=task_id,
        created_at=dt(1978, 6, 16),
        started_at=dt(1978, 6, 16, 12),
        completed_at=dt(1978, 6, 16, 13),
        successful=False,
        result=json.dumps({'error': 'ETIMEOUT'}),
        logs="Trying..\nTrying..\nTimed out :(\n").id == cleanup_job_2.id

    task_id = insert_task(app, 'report').id

    assert insert_job(app,
                      task_id=task_id,
                      created_at=dt(1978, 6, 2),
                      started_at=dt(1978, 6, 2, 12),
                      completed_at=dt(1978, 6, 2, 13),
                      successful=True,
                      result=json.dumps({})).id == report_job_1.id

    insert_task(app, 'check')


@contextlib.contextmanager
def active_tasks(*tasks):
    with mock.patch('relengapi.lib.badpenny.Task.get') as get:
        # make some fake tasks
        tasks = dict((task, mock.Mock(name=task,
                                      schedule='schedule for {}'.format(task)))
                     for task in tasks)
        get.side_effect = tasks.get
        yield

# tests


@test_context.specialize(app_setup=add_data)
def test_to_jsontask(app):
    """Converting a BadpennyTask to a JsonTask produces well-formed output"""
    with app.test_request_context():
        t = BadpennyTask.query.filter(BadpennyTask.name == 'cleanup').first()
        eq_(json.dumps(t.to_jsontask()), json.dumps(cleanup_task))
        t = BadpennyTask.query.filter(BadpennyTask.name == 'report').first()
        eq_(json.dumps(t.to_jsontask(with_jobs=True)),
            json.dumps(JsonTask(active=False, name="report", last_success=1,
                                jobs=[report_job_1])))


@test_context.specialize(app_setup=add_data)
def test_last_success(app):
    """The last_success property returns -1 for never, 0 for failure, and 1 for success"""
    q = lambda name: BadpennyTask.query.filter(
        BadpennyTask.name == name).first()
    with app.test_request_context():
        eq_(q('cleanup').last_success, 0)
        eq_(q('report').last_success, 1)
        eq_(q('check').last_success, -1)


@test_context.specialize(app_setup=add_data)
def test_unique_task(app):
    """Finding a task with `as_unique` either creates a new task row or finds an existing row"""
    with app.test_request_context():
        sess = app.db.session('relengapi')
        check_id = BadpennyTask.query.filter(
            BadpennyTask.name == 'check').first().id
        existing_task = BadpennyTask.as_unique(sess, name='check')
        eq_(existing_task.id, check_id)
        new_task = BadpennyTask.as_unique(sess, name='update')
        assert new_task.id == BadpennyTask.query.filter(
            BadpennyTask.name == 'update').first().id


@test_context.specialize(app_setup=add_data)
def test_to_jsonjob(app):
    """Converting a BadpennyJob to a JsonJob produces output with matching fields"""
    with app.test_request_context():
        j = BadpennyJob.query.filter(
            BadpennyJob.id == cleanup_job_2.id).first()
        eq_(json.dumps(j.to_jsonjob()), json.dumps(cleanup_job_2))


@test_context.specialize(perms=[p.base.badpenny.view])
def test_ui_view(app, client):
    """The UI view renders something with some JavaScript"""
    with app.test_request_context():
        resp = client.get('/badpenny/')
        assert 'badpenny.js' in resp.data


def test_perms_required():
    """Badpenny paths all require the base.badpenny.view permission"""
    paths = [
        '/badpenny/',
        '/badpenny/tasks',
        '/badpenny/tasks/abc',
        '/badpenny/jobs/123',
    ]

    @test_context
    def t(path, app, client):
        with app.test_request_context():
            resp = client.get(path)
            eq_(resp.status_code, 403)
    for path in paths:
        yield t, path


@test_context.specialize(app_setup=add_data, perms=[p.base.badpenny.view])
def test_get_tasks(app, client):
    """Getting /tasks gets a list of all active tasks, in unspecified order"""
    with app.test_request_context():
        resp = client.get('/badpenny/tasks')
        # nothing's active by default
        eq_(json.loads(resp.data)['result'], [])
        with active_tasks('check', 'cleanup'):
            resp = client.get('/badpenny/tasks')
            eq_(sorted([t['name'] for t in json.loads(resp.data)['result']]),
                sorted(['check', 'cleanup']))


@test_context.specialize(app_setup=add_data, perms=[p.base.badpenny.view])
def test_get_all_tasks(app, client):
    """Getting /tasks?all gets a list of all tasks, including inactive, in
    unspecified order"""
    with app.test_request_context():
        resp = client.get('/badpenny/tasks?all=1')
        eq_(sorted([t['name'] for t in json.loads(resp.data)['result']]),
            sorted(['check', 'report', 'cleanup']))


@test_context.specialize(app_setup=add_data, perms=[p.base.badpenny.view])
def test_get_task(app, client):
    """Getting /tasks/$task returns the appropriate task"""
    with app.test_request_context():
        resp = client.get('/badpenny/tasks/check')
        eq_(json.loads(resp.data)['result'],
            {'active': False, 'name': 'check', 'last_success': -1, 'jobs': []})


@test_context.specialize(app_setup=add_data, perms=[p.base.badpenny.view])
def test_get_task_nosuch(app, client):
    """Getting /tasks/$task returns 404 if no such task exists"""
    with app.test_request_context():
        resp = client.get('/badpenny/tasks/nosuch')
        eq_(resp.status_code, 404)


@test_context.specialize(app_setup=add_data, perms=[p.base.badpenny.view])
def test_get_active_task(app, client):
    """Getting /tasks/$task returns active and a schedule for an active task"""
    with app.test_request_context():
        with active_tasks('check'):
            resp = client.get('/badpenny/tasks/check')
            eq_(json.loads(resp.data)['result'],
                {'active': True, 'schedule': 'schedule for check',
                 'name': 'check', 'last_success': -1, 'jobs': []})


@test_context.specialize(app_setup=add_data, perms=[p.base.badpenny.view])
def test_get_jobs(app, client):
    """Getting /jobs gets a list of all jobs, in unspecified order"""
    with app.test_request_context():
        resp = client.get('/badpenny/jobs')
        eq_(sorted([(t['id'], t['task_name']) for t in json.loads(resp.data)['result']]),
            sorted([
                (cleanup_job_1.id, 'cleanup'),
                (cleanup_job_2.id, 'cleanup'),
                (report_job_1.id, 'report'),
            ]))


@test_context.specialize(app_setup=add_data, perms=[p.base.badpenny.view])
def test_get_job(app, client):
    """Getting /jobs/$jobid returns the appropriate job, or a 404"""
    with app.test_request_context():
        resp = client.get('/badpenny/jobs/{}'.format(report_job_1.id))
        eq_(json.loads(resp.data)['result'],
            json.loads(json.dumps(report_job_1)))
        resp = client.get('/badpenny/jobs/9999999')
        eq_(resp.status_code, 404)
