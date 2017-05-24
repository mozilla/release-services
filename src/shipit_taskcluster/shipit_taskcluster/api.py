# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging

from sqlalchemy.orm.exc import NoResultFound
from flask import request
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
def list_taskcluster_steps():
    log.info('listing steps')

    try:
        desired_state = TaskclusterStatus[request.args.get('state', 'running')]
    except KeyError:
        log.warning("valid states: %s", [state.value for state in TaskclusterStatus])
        log.exception("%s is not a valid state", request.args["state"])
        return []

    try:
        steps = db.session.query(TaskclusterStep).filter(TaskclusterStep.state == desired_state).all()
    except NoResultFound:
        return []

    log.info("listing steps: {}", steps)
    return [step.uid for step in steps]


def get_taskcluster_step_status(uid):
    pass  # TODO


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
    pass  # TODO
