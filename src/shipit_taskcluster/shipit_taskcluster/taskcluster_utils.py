# -*- coding: utf-8 -*-
import logging
from collections import Counter

import taskcluster

log = logging.getLogger(__name__)

TC_QUEUE = taskcluster.Queue()
TC_SCHEDULER = taskcluster.Scheduler()


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


def listTaskGroup_all(task_group_id):
    '''Use the continuation token to get an entire task group_name
    We currently have task graphs ranging up to ~2500 entries, so
    this should be relatively safe for now. May need to revisit it
    once task graphs grow.
    '''
    taskgroup = TC_QUEUE.listTaskGroup(task_group_id)

    continuationToken = taskgroup.get('continuationToken')
    while continuationToken:
        result = TC_QUEUE.listTaskGroup(task_group_id, continuationToken=continuationToken)
        taskgroup['tasks'].extend(result.get('tasks', list()))
        continuationToken = result.get('continuationToken')

    return taskgroup

def get_queue_group_state(task_group_id):
    '''Use taskcluster.queue to get the task group data'''
    taskgroup = listTaskGroup_all(task_group_id)

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
