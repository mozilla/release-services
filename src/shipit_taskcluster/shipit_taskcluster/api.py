# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging
from sqlalchemy.exc import IntegrityError

from shipit_taskcluster.models import TaskclusterStep
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
    pass  # TODO


def get_taskcluster_step_status(uid):
    pass  # TODO


def create_taskcluster_step(uid, body):
    """creates taskcluster step"""

    log.info('creating taskcluster step %s for task_group_id %s', uid, task_group_id)
    step = TaskclusterStep()

    step.uid = uid
    step.state = 'running'
    step.task_group_id = body.task_group_id

    db.session.add(step)

    try:
        db.session.commit()
    except IntegrityError as e:
        # TODO check for existence of step with same task_group_id
        return {
                   'error_title': 'Step with that uid already exists',
                   'error_message': str(e),
               }, 409  # Conflict

    return None


def delete_taskcluster_step(uid):
    pass  # TODO
