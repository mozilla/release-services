# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging

from flask import request, abort
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from backend_common.db import db
from shipit_taskcluster.models import TaskclusterStatus, TaskclusterStep

log = logging.getLogger(__name__)


# api
def list_taskcluster_steps(state="running"):
    log.info('listing steps')

    try:
        desired_state = TaskclusterStatus[state]
    except KeyError:
        exception = "{} is not a valid state".format(state)
        log.warning("valid states: %s", [state.value for state in TaskclusterStatus])
        log.exception(exception)
        abort(400, exception)

    try:
        steps = db.session.query(TaskclusterStep).filter(TaskclusterStep.state == desired_state).all()
    except NoResultFound:
        abort(404, "No Taskcluster steps found with that given state.")

    log.info("listing steps: {}", steps)
    return [step.uid for step in steps]


def get_taskcluster_step_status(uid):
    """
    Get the current status of a taskcluster step
    """
    log.info('getting step status %s', uid)

    try:
        step = db.session.query(SignoffStep).filter(SignoffStep.uid == uid).one()
    except NoResultFound:
        abort(404)

    task_group_status, task_group_status_message = get_task_group_state(step.task_group_id)

    if not step.status != task_group_status:
        # update step status!
        if task_group_status in ["completed", "failed", "exception"]:
            step.completed = datetime.datetime.utcnow
        step.status = task_group_status
        step.task_message = task_group_status_message
        db.session.commit()

    return dict(uid=step.uid, status=step.task_group_id, message=step.status_message,
                finished=step.finished, created=step.created)


def get_taskcluster_step(uid):
    log.info('getting step %s', uid)

    try:
        step = db.session.query(TaskclusterStep).filter(TaskclusterStep.uid == uid).one()
    except NoResultFound:
        abort(404, "taskcluster step not found")

    return dict(uid=step.uid, taskGroupId=step.task_group_id,
                schedulerAPI=step.scheduler_api, parameters={})


def create_taskcluster_step(uid, body):
    """creates taskcluster step"""

    step = TaskclusterStep()

    step.uid = uid
    step.state = 'running'
    step.task_group_id = body["taskGroupId"]
    step.scheduler_api = body["schedulerAPI"]

    log.info('creating taskcluster step %s for task_group_id %s', step.uid, step.task_group_id)
    db.session.add(step)

    try:
        db.session.commit()
    except IntegrityError as e:
        # TODO is there a better way to do this?
        if "shipit_taskcluster_steps_pkey" in str(e):
            title = 'Step with that uid already exists'
        elif "shipit_taskcluster_steps_task_group_id_key" in str(e):
            title = 'Step with that task_group_id already exists'
        else:
            title = 'Integrity Error'
        return {'error_title': title, 'error_message': str(e)}, 409

    return None


def delete_taskcluster_step(uid):
    log.info('deleting step %s', uid)

    try:
        step = TaskclusterStep.query.filter_by(uid=uid).one()
    except Exception as e:
        exception = "Taskcluster step could not be found by given uid: {}".format(uid)
        log.exception(exception)
        abort(404, exception)

    db.session.delete(step)
    db.session.commit()

    return {}
