# -*- coding: utf-8 -*-
import asyncio
import multiprocessing

import pytest

from pulselistener.lib.bus import MessageBus


def test_queue_creation():
    '''
    Test queues creation with different types
    '''
    bus = MessageBus()
    assert len(bus.queues) == 0

    bus.add_queue('test')
    assert len(bus.queues) == 1

    with pytest.raises(AssertionError) as e:
        bus.add_queue('test')
    assert str(e.value) == 'Queue test already setup'
    assert len(bus.queues) == 1

    bus.add_queue('another')
    assert len(bus.queues) == 2

    bus.add_queue('different', mp=True)
    assert len(bus.queues) == 3

    assert isinstance(bus.queues['test'], asyncio.Queue)
    assert isinstance(bus.queues['another'], asyncio.Queue)
    assert isinstance(bus.queues['different'], multiprocessing.queues.Queue)


@pytest.mark.asyncio
async def test_message_passing_async():
    '''
    Test sending & receiving messages on an async queue
    '''
    bus = MessageBus()
    bus.add_queue('test')
    assert isinstance(bus.queues['test'], asyncio.Queue)

    await bus.send('test', {'payload': 1234})
    await bus.send('test', {'another': 'deadbeef'})
    await bus.send('test', 'covfefe')
    assert bus.queues['test'].qsize() == 3

    msg = await bus.receive('test')
    assert msg == {'payload': 1234}
    msg = await bus.receive('test')
    assert msg == {'another': 'deadbeef'}
    msg = await bus.receive('test')
    assert msg == 'covfefe'
    assert bus.queues['test'].qsize() == 0


@pytest.mark.asyncio
async def test_message_passing_mp():
    '''
    Test sending & receiving messages on a multiprocessing queueu
    '''
    bus = MessageBus()
    bus.add_queue('test', mp=True)
    assert isinstance(bus.queues['test'], multiprocessing.queues.Queue)

    await bus.send('test', {'payload': 1234})
    await bus.send('test', {'another': 'deadbeef'})
    await bus.send('test', 'covfefe')
    assert bus.queues['test'].qsize() == 3

    msg = await bus.receive('test')
    assert msg == {'payload': 1234}
    msg = await bus.receive('test')
    assert msg == {'another': 'deadbeef'}
    msg = await bus.receive('test')
    assert msg == 'covfefe'
    assert bus.queues['test'].qsize() == 0


@pytest.mark.asyncio
async def test_conversion():
    '''
    Test message conversion between 2 queues
    '''
    bus = MessageBus()
    bus.add_queue('input')
    bus.add_queue('output', maxsize=3)  # limit size to immediately stop execution for unit test
    assert isinstance(bus.queues['input'], asyncio.Queue)
    assert isinstance(bus.queues['output'], asyncio.Queue)
    assert bus.queues['input'].qsize() == 0
    assert bus.queues['output'].qsize() == 0

    await bus.send('input', 'test x')
    await bus.send('input', 'hello world.')
    await bus.send('output', 'lowercase')

    # Convert all strings from input in uppercase
    assert bus.queues['input'].qsize() == 2
    await bus.run('input', 'output', lambda x: x.upper())
    assert bus.queues['input'].qsize() == 0

    await bus.receive('output') == 'lowercase'
    await bus.receive('output') == 'TEST X'
    await bus.receive('output') == 'HELLO WORLD.'


@pytest.mark.asyncio
async def test_maxsize():
    '''
    Test a queue maxsize behaves as expected
    Maxsize=-1 is enabled by default
    '''
    bus = MessageBus()
    bus.add_queue('async')
    bus.add_queue('mp', mp=True)
    assert bus.queues['async'].maxsize == -1
    # No maxsize getter on mp queues

    assert bus.queues['async'].empty()
    assert bus.queues['mp'].empty()

    for i in range(1000):
        await bus.send('async', i)
        await bus.send('mp', i)

    assert not bus.queues['async'].full()
    assert not bus.queues['mp'].full()
