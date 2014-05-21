# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import threading
from relengapi import util


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
