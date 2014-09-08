# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import croniter

from datetime import datetime
from dateutil.relativedelta import relativedelta


class Task(object):

    _registry = {}

    def __init__(self, task_func, get_next_time, schedule):
        self.task_func = task_func
        self.get_next_time = get_next_time
        self.schedule = schedule
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


def _task_decorator(get_next_time, schedule):
    def dec(task_func):
        Task(task_func, get_next_time, schedule).register()
        return task_func
    return dec


def periodic_task(seconds):
    """Decorator for a periodic task executed ever INTERVAL seconds"""
    assert seconds > 0
    delta = relativedelta(seconds=seconds)

    def get_next_time(last_run):
        return last_run + delta
    return _task_decorator(get_next_time, "every %d seconds" % seconds)


def cron_task(cron_spec):
    """Decorator for a task that executes on a cron-like schedule"""
    # test the cron spec before the function is called
    croniter.croniter(cron_spec)

    def get_next_time(last_run):
        ci = croniter.croniter(cron_spec, last_run)
        return ci.get_next(datetime)
    return _task_decorator(get_next_time, "cron: %s" % cron_spec)
