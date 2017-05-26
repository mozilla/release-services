# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging

from flask import request, abort
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from backend_common.db import db
from shipit_taskcluster.models import TaskclusterStep, TaskclusterStatus
from shipit_taskcluster.taskcluster_utils import get_task_group_state, \
    TASK_TO_STEP_STATE

log = logging.getLogger(__name__)


# helpers
def query_state(step):
    log.info(step.task_group_id)
    tc_state = get_task_group_state(step.task_group_id)
    return TASK_TO_STEP_STATE[tc_state]


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
    pass  # TODO


def get_taskcluster_step(uid):
    log.info('getting step %s', uid)

    try:
        step = db.session.query(TaskclusterStep).filter(TaskclusterStep.uid == uid).one()
    except NoResultFound:
        abort(404, "taskcluster step not found")

    return dict(uid=step.uid, taskGroupId=step.task_group_id, parameters={})


def create_taskcluster_step(uid, body):
    """creates taskcluster step"""

    step = TaskclusterStep()

    step.uid = uid
    step.state = 'running'
    step.task_group_id = body["taskGroupId"]

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
