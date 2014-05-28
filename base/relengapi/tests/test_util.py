# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import threading
import datetime
import pytz
from mock import patch
from nose.tools import eq_, with_setup, assert_raises
from relengapi import util
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

_cachedUTCNow = None


class _MockUtcnow(datetime.datetime):
    _datetime = datetime.datetime

    @classmethod
    def utcnow(cls):
        global _cachedUTCNow
        if not _cachedUTCNow:
            _cachedUTCNow = _MockUtcnow._datetime.utcnow()
        return _cachedUTCNow


def _clear_cachedUTCNow():
    global _cachedUTCNow
    _cachedUTCNow = None


@patch('datetime.datetime', _MockUtcnow)
@with_setup(teardown=_clear_cachedUTCNow)
def test_mock_utcnow():
    dt1 = datetime.datetime.utcnow()
    time.sleep(1)
    dt2 = datetime.datetime.utcnow()
    eq_(dt1, dt2)


@patch('datetime.datetime', _MockUtcnow)
@with_setup(teardown=_clear_cachedUTCNow)
def test_utcnow():
    dt = datetime.datetime.utcnow()
    util_dt = tz.utcnow()
    eq_(util_dt.tzinfo, pytz.UTC)
    eq_(util_dt.replace(tzinfo=None), dt)


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
            dt = tz.dt_as_timezone(obj, pytz.timezone("US/Pacific"))


def test_dt_as_timezone_aware():
    with assert_raises(ValueError):
        dt = tz.dt_as_timezone(datetime.datetime.utcnow(), pytz.timezone("US/Pacific"))


def test_dt_as_timezone_conversions():
    dt = datetime.datetime(2014, 5, 23, 16, 39, 32, 125099, tzinfo=pytz.UTC)
    eq_(dt.strftime('%Y-%m-%d %H:%M:%S %Z%z'), '2014-05-23 16:39:32 UTC+0000')
    dt_converted = tz.dt_as_timezone(dt, pytz.timezone("US/Pacific"))
    eq_(dt_converted.strftime('%Y-%m-%d %H:%M:%S %Z%z'), '2014-05-23 09:39:32 PDT-0700')
