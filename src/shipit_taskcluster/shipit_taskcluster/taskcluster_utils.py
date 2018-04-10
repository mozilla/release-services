# -*- coding: utf-8 -*-
from collections import Counter

import taskcluster

import cli_common.log

log = cli_common.log.get_logger(__name__)

TC_QUEUE = taskcluster.Queue()
# TODO: new version of taskcluster does not have taskcluster.Scheduler
# TC_SCHEDULER = taskcluster.Scheduler()
TC_SCHEDULER = None


TASK_GRAPH_STATE_TO_STEP_STATE = {
    'running': 'running',
    'blocked': 'failed',
    'finished': 'completed'
}


def get_taskcluster_tasks_state(task_group_id, scheduler_api=False):
    # TODO rather than poll taskcluster queue and scheduler for state
    # we should use pulse and listen in for status changes
    if scheduler_api:
        return get_scheduler_graph_state(task_graph_id=task_group_id)
    return get_queue_group_state(task_group_id)


def get_scheduler_graph_state(task_graph_id):
    '''poll the scheduler for overall status.
    this request is relatively cheap.
    :returns state where state is of: running, blocked or finished'''
    try:
        return TASK_GRAPH_STATE_TO_STEP_STATE[TC_SCHEDULER.status(task_graph_id)['status']['state']]
    except Exception:
        state = 'exception'
        log.exception('Could not determine status from taskcluster scheduler with graph id: %s',
                      task_graph_id)
        return state


def get_queue_group_state(task_group_id):
    # TODO
    # the python taskcluster package doesn't actually support the limit or
    # continuationToken query strings, so we can't get a subset or more than
    # 1000 tasks

    taskgroup = TC_QUEUE.listTaskGroup(task_group_id)

    try:
        states = Counter(task['status']['state'] for task in taskgroup['tasks'])
    except KeyError:
        log.error('Could not parse task states from task graph')
        return 'exception'

    # Example:
    # Counter({'completed': 689, 'unscheduled': 161, 'pending': 41, 'running': 19})
    if states['exception'] > 0 or states['failed'] > 0:
        # failed, exception > 0
        return 'failed'
    elif list(states.keys()) == ['completed']:
        # Only 'completed' states
        return 'completed'
    else:
        # unscheduled, running, pending > 0
        return 'running'
