# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from celery import Celery
from flask import current_app
from werkzeug.local import LocalProxy

_defined_tasks = {}


def make_celery(app):
    broker = app.config.get('CELERY_BROKER_URL', 'memory://')
    celery = Celery(app.import_name, broker=broker)
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
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
