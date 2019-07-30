# -*- coding: utf-8 -*-
import pytest

from pulselistener.hook import Hook
from pulselistener.lib.bus import MessageBus
from pulselistener.lib.monitoring import Monitoring


@pytest.mark.asyncio
async def test_create_task_no_hooks_service(HooksMock):
    bus = MessageBus()
    hook = Hook('aGroup', 'aHook', bus)

    with pytest.raises(Exception):
        await hook.create_task()


@pytest.mark.asyncio
async def test_create_task(HooksMock):
    bus = MessageBus()
    bus.add_queue(Monitoring.QUEUE_IN)
    hook = Hook('aGroup', 'aHook', bus)

    hook.hooks = HooksMock

    task_id = await hook.create_task()
    assert task_id == 'fake_task_id'
    assert HooksMock.obj['group_id'] == 'aGroup'
    assert HooksMock.obj['hook_id'] == 'aHook'
    assert HooksMock.obj['payload'] == {}

    assert bus.queues['monitoring:in'].qsize() == 1
    group_id, hook_id, task_id = await bus.queues['monitoring:in'].get()
    assert group_id == 'aGroup'
    assert hook_id == 'aHook'
    assert task_id == 'fake_task_id'


@pytest.mark.asyncio
async def test_create_task_extra_env(HooksMock):
    bus = MessageBus()
    bus.add_queue(Monitoring.QUEUE_IN)
    hook = Hook('aGroup', 'aHook', bus)

    hook.hooks = HooksMock

    task_id = await hook.create_task({'test': 'succeeded'})
    assert task_id == 'fake_task_id'
    assert HooksMock.obj['group_id'] == 'aGroup'
    assert HooksMock.obj['hook_id'] == 'aHook'
    assert HooksMock.obj['payload'] == {'test': 'succeeded'}

    assert bus.queues['monitoring:in'].qsize() == 1
    group_id, hook_id, task_id = await bus.queues['monitoring:in'].get()
    assert group_id == 'aGroup'
    assert hook_id == 'aHook'
    assert task_id == 'fake_task_id'
