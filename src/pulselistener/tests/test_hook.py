# -*- coding: utf-8 -*-
import pytest

from pulselistener.hook import Hook
from pulselistener.monitoring import task_monitoring


@pytest.mark.asyncio
async def test_create_task_no_hooks_service(HooksMock):
    hook = Hook('aGroup', 'aHook')

    with pytest.raises(Exception):
        await hook.create_task()


@pytest.mark.asyncio
async def test_create_task(HooksMock):
    hook = Hook('aGroup', 'aHook')

    hook.hooks = HooksMock

    task_id = await hook.create_task()
    assert task_id == 'fake_task_id'
    assert HooksMock.obj['group_id'] == 'aGroup'
    assert HooksMock.obj['hook_id'] == 'aHook'
    assert HooksMock.obj['payload'] == {}

    assert task_monitoring.tasks.qsize() == 1
    group_id, hook_id, task_id = await task_monitoring.tasks.get()
    assert group_id == 'aGroup'
    assert hook_id == 'aHook'
    assert task_id == 'fake_task_id'


@pytest.mark.asyncio
async def test_create_task_extra_env(HooksMock):
    hook = Hook('aGroup', 'aHook')

    hook.hooks = HooksMock

    task_id = await hook.create_task({'test': 'succeeded'})
    assert task_id == 'fake_task_id'
    assert HooksMock.obj['group_id'] == 'aGroup'
    assert HooksMock.obj['hook_id'] == 'aHook'
    assert HooksMock.obj['payload'] == {'test': 'succeeded'}

    assert task_monitoring.tasks.qsize() == 1
    group_id, hook_id, task_id = await task_monitoring.tasks.get()
    assert group_id == 'aGroup'
    assert hook_id == 'aHook'
    assert task_id == 'fake_task_id'
