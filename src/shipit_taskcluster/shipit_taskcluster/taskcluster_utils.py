# -*- coding: utf-8 -*-
import logging

import taskcluster

log = logging.getLogger(__name__)

TC_QUEUE = taskcluster.Queue()
TC_SCHEDULER = taskcluster.Scheduler()


TASK_GRAPH_STATE_TO_STEP_STATE = {
    "running": "running",
    "blocked": "failed",
    "finished": "completed"
}


def get_taskcluster_tasks_state(task_group_id, scheduler_api=False):
    # TODO rather than poll taskcluster queue and scheduler for state
    # we should use pulse and listen in for status changes
    if scheduler_api:
        return get_scheduler_graph_state(task_graph_id=task_group_id)
    return get_queue_group_state(task_group_id)


def get_scheduler_graph_state(task_graph_id):
    """poll the scheduler for overall status.
    this request is relatively cheap.
    :returns state where state is of: running, blocked or finished"""
    try:
        return TASK_GRAPH_STATE_TO_STEP_STATE[TC_SCHEDULER.status(task_graph_id)["status"]["state"]]
    except Exception:
        state = "exception"
        log.exception("Could not determine status from taskcluster scheduler with graph id: %s",
                      task_graph_id)
        return state


def get_queue_group_state(task_group_id):
    # TODO
    # the python taskcluster package doesn't actually support the limit or
    # continuationToken query strings, so we can't get a subset or more than 1000
    # tasks
    # group = TC_QUEUE.listTaskGroup(taskGroupId)
    pass
