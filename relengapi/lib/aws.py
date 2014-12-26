# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import boto
import importlib
import json
import logging
import wsme.rest.json

from boto.sqs import message as sqs_message


class AWS(object):

    def __init__(self, config):
        self.config = config
        self._connections = {}
        self._queues = {}

    def connect_to(self, service_name, region_name):
        key = service_name, region_name
        if key in self._connections:
            return self._connections[key]

        # for the service, import 'boto.$service'
        service = importlib.import_module('boto.' + service_name)

        for region in service.regions():
            if region.name == region_name:
                break
        else:
            raise RuntimeError("invalid region %r" % (region_name,))

        connect_fn = getattr(boto, 'connect_' + service_name)
        conn = connect_fn(
            aws_access_key_id=self.config.get('access_key_id'),
            aws_secret_access_key=self.config.get('secret_access_key'),
            region=region)
        self._connections[key] = conn
        return conn

    def get_sqs_queue(self, region_name, queue_name):
        key = (region_name, queue_name)
        if key in self._queues:
            return self._queues[key]

        sqs = self.connect_to('sqs', region_name)
        queue = sqs.get_queue(queue_name)
        if not queue:
            raise RuntimeError("no such queue %r in %s" % (queue_name, region_name))
        self._queues[key] = queue
        return queue

    def sqs_write(self, region_name, queue_name, body):
        body = wsme.rest.json.tojson(type(body), body)
        queue = self.get_sqs_queue(region_name, queue_name)
        m = sqs_message.Message(body=json.dumps(body))
        queue.write(m)


def init_app(app):
    app.aws = AWS(app.config.get('AWS', {}))
    # disable boto debug logging unless DEBUG = True
    if not app.debug:
        logging.getLogger('boto').setLevel(logging.INFO)
