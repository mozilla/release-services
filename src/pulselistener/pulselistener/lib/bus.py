# -*- coding: utf-8 -*-
import asyncio
import inspect
import multiprocessing

from cli_common.log import get_logger

logger = get_logger(__name__)


class MessageBus(object):
    '''
    Communication bus between processes
    '''
    def __init__(self):
        self.queues = {}

    def add_queue(self, name, mp=False, maxsize=-1):
        '''
        Create a new queue on the message bus
        * asyncio by default
        * multiprocessing when mp=True
        By default, there are no size limit enforced (maxsize=-1)
        '''
        assert name not in self.queues, 'Queue {} already setup'.format(name)
        assert isinstance(maxsize, int)
        if mp:
            self.queues[name] = multiprocessing.Queue(maxsize=maxsize)
        else:
            self.queues[name] = asyncio.Queue(maxsize=maxsize)

    async def send(self, name, payload):
        '''
        Send a message on a specific queue
        '''
        assert name in self.queues, 'Missing queue {}'.format(name)
        queue = self.queues[name]
        if isinstance(queue, asyncio.Queue):
            await queue.put(payload)
        else:
            # Run the synchronous mp queue.put in the asynchronous loop
            await asyncio.get_running_loop().run_in_executor(None, lambda: queue.put(payload))

    async def receive(self, name):
        '''
        Wait for a message on a specific queue
        This is a blocking operation
        '''
        assert name in self.queues, 'Missing queue {}'.format(name)
        queue = self.queues[name]
        if isinstance(queue, asyncio.Queue):
            return await queue.get()
        else:
            # Run the synchronous mp queue.get in the asynchronous loop
            return await asyncio.get_running_loop().run_in_executor(None, queue.get)

    async def run(self, input_name, output_name, method):
        '''
        Pass messages from input to output
        Optionally applies some conversions methods
        This is also the "ideal" usage between 2 queues
        '''
        assert input_name in self.queues, 'Missing queue {}'.format(input_name)
        assert output_name in self.queues, 'Missing queue {}'.format(output_name)

        while not self.queues[output_name].full():

            message = await self.receive(input_name)

            # Run async or sync methods
            if inspect.iscoroutinefunction(method):
                new_message = await method(message)
            else:
                new_message = method(message)

            if not new_message:
                logger.info('Skipping new message creation: no result', message=message)
                continue

            await self.send(output_name, new_message)
