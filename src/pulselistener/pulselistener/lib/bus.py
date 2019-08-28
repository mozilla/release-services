# -*- coding: utf-8 -*-
import asyncio
import collections
import inspect
import multiprocessing
import os
import pickle
from queue import Empty

import aioredis

from cli_common.log import get_logger

logger = get_logger(__name__)

RedisQueue = collections.namedtuple('RedisQueue', 'name')


class AsyncRedis(object):
    '''
    Async context manager to create a redis connection
    '''
    async def __aenter__(self):
        self.conn = await aioredis.create_redis(os.environ['REDIS_URL'])
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        self.conn.close()
        await self.conn.wait_closed()


class MessageBus(object):
    '''
    Communication bus between processes
    '''
    def __init__(self):
        self.queues = {}
        self.redis_enabled = 'REDIS_URL' in os.environ
        logger.info('Redis support', enabled=self.redis_enabled and 'yes' or 'no')

    def add_queue(self, name, mp=False, redis=False, maxsize=-1):
        '''
        Create a new queue on the message bus
        * asyncio by default
        * multiprocessing when mp=True
        By default, there are no size limit enforced (maxsize=-1)
        '''
        assert name not in self.queues, 'Queue {} already setup'.format(name)
        assert isinstance(maxsize, int)
        if self.redis_enabled and redis:
            self.queues[name] = RedisQueue(f'pulselistener:{name}')
        elif mp:
            self.queues[name] = multiprocessing.Queue(maxsize=maxsize)
        else:
            self.queues[name] = asyncio.Queue(maxsize=maxsize)

    async def send(self, name, payload):
        '''
        Send a message on a specific queue
        '''
        assert name in self.queues, 'Missing queue {}'.format(name)
        queue = self.queues[name]

        if isinstance(queue, RedisQueue):
            async with AsyncRedis() as redis:
                nb = await redis.rpush(queue.name, pickle.dumps(payload))
                logger.info('Put new item in redis queue', queue=queue, nb=nb)

        elif isinstance(queue, asyncio.Queue):
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

        if isinstance(queue, RedisQueue):
            async with AsyncRedis() as redis:
                _, payload = await redis.blpop(queue.name)
                assert isinstance(payload, bytes)
                logger.info('Read item from redis queue', queue=queue)
                return pickle.loads(payload)

        elif isinstance(queue, asyncio.Queue):
            return await queue.get()

        else:
            # Run the synchronous mp queue.get in the asynchronous loop
            # but use an asyncio sleep to be able to react to cancellation
            async def _get():
                while True:
                    try:
                        return queue.get(timeout=0)
                    except Empty:
                        await asyncio.sleep(1)

            return await _get()

    async def run(self, method, input_name, output_name=None):
        '''
        Pass messages from input to output
        Optionally applies some conversions methods
        This is also the "ideal" usage between 2 queues
        '''
        assert input_name in self.queues, 'Missing queue {}'.format(input_name)
        assert output_name is None or output_name in self.queues, 'Missing queue {}'.format(output_name)

        while True:
            message = await self.receive(input_name)

            # Run async or sync methods
            if inspect.iscoroutinefunction(method):
                new_message = await method(message)
            else:
                new_message = method(message)

            if not new_message:
                logger.info('Skipping new message creation: no result', message=message)
                continue

            if output_name is not None:
                await self.send(output_name, new_message)
