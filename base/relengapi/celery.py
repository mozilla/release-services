from __future__ import absolute_import

from flask import current_app
from werkzeug.local import LocalProxy
import types
import sys
from celery import Celery

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
    app.celery_tasks = {}
    return celery

def task(bp, *args, **kwargs):
    """Register the decorated method as a celery task; use this just like
    app.task, but always pass the blueprint.  Any arguments beyond the first
    will be treated as arguments to app.task"""
    # This is a little tricky; the decorator returns a LocalProxy that will look
    # up the appropriate Celery task object, using the app.celery_tasks dictionary.
    def wrap(fn):
        @bp.record
        def register(state):
            task = state.app.celery.task(*args, **kwargs)(fn)
            state.app.celery_tasks[fn] = task
        return LocalProxy(lambda: current_app.celery_tasks[fn])
    return wrap


# Replace this module with a subclass, so that we can add an 'celery' property
# that will create a new Flask app and Celery app on demand.  This lets 'celery
# -A relengapi worker' work as expected.  This, too, is a bit tricky but the
# result is elegant.

class PropModule(types.ModuleType):

    @property
    def celery(self):
        import relengapi.app
        app = relengapi.app.create_app()
        return app.celery

old_module = sys.modules[__name__]
new_module = PropModule(__name__)
new_module.__dict__.update(old_module.__dict__)
