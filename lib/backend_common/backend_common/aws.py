# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import importlib
import json
import logging
import threading
import time
import cli_common.log
import boto
from boto.sqs import message as sqs_message

logger = cli_common.log.get_logger()


class _StopListening(Exception):
    pass


class AWS(object):

    def __init__(self, config):
        self.config = config
        self._connections = {}
        self._queues = {}
        self._listeners = []

    def connect_to(self, service_name, region_name):
        key = service_name, region_name
        if key in self._connections:
            return self._connections[key]

        # handle special cases
        try:
            fn = getattr(self, 'connect_to_' + service_name)
        except AttributeError:
            fn = self.connect_to_default
        conn = fn(service_name, region_name)
        self._connections[key] = conn
        return conn

    def connect_to_default(self, service_name, region_name):
        # for the service, import 'boto.$service'
        service = importlib.import_module('boto.' + service_name)

        for region in service.regions():
            if region.name == region_name:
                break
        else:
            raise RuntimeError('invalid region %r' % (region_name,))

        connect_fn = getattr(boto, 'connect_' + service_name)
        return connect_fn(
            aws_access_key_id=self.config.get('access_key_id'),
            aws_secret_access_key=self.config.get('secret_access_key'),
            region=region)

    def connect_to_s3(self, service_name, region_name):
        # special case for S3, which boto does differently than
        # the other services
        import boto.s3
        return boto.s3.connect_to_region(region_name=region_name,
                                         aws_access_key_id=self.config.get('access_key_id'),
                                         aws_secret_access_key=self.config.get('secret_access_key'))

    def get_sqs_queue(self, region_name, queue_name):
        key = (region_name, queue_name)
        if key in self._queues:
            return self._queues[key]

        sqs = self.connect_to('sqs', region_name)
        queue = sqs.get_queue(queue_name)
        if not queue:
            raise RuntimeError('no such queue {} in {}'.format(repr(queue_name), str(region_name)))
        self._queues[key] = queue
        return queue

    def sqs_write(self, region_name, queue_name, body):
        queue = self.get_sqs_queue(region_name, queue_name)
        m = sqs_message.Message(body=json.dumps(body))
        queue.write(m)

    def sqs_listen(self, region_name, queue_name, read_args=None):
        def decorate(func):
            self._listeners.append(
                (region_name, queue_name, read_args or {}, func))
            return func
        return decorate

    def _listen_thd(self, region_name, queue_name, read_args, listener):
        logger.info(
            'Listening to SQS queue %r in region %s', queue_name, region_name)
        try:
            queue = self.get_sqs_queue(region_name, queue_name)
        except Exception:
            logger.exception('While getting queue %r in region %s; listening cancelled',
                             queue_name, region_name)
            return

        while True:
            msg = queue.read(wait_time_seconds=20, **read_args)
            if msg:
                try:
                    listener(msg)
                except _StopListening:  # for tests
                    break
                except Exception:
                    logger.exception('while invoking %r', listener)
                    # note that we do nothing with the message; it will
                    # remain invisible for a while, then reappear and maybe
                    # cause another exception
                    continue
                msg.delete()

    def _spawn_sqs_listeners(self, _testing=False):
        # launch a listening thread for each SQS queue
        threads = []
        for region_name, queue_name, read_args, listener in self._listeners:
            thd = threading.Thread(
                name='%s/%r -> %r' % (region_name, queue_name, listener),
                target=self._listen_thd,
                args=(region_name, queue_name, read_args, listener))
            # set the thread to daemon so that SIGINT will kill the process
            thd.daemon = True
            thd.start()
            threads.append(thd)

        # sleep forever, or until we get a SIGINT, at which point the remaining
        # threads will be killed during process shutdown
        if not _testing:  # pragma: no cover
            while True:
                time.sleep(2 ** 31)

        return threads


def init_app(app):
    app.aws = AWS(app.config.get('AWS', {}))
    # disable boto debug logging unless DEBUG = True
    if not app.debug:
        logging.getLogger('boto').setLevel(logging.INFO)
