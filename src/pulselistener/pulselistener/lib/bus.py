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
    def __init__(self, max_messages=None):
        self.queues = {}
        self.max_messages = max_messages
        self.nb_messages = 0

    def add_queue(self, name, mp=False):
        assert name not in self.queues, 'Queue {} already setup'.format(name)
        if mp:
            self.queues[name] = multiprocessing.Queue()
        else:
            self.queues[name] = asyncio.Queue()

    def is_alive(self):
        '''
        Helper for unit tests runtimes
        '''
        if self.max_messages is None:
            return True
        return self.nb_messages <= self.max_messages

    async def send(self, name, payload):
        assert name in self.queues, 'Missing queue {}'.format(name)
        queue = self.queues[name]
        if isinstance(queue, asyncio.Queue):
            await queue.put(payload)
        else:
            queue.put(payload)
            await asyncio.sleep(0)
        self.nb_messages += 1

    async def receive(self, name):
        assert name in self.queues, 'Missing queue {}'.format(name)
        queue = self.queues[name]
        if isinstance(queue, asyncio.Queue):
            return await queue.get()
        else:
            return queue.get()
            await asyncio.sleep(0)
        self.nb_messages += 1

    async def run(self, input_name, output_name, method):
        '''
        Pass messages from input to output
        Optionally applies some conversions methods
        '''
        assert input_name in self.queues, 'Missing queue {}'.format(input_name)
        assert output_name in self.queues, 'Missing queue {}'.format(output_name)

        while self.is_alive():

            message = await self.receive(input_name)

            # Run async or sync methods
            if inspect.iscoroutinefunction(method):
                new_message = await method(message)
            else:
                new_message = method(message)

            if not new_message:
                logger.info('Skipping new message conversion, no result', message=message)
                continue

            await self.send(output_name, new_message)

            # Notify the queue that the message has been processed
            # await self.queues[input_name].task_done()
