# -*- coding: utf-8 -*-
import asyncio

import pytest

from pulselistener.config import QUEUE_MONITORING
from pulselistener.config import QUEUE_PULSE_CODECOV
from pulselistener.lib.bus import MessageBus
from pulselistener.listener import HookCodeCoverage


@pytest.mark.asyncio
async def test_create_task(HooksMock, QueueMock, mock_taskcluster):
    bus = MessageBus()
    bus.add_queue(QUEUE_MONITORING, maxsize=1)
    bus.add_queue(QUEUE_PULSE_CODECOV)

    conf = {
        'hookGroupId': 'aGroup',
        'hookId': 'aHook',
    }
    hook = HookCodeCoverage(conf, bus)
    hook.hooks = HooksMock
    hook.queue = QueueMock

    # Add a dummy task in the target group
    QueueMock.add_task_in_group('aGroup', name='whatever', env={'key': 'value'})

    # Add a coverage task in the target group
    env = {
        'GECKO_HEAD_REPOSITORY': 'https://hg.mozilla.org/mozilla-central',
        'GECKO_HEAD_REV': 'deadbeef',
    }
    QueueMock.add_task_in_group('aGroup', name='build-linux64-ccov/test', env=env)

    # Send a pulse message with the target group
    pulse_payload = {
        'taskGroupId': 'aGroup',
    }
    await bus.send(QUEUE_PULSE_CODECOV, pulse_payload)

    # Run the code coverage event listener as a task
    task = asyncio.create_task(hook.run())

    # Stop as soon as a message is sent to monitoring
    group_id, hook_id, task_id = await bus.queues[QUEUE_MONITORING].get()
    task.cancel()
    assert bus.queues[QUEUE_MONITORING].qsize() == 0

    assert group_id == 'aGroup'
    assert hook_id == 'aHook'
    assert task_id == 'fake_task_id'

    assert HooksMock.obj['group_id'] == 'aGroup'
    assert HooksMock.obj['hook_id'] == 'aHook'
    assert HooksMock.obj['payload'] == {
        'REPOSITORY': 'https://hg.mozilla.org/mozilla-central',
        'REVISION': 'deadbeef',
    }
