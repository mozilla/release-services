# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging

import structlog
from celery import Celery
from celery.signals import celeryd_after_setup
from celery.signals import task_postrun
from celery.signals import task_prerun
from flask import current_app
from werkzeug.local import LocalProxy

from relengapi.lib import badpenny
from relengapi.lib import logging as relengapi_logging

_defined_tasks = {}
logger = structlog.get_logger()


def make_celery(app):
    # default to using JSON, rather than Pickle (Celery's default, but Celery
    # warns about it)
    for var, dfl in [
            ('CELERY_ACCEPT_CONTENT', ['json']),
            ('CELERY_TASK_SERIALIZER', 'json'),
            ('CELERY_RESULT_SERIALIZER', 'json')]:
        app.config[var] = app.config.get(var, dfl)
    broker = app.config.get('CELERY_BROKER_URL', 'memory://')
    celery = Celery(app.import_name, broker=broker)
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                try:
                    return TaskBase.__call__(self, *args, **kwargs)
                finally:
                    # flush any open DB sessions used by this task
                    current_app.db.flush_sessions()

    celery.Task = ContextTask
    app.celery_tasks = dict((fn, celery.task(**kwargs)(fn))
                            for (fn, kwargs) in _defined_tasks.iteritems())
    return celery


def task(*args, **kwargs):
    """Register the decorated method as a celery task; use this just like
    app.task."""
    def inner(**kwargs):
        def wrap(fn):
            _defined_tasks[fn] = kwargs
            return LocalProxy(lambda: current_app.celery_tasks[fn])
        return wrap
    # remainder of this function is adapted from celery/app/base.py
    # (BSD-licensed)
    if len(args) == 1:
        if callable(args[0]):
            return inner(**kwargs)(*args)
        raise TypeError('argument 1 to @task() must be a callable')
    if args:
        raise TypeError(
            '@db.task() takes exactly 1 argument ({0} given)'.format(
                sum([len(args), len(kwargs)])))
    return inner(**kwargs)


@badpenny.periodic_task(3600 * 24)
def backend_cleanup(js):
    # Celery's built-in backend_cleanup task depends on Beat, which relengapi
    # does not use, so we just run it via badpenny.  These conditions attempt
    # to replicate those in Celery's `celery/beat.py`
    c = current_app.celery
    if c.conf.CELERY_TASK_RESULT_EXPIRES and not c.backend.supports_autoexpire:
        backend_cleanup_task = c.tasks['celery.backend_cleanup']
        backend_cleanup_task.apply()


@task_prerun.connect
def per_task_setup(sender, task_id, task, args, kwargs, **_kwargs):
    relengapi_logging.reset_context(task_id=task_id, task_name=task.name)
    logger.info("starting task %s" % (task_id,))


@task_postrun.connect
def log_task_complete(sender, task_id, task, args, kwargs, **_kwargs):
    logger.info("completed task %s" % (task_id,))


@celeryd_after_setup.connect
def setup_relengapi_logging(sender, instance, conf, **kwargs):
    _relengapi_log_lvl = conf.get("RELENGAPI_CELERY_LOG_LEVEL", None)
    if _relengapi_log_lvl:
        n = logging.getLogger('relengapi')
        n.setLevel(_relengapi_log_lvl)
        n.debug("Setting relengapi logger to %s", _relengapi_log_lvl)
