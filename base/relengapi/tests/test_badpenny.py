# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import datetime

from nose.tools import eq_
from nose.tools import raises
from relengapi.lib import badpenny


@contextlib.contextmanager
def empty_registry():
    old_registry = badpenny.Task._registry
    badpenny.Task._registry = {}
    try:
        yield
    finally:
        badpenny.Task._registry = old_registry


def test_periodic_task():
    """The periodic_task decorator takes a `seconds` argument and creates a task"""
    with empty_registry():
        @badpenny.periodic_task(seconds=10)
        def run_me(job):
            return job
        t = badpenny.Task.get('{}.run_me'.format(__name__))
        eq_(t.schedule, 'every 10 seconds')
        base = datetime.datetime(2014, 8, 12, 15, 59, 17)
        eq_(t.get_next_time(base),
            datetime.datetime(2014, 8, 12, 15, 59, 27))


def test_cron_task():
    """The cron_task decorator takes a cron spec argument and creates a task"""
    with empty_registry():
        @badpenny.cron_task('13 * * * *')
        def run_me(job):
            return job
        t = badpenny.Task.get('{}.run_me'.format(__name__))
        eq_(t.schedule, 'cron: 13 * * * *')
        base = datetime.datetime(2014, 8, 12, 15, 59, 17)
        eq_(t.get_next_time(base),
            datetime.datetime(2014, 8, 12, 16, 13, 00))


@raises(Exception)
def test_cron_task_invalid():
    """The cron_task decorator errors out immediately on an invalid cron spece."""
    with empty_registry():
        badpenny.cron_task('13 * * * * * *')


def test_list_tasks():
    """Task.list lists all registered tasks"""
    with empty_registry():
        eq_(badpenny.Task.list(), [])

        @badpenny.periodic_task(seconds=10)
        def run_me(job):
            return job
        eq_([t.name for t in badpenny.Task.list()],
            ['{}.run_me'.format(__name__)])
