# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import datetime
import mock
import pytz

from flask import json
from nose.tools import eq_
from relengapi.blueprints.badpenny import cleanup
from relengapi.blueprints.badpenny import cron
from relengapi.blueprints.badpenny import execution
from relengapi.blueprints.badpenny import rest
from relengapi.blueprints.badpenny import tables
from relengapi.lib import badpenny
from relengapi.lib.permissions import p
from relengapi.lib.testing.context import TestContext


dt = lambda *args: datetime.datetime(*args, tzinfo=pytz.UTC)

test_context = TestContext(databases=['relengapi'],
                           reuse_app=True)


def insert_job(app, task_id, created_at, **kwargs):
    session = app.db.session('relengapi')
    j = tables.BadpennyJob(task_id=task_id, created_at=created_at, **kwargs)
    session.add(j)
    session.commit()
    return j


def insert_task(app, name):
    session = app.db.session('relengapi')
    t = tables.BadpennyTask(name=name)
    session.add(t)
    session.commit()
    return t

cleanup_task = rest.BadpennyTask(active=False, name="cleanup", last_success=0)
cleanup_job_1 = rest.BadpennyJob(
    id=1,
    result=json.dumps({"deleted": 6}),
    successful=True,
    logs=None,
    task_name='cleanup',
    created_at=dt(1978, 6, 15),
    started_at=dt(1978, 6, 15, 12),
    completed_at=dt(1978, 6, 15, 13))
cleanup_job_2 = rest.BadpennyJob(
    id=2,
    result=json.dumps({"error": "ETIMEOUT"}),
    successful=False,
    logs="Trying..\nTrying..\nTimed out :(\n",
    task_name='cleanup',
    created_at=dt(1978, 6, 16),
    started_at=dt(1978, 6, 16, 12),
    completed_at=dt(1978, 6, 16, 13))

report_task = rest.BadpennyTask(active=False, name="report", last_success=1)
report_job_1 = rest.BadpennyJob(
    id=3,
    result=json.dumps({}),
    successful=True,
    logs=None,
    task_name='report',
    created_at=dt(1978, 6, 2),
    started_at=dt(1978, 6, 2, 12),
    completed_at=dt(1978, 6, 2, 13))

check_task = rest.BadpennyTask(active=False, name="check", last_success=-1)


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
    """Converting a tables.BadpennyTask to a rest.BadpennyTask produces well-formed output"""
    with app.test_request_context():
        t = tables.BadpennyTask.query.filter(
            tables.BadpennyTask.name == 'cleanup').first()
        eq_(json.dumps(t.to_jsontask()), json.dumps(cleanup_task))
        t = tables.BadpennyTask.query.filter(
            tables.BadpennyTask.name == 'report').first()
        eq_(json.dumps(t.to_jsontask(with_jobs=True)),
            json.dumps(rest.BadpennyTask(active=False, name="report", last_success=1,
                                         jobs=[report_job_1])))


@test_context.specialize(app_setup=add_data)
def test_last_success(app):
    """The last_success property returns -1 for never, 0 for failure, and 1 for success"""
    q = lambda name: tables.BadpennyTask.query.filter(
        tables.BadpennyTask.name == name).first()
    with app.test_request_context():
        eq_(q('cleanup').last_success, 0)
        eq_(q('report').last_success, 1)
        eq_(q('check').last_success, -1)


@test_context.specialize(app_setup=add_data)
def test_unique_task(app):
    """Finding a task with `as_unique` either creates a new task row or finds an existing row"""
    with app.test_request_context():
        sess = app.db.session('relengapi')
        check_id = tables.BadpennyTask.query.filter(
            tables.BadpennyTask.name == 'check').first().id
        existing_task = tables.BadpennyTask.as_unique(sess, name='check')
        eq_(existing_task.id, check_id)
        new_task = tables.BadpennyTask.as_unique(sess, name='update')
        assert new_task.id == tables.BadpennyTask.query.filter(
            tables.BadpennyTask.name == 'update').first().id


@test_context.specialize(app_setup=add_data)
def test_to_jsonjob(app):
    """Converting a tables.BadpennyJob to a rest.BadpennyJob produces output with matching fields"""
    with app.test_request_context():
        j = tables.BadpennyJob.query.filter(
            tables.BadpennyJob.id == cleanup_job_2.id).first()
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

# badpenny_cron


@contextlib.contextmanager
def empty_registry():
    old_registry = badpenny.Task._registry
    badpenny.Task._registry = {}
    try:
        yield
    finally:
        badpenny.Task._registry = old_registry


def fake_task_func(name):
    func = lambda j: None
    func.__module__ = 'test'
    func.__name__ = name
    return func


@test_context
def test_cron_sync_tasks(app):
    """The `sync_tasks` method inserts new rows into the DB for any new
    registered tasks, and sets task.task_id"""
    cmd = cron.BadpennyCron()
    with app.app_context():
        with empty_registry():
            badpenny.periodic_task(seconds=10)(fake_task_func('foo'))
            badpenny.periodic_task(seconds=10)(fake_task_func('bar'))
            cmd.sync_tasks()

            dbtasks = tables.BadpennyTask.query.all()
            eq_(sorted([t.name for t in dbtasks]),
                sorted(['test.foo', 'test.bar']))

            badpenny.periodic_task(seconds=30)(fake_task_func('bing'))
            cmd.sync_tasks()

            dbtasks = tables.BadpennyTask.query.all()
            eq_(sorted([t.name for t in dbtasks]),
                sorted(['test.foo', 'test.bar', 'test.bing']))

            eq_(sorted([t.task_id for t in badpenny.Task.list()]), [1, 2, 3])


@test_context
def test_cron_runnable_tasks(app):
    """The `runnable_tasks` method yields Task instances for runnable tasks"""

    def runnable_yes(bpt, now):
        assert isinstance(bpt, tables.BadpennyTask)
        eq_(now, 'now')
        return True

    def runnable_no(bpt, now):
        assert isinstance(bpt, tables.BadpennyTask)
        eq_(now, 'now')
        return False

    cmd = cron.BadpennyCron()
    with app.app_context():
        with empty_registry():
            badpenny._task_decorator(runnable_yes, 'y')(fake_task_func('yes'))
            badpenny._task_decorator(runnable_no, 'n')(fake_task_func('no'))
            cmd.sync_tasks()

            tasks = list(cmd.runnable_tasks('now'))
            eq_([t.name for t in tasks], ['test.yes'])


@test_context
def test_cron_run_task(app):
    """The `run_task` method inserts a new BadpennyJob row"""
    cmd = cron.BadpennyCron()
    with app.app_context():
        badpenny.periodic_task(seconds=10)(fake_task_func('ten'))
        cmd.sync_tasks()
        task = badpenny.Task.get('test.ten')

        today = dt(2014, 9, 6, 16, 10, 45)
        with mock.patch('relengapi.lib.time.now') as now:
            now.return_value = today
            cmd.run_task(task)

        job = tables.BadpennyJob.query.first()
        eq_(job.task_id, task.task_id)
        eq_(job.created_at, today)
        eq_(job.started_at, None)
        eq_(job.completed_at, None)


def test_cron_run():
    """The `relengapi badpenny-cron` script syncs tasks, gets the list of runnable tasks,
    and then runs them."""
    cmd = cron.BadpennyCron()
    with mock.patch.multiple('relengapi.blueprints.badpenny.cron.BadpennyCron',
                             sync_tasks=mock.DEFAULT,
                             runnable_tasks=mock.DEFAULT,
                             run_task=mock.DEFAULT) as mocks:
        tasks = [tables.BadpennyTask(name=n) for n in '01']
        mocks['runnable_tasks'].return_value = tasks
        cmd.run(None, None)
        mocks['sync_tasks'].assert_called_with()
        mocks['runnable_tasks'].assert_called_with(mock.ANY)
        eq_(mocks['run_task'].mock_calls, [
            mock.call(tasks[0]), mock.call(tasks[1])])

# task execution


def test_submit_job():
    """`execution.submit_job` just invokes _run_job via Celery"""
    with mock.patch('relengapi.blueprints.badpenny.execution._run_job') as _run_job:
        execution.submit_job('foo', 10)
        _run_job.delay.assert_called_with('foo', 10)


@contextlib.contextmanager
def run_job_setup():
    task_ran = []
    with empty_registry():
        @badpenny.periodic_task(seconds=1)
        def my_task(js):
            assert isinstance(js, execution.JobStatus)
            task_ran.append(1)
            js.log_message('HELLO')
            return 'RES'

        @badpenny.periodic_task(seconds=1)
        def failz(js):
            task_ran.append(1)
            raise RuntimeError('oh noes')

        yield task_ran


@test_context
def test_run_job_no_such_task(app):
    """`execution._run_job` ignores runs with no matching task"""
    with run_job_setup() as task_ran:
        # no such task..
        with app.app_context():
            execution._run_job.apply((__name__ + '.nosuch', 10))
        assert not task_ran


@test_context
def test_run_job_no_job(app):
    """`execution._run_job` ignores runs with no existing job row"""
    with run_job_setup() as task_ran:
        with app.app_context():
            execution._run_job.apply((__name__ + '.my_task', 10))
        assert not task_ran


@test_context
def test_run_job_success(app):
    """`execution._run_job` runs a job and updates the job row."""
    with run_job_setup() as task_ran:
        with app.app_context():
            job = tables.BadpennyJob(task_id=10, created_at=dt(2014, 9, 16))
            app.db.session('relengapi').add(job)
            app.db.session('relengapi').commit()
            execution._run_job.apply((__name__ + '.my_task', job.id))
        assert task_ran

        assert 'HELLO' in job.logs
        assert job.started_at is not None
        assert job.completed_at is not None
        eq_(json.loads(job.result), 'RES')
        eq_(job.successful, True)


@test_context
def test_run_job(app):
    """When a job fails, `execution._run_job` logs the exception."""
    with run_job_setup() as task_ran:
        with app.app_context():
            job = tables.BadpennyJob(task_id=10, created_at=dt(2014, 9, 16))
            app.db.session('relengapi').add(job)
            app.db.session('relengapi').commit()
            execution._run_job.apply((__name__ + '.failz', job.id))
        assert task_ran

        assert 'oh noes' in job.logs
        assert job.started_at is not None
        assert job.completed_at is not None
        eq_(json.loads(job.result), None)
        eq_(job.successful, False)

# cleanup


@test_context.specialize(reuse_app=False)
def test_cleanup(app):
    """The cleanup task deletes jobs older than 7 days"""
    job_status = mock.Mock(spec=execution.JobStatus)
    with app.app_context():
        session = app.db.session('relengapi')
        task = tables.BadpennyTask(name='foo')
        session.add(task)
        newjob = lambda id, created_at: task.jobs.append(
            tables.BadpennyJob(id=id, task_id=task.id,
                               created_at=created_at))
        newjob(1, dt(2014, 9, 20))
        newjob(2, dt(2014, 9, 15))
        newjob(3, dt(2014, 9, 10))
        newjob(4, dt(2014, 9, 5))
        session.commit()
        with mock.patch('relengapi.blueprints.badpenny.cleanup.time.now') as now:
            now.return_value = dt(2014, 9, 16)
            cleanup.cleanup_old_jobs(job_status)

        eq_(sorted([j.id for j in tables.BadpennyJob.query.all()]),
            sorted([1, 2, 3]))  # 4 is gone
