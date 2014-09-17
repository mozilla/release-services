# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import multiprocessing
import os
import shutil
import signal

from celery.signals import worker_ready
from nose.tools import assert_raises
from nose.tools import eq_
from relengapi.lib import celery
from relengapi.lib.testing.context import TestContext

test_temp_dir = os.path.join(os.path.dirname(__file__), 'test_temp')


def setup_module():
    if os.path.exists(test_temp_dir):
        shutil.rmtree(test_temp_dir)
    os.makedirs(test_temp_dir)


def teardown_module():
    if os.path.exists(test_temp_dir):
        shutil.rmtree(test_temp_dir)


def _run(app, event):
    # since celery insists on printing its stuff to sys.__stdout__
    # and sys.__stderr__..
    import sys
    sys.__stdout__ = sys.stdout
    sys.__stderr__ = sys.stdout

    # make the kombu transport poll more frequently..
    from kombu.transport.virtual import Transport
    Transport.polling_interval = 0.01

    # let the parent process know the worker is ready
    @worker_ready.connect
    def rdy(sender, **kwargs):
        event.set()

    # poll the db very frequently, to make sure the tests pass quickly
    app.celery.Worker().start()


@contextlib.contextmanager
def running_worker(app):
    ready_event = multiprocessing.Event()
    proc = multiprocessing.Process(target=_run, args=(app, ready_event))
    proc.start()
    # wait until the worker is ready.  This gives it a chance to set up all
    # of the tables and data in the DB; otherwise, it would race with this
    # process and fail periodically
    ready_event.wait()
    try:
        yield
    finally:
        # send SIGKILL since celery traps SIGTERM and turns it into an exception
        # which SQLAlchemy catches and ignores
        # (see https://github.com/mozilla/build-relengapi/issues/90)
        os.kill(proc.pid, signal.SIGKILL)
        proc.join()


test_context = TestContext(config={
    'CELERY_BROKER_URL': 'sqla+sqlite:///%s/celery.db' % test_temp_dir,
    'CELERY_RESULT_BACKEND': 'db+sqlite:///%s/celery.db' % test_temp_dir,
    'CELERYD_POOL': 'solo',
})


@celery.task
def test_task(a, b):
    return a + b


@celery.task(serializer='json')
def test_task_with_args(x, y):
    return x * y


@test_context
def test_add(app):
    with running_worker(app):
        with app.app_context():
            eq_(test_task.delay(1, 2).get(interval=0.01), 3)


@test_context
def test_mult(app):
    with running_worker(app):
        with app.app_context():
            eq_(test_task_with_args.delay(2, 3).get(interval=0.01), 6)


def test_bad_decorator_use():
    assert_raises(TypeError, lambda: celery.task(None))


def test_relengapi_celery_module():
    """The module path `relengapi.celery.celery` exists and is a Celery object,
    as `celery -A relengapi` expects"""
    import relengapi.celery
    # this has to point somewhere, so point it at this directory's __init__.py
    os.environ['RELENGAPI_SETTINGS'] = os.path.join(os.path.dirname(__file__), '__init__.py')
    try:
        eq_(type(relengapi.celery.celery).__name__, 'Celery')
    finally:
        del os.environ['RELENGAPI_SETTINGS']
