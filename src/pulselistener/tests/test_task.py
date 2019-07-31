# -*- coding: utf-8 -*-
import pytest

from pulselistener.config import QUEUE_MONITORING
from pulselistener.lib.bus import MessageBus
from pulselistener.lib.pulse import PulseListener
from pulselistener.listener import HookCodeCoverage


@pytest.mark.asyncio
async def test_create_task(HooksMock, QueueMock, mock_taskcluster):
    bus = MessageBus()
    bus.add_queue(QUEUE_MONITORING, maxsize=1)
    bus.add_queue(PulseListener.QUEUE_OUT)

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
    await bus.send(PulseListener.QUEUE_OUT, pulse_payload)

    # Run the code coverage event listener
    await hook.run()
    assert HooksMock.obj['group_id'] == 'aGroup'
    assert HooksMock.obj['hook_id'] == 'aHook'
    assert HooksMock.obj['payload'] == {
        'REPOSITORY': 'https://hg.mozilla.org/mozilla-central',
        'REVISION': 'deadbeef',
    }

    assert bus.queues[QUEUE_MONITORING].qsize() == 1
    group_id, hook_id, task_id = await bus.queues[QUEUE_MONITORING].get()
    assert group_id == 'aGroup'
    assert hook_id == 'aHook'
    assert task_id == 'fake_task_id'
