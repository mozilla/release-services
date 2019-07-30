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

    assert not bus.is_full()

    await bus.send('test', {'payload': 1234})
    await bus.send('test', {'another': 'deadbeef'})
    await bus.send('test', 'covfefe')
    assert bus.nb_messages == 3

    assert not bus.is_full()
    msg = await bus.receive('test')
    assert msg == {'payload': 1234}
    msg = await bus.receive('test')
    assert msg == {'another': 'deadbeef'}
    msg = await bus.receive('test')
    assert msg == 'covfefe'


@pytest.mark.asyncio
async def test_message_passing_mp():
    '''
    Test sending & receiving messages on a multiprocessing queueu
    '''
    bus = MessageBus()
    bus.add_queue('test', mp=True)
    assert isinstance(bus.queues['test'], multiprocessing.queues.Queue)

    assert not bus.is_full()

    await bus.send('test', {'payload': 1234})
    await bus.send('test', {'another': 'deadbeef'})
    await bus.send('test', 'covfefe')
    assert bus.nb_messages == 3

    assert not bus.is_full()
    msg = await bus.receive('test')
    assert msg == {'payload': 1234}
    msg = await bus.receive('test')
    assert msg == {'another': 'deadbeef'}
    msg = await bus.receive('test')
    assert msg == 'covfefe'


@pytest.mark.asyncio
async def test_conversion():
    '''
    Test message conversion between 2 queues
    '''
    bus = MessageBus(max_messages=4)
    bus.add_queue('input')
    bus.add_queue('output')
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
