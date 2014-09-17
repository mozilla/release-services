# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import pytz
import threading
import time

from mock import patch
from nose.tools import assert_raises
from nose.tools import eq_
from relengapi import util
from relengapi.lib.testing.context import TestContext
from relengapi.util import tz


class TestSynchronized(object):

    lock = threading.Lock()

    @util.synchronized(lock)
    def syncd(self, ident, finish_event):
        with self.cond:
            self.results.append("start %d" % ident)
            self.cond.notify()
        finish_event.wait()
        with self.cond:
            self.results.append("finish %d" % ident)
            self.cond.notify()

    def run(self, ident, start_event, finish_event):
        start_event.wait()
        self.syncd(ident, finish_event)

    def test_synchronized(self):
        self.cond = threading.Condition()
        self.results = []

        start1, finish1 = threading.Event(), threading.Event()
        thd1 = threading.Thread(target=self.run, args=(1, start1, finish1))
        thd1.setDaemon(1)
        thd1.start()

        start2, finish2 = threading.Event(), threading.Event()
        thd2 = threading.Thread(target=self.run, args=(2, start2, finish2))
        thd2.setDaemon(1)
        thd2.start()

        with self.cond:
            start1.set()
            while self.results != ["start 1"]:
                self.cond.wait()
            start2.set()
            time.sleep(0.01)  # favor the race condition
            finish1.set()
            while self.results != ["start 1", "finish 1", "start 2"]:
                self.cond.wait()
            finish2.set()
            while self.results != ["start 1", "finish 1", "start 2", "finish 2"]:
                self.cond.wait()

        thd1.join()
        thd2.join()


@TestContext()
def test_is_browser(app):
    for is_browser, headers in [
        (True, [('Accept', 'text/html')]),
        (False, [('Accept', 'application/json')]),
        (False, []),
        (True, [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]),
        # It'd be simpler if these were True, but it doesn't really matter -- they're static
        (False, [('Accept', 'text/css,*/*;q=0.1')]),
        (False, [('Accept', 'image/png,image/*;q=0.8,*/*;q=0.5')]),
    ]:
        with app.test_request_context(headers=headers):
            eq_(util.is_browser(), is_browser,
                "%s should %sbe a browser" % (headers, '' if is_browser else 'not '))


NOW = datetime.datetime(2014, 6, 15, 7, 15, 29, 612709)

# datetime.datetime is a built-in type, so its attributes can't be mocked
# individually


@patch('datetime.datetime', spec=datetime.datetime)
def test_utcnow(datetime_mock):
    datetime_mock.utcnow.return_value = NOW
    util_dt = tz.utcnow()
    eq_(util_dt.tzinfo, pytz.UTC)
    eq_(util_dt.replace(tzinfo=None), NOW)


def test_utcfromtimestamp():
    timestamp = 1401240762.0  # UTC ver of datetime(2014, 5, 28, 1, 32, 42)
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    util_dt = tz.utcfromtimestamp(timestamp)
    eq_(util_dt.tzinfo, pytz.UTC)
    eq_(util_dt.replace(tzinfo=None), dt)


def test_dt_as_timezone_invalid_object():
    tests = [list(), dict(), "20140728", '2014-05-28T01:32:42']
    for obj in tests:
        with assert_raises(ValueError):
            tz.dt_as_timezone(obj, pytz.timezone("US/Pacific"))


def test_dt_as_timezone_aware():
    with assert_raises(ValueError):
        tz.dt_as_timezone(
            datetime.datetime.utcnow(), pytz.timezone("US/Pacific"))


def test_dt_as_timezone_conversions():
    dt = datetime.datetime(2014, 5, 23, 16, 39, 32, 125099, tzinfo=pytz.UTC)
    eq_(dt.strftime('%Y-%m-%d %H:%M:%S %Z%z'), '2014-05-23 16:39:32 UTC+0000')
    dt_converted = tz.dt_as_timezone(dt, pytz.timezone("US/Pacific"))
    eq_(dt_converted.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
        '2014-05-23 09:39:32 PDT-0700')
