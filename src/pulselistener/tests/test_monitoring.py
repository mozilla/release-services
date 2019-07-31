# -*- coding: utf-8 -*-
import pytest

from pulselistener.lib.bus import MessageBus
from pulselistener.lib.monitoring import Monitoring


@pytest.mark.asyncio
async def test_monitoring(QueueMock, NotifyMock, mock_taskcluster):
    bus = MessageBus()
    monitoring = Monitoring('testqueue', ['pinco@pallino'], 1)
    monitoring.register(bus)
    await bus.send('testqueue', ('Group1', 'Hook1', 'Task-invalid'))
    await bus.send('testqueue', ('Group1', 'Hook1', 'Task-pending'))
    await bus.send('testqueue', ('Group1', 'Hook1', 'Task1-completed'))
    await bus.send('testqueue', ('Group1', 'Hook1', 'Task2-completed'))
    await bus.send('testqueue', ('Group1', 'Hook2', 'Task-exception'))
    await bus.send('testqueue', ('Group2', 'Hook1', 'Task-failed'))
    assert bus.queues['testqueue'].qsize() == 6

    monitoring.queue = QueueMock
    monitoring.notify = NotifyMock

    # No report sent, since we haven't collected any stats yet.
    monitoring.send_report()
    assert NotifyMock.email_obj == {}

    # Queue throws exception, remove task from queue.
    await monitoring.check_task()
    assert bus.queues['testqueue'].qsize() == 5

    # Task is pending, put it back in the queue.
    await monitoring.check_task()
    assert bus.queues['testqueue'].qsize() == 5

    # No report sent, since we haven't collected any stats yet.
    monitoring.send_report()
    assert NotifyMock.email_obj == {}

    # Task is completed.
    await monitoring.check_task()
    assert monitoring.stats['Hook1']['completed'] == ['Task1-completed']
    assert bus.queues['testqueue'].qsize() == 4

    # Another task is completed.
    await monitoring.check_task()
    assert monitoring.stats['Hook1']['completed'] == ['Task1-completed', 'Task2-completed']
    assert bus.queues['testqueue'].qsize() == 3

    # Task exception.
    assert len(monitoring.queue.created_tasks) == 0
    await monitoring.check_task()
    assert monitoring.stats['Hook1']['exception'] == []
    assert monitoring.stats['Hook2']['exception'] == ['Task-exception']

    # A new task has been retried, replacing the exception
    assert len(monitoring.queue.created_tasks) == 1
    assert bus.queues['testqueue'].qsize() == 3

    # Task failed.
    await monitoring.check_task()
    assert monitoring.stats['Hook1']['failed'] == ['Task-failed']
    assert bus.queues['testqueue'].qsize() == 2

    # Task is pending, put it back in the queue.
    await monitoring.check_task()
    assert bus.queues['testqueue'].qsize() == 2

    content = '''# Hook1 tasks for the last period


## completed

66.67% of all tasks (2/3)

* [Task1-completed](https://tools.taskcluster.net/task-inspector/#Task1-completed)
* [Task2-completed](https://tools.taskcluster.net/task-inspector/#Task2-completed)

## exception

0.00% of all tasks (0/3)



## failed

33.33% of all tasks (1/3)

* [Task-failed](https://tools.taskcluster.net/task-inspector/#Task-failed)

# Hook2 tasks for the last period


## completed

0.00% of all tasks (0/1)



## exception

100.00% of all tasks (1/1)

* [Task-exception](https://tools.taskcluster.net/task-inspector/#Task-exception)

## failed

0.00% of all tasks (0/1)

'''

    monitoring.send_report()
    assert NotifyMock.email_obj['address'] == 'pinco@pallino'
    assert NotifyMock.email_obj['subject'] == 'Pulse listener tasks'
    assert NotifyMock.email_obj['content'] == content
    assert NotifyMock.email_obj['template'] == 'fullscreen'
    assert monitoring.stats == {}


@pytest.mark.asyncio
async def test_report_all_completed(QueueMock, NotifyMock, mock_taskcluster):
    bus = MessageBus()
    monitoring = Monitoring('testqueue', ['pinco@pallino'], 1)
    monitoring.register(bus)
    await bus.send('testqueue', ('Group1', 'Hook1', 'Task1-completed'))
    await bus.send('testqueue', ('Group1', 'Hook1', 'Task2-completed'))
    assert bus.queues['testqueue'].qsize() == 2

    monitoring.queue = QueueMock
    monitoring.notify = NotifyMock

    await monitoring.check_task()
    await monitoring.check_task()

    # No email sent, since all tasks were successful.
    monitoring.send_report()
    assert NotifyMock.email_obj == {}
    assert monitoring.stats == {}


@pytest.mark.asyncio
async def test_monitoring_whiteline_between_failed_and_hook(QueueMock, NotifyMock, mock_taskcluster):
    bus = MessageBus()
    monitoring = Monitoring('testqueue', ['pinco@pallino'], 1)
    monitoring.register(bus)
    await bus.send('testqueue', ('Group1', 'Hook1', 'Task-failed'))
    await bus.send('testqueue', ('Group1', 'Hook2', 'Task-failed'))
    assert bus.queues['testqueue'].qsize() == 2

    monitoring.queue = QueueMock
    monitoring.notify = NotifyMock

    # Task exception.
    await monitoring.check_task()
    assert monitoring.stats['Hook1']['failed'] == ['Task-failed']
    assert bus.queues['testqueue'].qsize() == 1

    # Task failed.
    await monitoring.check_task()
    assert monitoring.stats['Hook2']['failed'] == ['Task-failed']
    assert bus.queues['testqueue'].qsize() == 0

    content = '''# Hook1 tasks for the last period


## completed

0.00% of all tasks (0/1)



## exception

0.00% of all tasks (0/1)



## failed

100.00% of all tasks (1/1)

* [Task-failed](https://tools.taskcluster.net/task-inspector/#Task-failed)

# Hook2 tasks for the last period


## completed

0.00% of all tasks (0/1)



## exception

0.00% of all tasks (0/1)



## failed

100.00% of all tasks (1/1)

* [Task-failed](https://tools.taskcluster.net/task-inspector/#Task-failed)'''

    monitoring.send_report()
    assert NotifyMock.email_obj['address'] == 'pinco@pallino'
    assert NotifyMock.email_obj['subject'] == 'Pulse listener tasks'
    assert NotifyMock.email_obj['content'] == content
    assert NotifyMock.email_obj['template'] == 'fullscreen'
    assert monitoring.stats == {}


@pytest.mark.asyncio
async def test_monitoring_retry_exceptions(QueueMock, NotifyMock, mock_taskcluster):
    bus = MessageBus()
    monitoring = Monitoring('testqueue', ['pinco@pallino'], 1)
    monitoring.register(bus)
    await bus.send('testqueue', ('Group1', 'Hook1', 'Task-exception-retry:2'))
    await bus.send('testqueue', ('Group1', 'Hook2', 'Task-exception-retry:0'))
    assert bus.queues['testqueue'].qsize() == 2

    monitoring.queue = QueueMock
    assert len(monitoring.queue.created_tasks) == 0
    monitoring.notify = NotifyMock

    # Task exception with 2 retries
    await monitoring.check_task()
    assert monitoring.stats['Hook1']['exception'] == ['Task-exception-retry:2']
    assert len(monitoring.queue.created_tasks) == 1
    assert bus.queues['testqueue'].qsize() == 2

    # The retried task should maintain the original taskGroupId
    old_task = monitoring.queue.task('Task-exception-retry:2')
    new_task_id, new_task = monitoring.queue.created_tasks[0]
    assert new_task_id != 'Task-exception-retry:2'
    assert new_task != old_task
    assert new_task['taskGroupId'] == old_task['taskGroupId']
    assert new_task['payload'] == old_task['payload']
    assert new_task['created'] != old_task['created']

    # Task exception with 0 retries
    # No new task should be created
    await monitoring.check_task()
    assert monitoring.stats['Hook2']['exception'] == ['Task-exception-retry:0']
    assert len(monitoring.queue.created_tasks) == 1
    assert bus.queues['testqueue'].qsize() == 1


@pytest.mark.asyncio
async def test_monitoring_restartable(QueueMock, IndexMock, mock_taskcluster):
    bus = MessageBus()
    monitoring = Monitoring('testqueue', ['pinco@pallino'], 1)
    monitoring.register(bus)

    monitoring.index = IndexMock
    monitoring.queue = QueueMock

    # Check a failed task is restartable
    # when the monitoring flag is set
    assert monitoring.is_restartable('Task-failed-restart')

    # Check a failed task is not restartable
    # when the monitoring flag is not set
    assert not monitoring.is_restartable('Task-failed-nope')

    # Check a completed task is not restartable
    assert not monitoring.is_restartable('Task-completed-restart')
    assert not monitoring.is_restartable('Task-completed-nope')

    # Check a failed task is restarted by the monitoring flow
    assert len(monitoring.queue.created_tasks) == 0
    await bus.send('testqueue', ('Group', 'Hook-staticanalysis/bot', 'Task-failed-restart'))
    await monitoring.check_task()
    assert len(monitoring.queue.created_tasks) == 1
