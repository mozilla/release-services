# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import redis
from rq import Connection
from rq import Queue
from rq import SimpleWorker

from shipit_uplift import secrets

conn = redis.from_url(secrets.REDIS_URL)


def exc_handler(job, *exc_info):
    job.cleanup(ttl=3600)


if __name__ == '__main__':
    with Connection(conn):
        worker = SimpleWorker(map(Queue, ['default']), exception_handlers=[])
        worker.push_exc_handler(exc_handler)
        worker.push_exc_handler(worker.move_to_failed_queue)
        worker.work()
