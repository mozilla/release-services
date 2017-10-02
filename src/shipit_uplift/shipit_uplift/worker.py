# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import redis
from rq import Worker, Queue, Connection

import cli_common.taskcluster
import shipit_uplift.config


secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    shipit_uplift.config.PROJECT_NAME,
    required=[],
    existing={x: os.environ.get(x) for x in ['REDIS_URL'] if x in os.environ},
    taskcluster_client_id=os.environ.get('TASKCLUSTER_CLIENT_ID'),
    taskcluster_access_token=os.environ.get('TASKCLUSTER_ACCESS_TOKEN'),
)

REDIS_URL = secrets['REDIS_URL'] if 'REDIS_URL' in secrets else 'redis://localhost:6379'

conn = redis.from_url(REDIS_URL)


def exc_handler(job, *exc_info):
    job.cleanup(ttl=3600)


if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, ['default']), exception_handlers=[])
        worker.push_exc_handler(exc_handler)
        worker.push_exc_handler(worker.move_to_failed_queue)
        worker.work()
