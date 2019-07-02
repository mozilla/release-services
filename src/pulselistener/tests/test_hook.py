# -*- coding: utf-8 -*-
import pytest

from pulselistener.lib.bus import MessageBus
from pulselistener.lib.taskcluster import TaskclusterHook


@pytest.mark.asyncio
async def test_create_task(HooksMock):
    bus = MessageBus(max_messages=1)
    hook = TaskclusterHook('aGroup', 'aHook', 'user', 'token')
    hook.register(bus)
    assert bus.nb_messages == 0

    hook.hooks = HooksMock

    await bus.send('hook:in', {})
    assert bus.nb_messages == 1

    await hook.create_tasks()
    assert bus.nb_messages == 2

    output = await bus.receive('hook:out')
    assert output == {
        'group_id': 'aGroup',
        'hook_id': 'aHook',
        'task_id': 'fake_task_id',
    }
    assert HooksMock.obj['group_id'] == 'aGroup'
    assert HooksMock.obj['hook_id'] == 'aHook'
    assert HooksMock.obj['payload'] == {}


@pytest.mark.asyncio
async def test_create_task_extra_env(HooksMock):
    bus = MessageBus(max_messages=1)
    hook = TaskclusterHook('aGroup', 'aHook', 'user', 'token')
    hook.register(bus)
    assert bus.nb_messages == 0

    hook.hooks = HooksMock

    await bus.send('hook:in', {'test': 'succeeded'})
    assert bus.nb_messages == 1

    await hook.create_tasks()
    assert bus.nb_messages == 2

    output = await bus.receive('hook:out')
    assert output == {
        'group_id': 'aGroup',
        'hook_id': 'aHook',
        'task_id': 'fake_task_id',
    }
    assert HooksMock.obj['group_id'] == 'aGroup'
    assert HooksMock.obj['hook_id'] == 'aHook'
    assert HooksMock.obj['payload'] == {'test': 'succeeded'}
