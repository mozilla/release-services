# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import croniter

from datetime import datetime
from dateutil.relativedelta import relativedelta


class Task(object):

    _registry = {}

    def __init__(self, task_func, runnable_now, schedule):
        self.task_func = task_func
        self.runnable_now = runnable_now
        self.schedule = schedule
        self.task_id = None  # set by sync_tasks
        self.name = "{}.{}".format(
            task_func.__module__, task_func.__name__)

    def register(self):
        assert self.name not in self._registry
        self._registry[self.name] = self

    @classmethod
    def list(cls):
        return cls._registry.values()

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)


def _task_decorator(runnable_now, schedule):
    def dec(task_func):
        Task(task_func, runnable_now, schedule).register()
        return task_func
    return dec


def periodic_task(seconds):
    """Decorator for a periodic task executed ever INTERVAL seconds"""
    assert seconds > 0
    delta = relativedelta(seconds=seconds)

    def runnable_now(task, now):
        last_run = max(j.created_at for j in task.jobs) if task.jobs else None
        if last_run:
            return now >= last_run + delta
        else:
            return True
    return _task_decorator(runnable_now, "every %d seconds" % seconds)


def cron_task(cron_spec):
    """Decorator for a task that executes on a cron-like schedule"""
    # test the cron spec before the function is called
    croniter.croniter(cron_spec)

    def runnable_now(task, now):
        last_run = max(j.created_at for j in task.jobs) if task.jobs else None
        ci = croniter.croniter(cron_spec, last_run)
        return now >= ci.get_next(datetime)
    return _task_decorator(runnable_now, "cron: %s" % cron_spec)
