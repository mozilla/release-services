# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import kombu


class PulseNotifier(object):
    def __init__(self, host, port, user, password,
                 virtual_host='/', ssl=True, connect_timeout=5):
        self.pulse_connection = kombu.Connection(
            hostname=host,
            port=port,
            userid=user,
            password=password,
            virtual_host=virtual_host,
            ssl=ssl,
            connect_timeout=connect_timeout)

    def publish(self, exchange, routing_key, payload):
        with self.pulse_connection as connection:
            if not connection.connected:
                connection.connect()

            ex = kombu.Exchange(exchange, type='topic')
            producer = connection.Producer(exchange=ex,
                                           routing_key=routing_key,
                                           serializer='json')
            message = {
                'payload': payload,
                '_meta': {
                    'exchange': exchange,
                    'routing_key': routing_key,
                    'serializer': 'json',
                    'sent': datetime.datetime.utcnow().isoformat()}}

            producer.publish(message)
            connection.close()
