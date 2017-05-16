import logging

from taskcluster.queue import Queue

log = logging.getLogger(__name__)

TASK_TO_STEP_STATE = {
    "running": "running",
    "complete": "success"
    # etc
}

TC_QUEUE = Queue()

def get_task_group_state(taskGroupId):
    # TODO query taskcluster group api for overall state
    # return summary of remaining tasks and tasks that have failed while
    # exhausting retries

    # the python taskcluster package doesn't actuallly support the limit or
    # continuationToken query strings, so we can't get a subset or more than 1000
    # tasks
    d = TC_QUEUE.listTaskGroup(taskGroupId)
    log.info(d)
    return 'running'
