# -*- coding: utf-8 -*-

import json

from cli_common.log import get_logger
from cli_common.pulse import create_consumer

logger = get_logger(__name__)


class PulseListener(object):
    '''
    Service listening to pulse messages and pushing them in a local queue
    '''
    QUEUE_OUT = 'pulse:out'

    def __init__(self, queue, route, user, password):

        # Pulse settings
        self.queue = queue
        self.route = route
        self.user = user
        self.password = password

        # Output queue
        self.bus = None

    def register(self, bus):
        '''
        Add an async outbound queue
        '''
        self.bus = bus
        self.bus.add_queue(PulseListener.QUEUE_OUT)

    async def start(self):
        consumer = await create_consumer(
            self.user,
            self.password,
            self.queue,
            self.route,
            self.got_message
        )
        logger.info('Listening for pulse messages', queue=self.queue, route=self.route)
        return consumer

    async def got_message(self, channel, body, envelope, properties):
        '''
        Generic Pulse consumer callback
        '''
        assert isinstance(body, bytes), \
            'Body is not in bytes'

        body = json.loads(body.decode('utf-8'))

        # Put message in message bus
        await self.bus.send(PulseListener.QUEUE_OUT, body)

        # Ack the message so it is removed from the broker's queue
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
