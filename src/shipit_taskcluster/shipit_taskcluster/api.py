# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime

from flask import abort
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import cli_common.log
from backend_common.db import db
from shipit_taskcluster.models import TaskclusterStatus
from shipit_taskcluster.models import TaskclusterStep
from shipit_taskcluster.taskcluster_utils import get_taskcluster_tasks_state

log = cli_common.log.get_logger(__name__)


# api
def list_taskcluster_steps(state='running'):
    log.info('listing steps')

    try:
        desired_state = TaskclusterStatus[state]
    except KeyError:
        exception = '{} is not a valid state'.format(state)
        log.warning('valid states: %s', [state.value for state in TaskclusterStatus])
        log.exception(exception)
        abort(400, exception)

    try:
        steps = db.session.query(TaskclusterStep).filter(TaskclusterStep.state == desired_state).all()
    except NoResultFound:
        abort(404, 'No Taskcluster steps found with that given state.')

    log.info('listing steps: {}', steps)
    return [step.uid for step in steps]


def get_taskcluster_step_status(uid):
    '''
    Get the current status of a taskcluster step
    '''
    log.info('getting step status %s', uid)

    try:
        step = db.session.query(TaskclusterStep).filter(TaskclusterStep.uid == uid).one()
    except NoResultFound:
        abort(404)

    if not step.state.value == 'completed':
        # only poll taskcluster if the step is not resolved successfully
        # this is so the shipit taskcluster step can still be manually overridden as complete

        task_group_state = get_taskcluster_tasks_state(step.task_group_id, step.scheduler_api)

        if step.state.value != task_group_state:
            # update step status!
            if task_group_state in ['completed', 'failed', 'exception']:
                step.finished = datetime.datetime.utcnow()
            step.state = task_group_state
            db.session.commit()

    return dict(uid=step.uid, task_group_id=step.task_group_id, state=step.state.value,
                finished=step.finished or '', created=step.created)


def get_taskcluster_step(uid):
    log.info('getting step %s', uid)

    try:
        step = db.session.query(TaskclusterStep).filter(TaskclusterStep.uid == uid).one()
    except NoResultFound:
        abort(404, 'taskcluster step not found')

    return dict(uid=step.uid, taskGroupId=step.task_group_id,
                schedulerAPI=step.scheduler_api, parameters={})


def create_taskcluster_step(uid, body):
    '''creates taskcluster step'''

    step = TaskclusterStep()

    step.uid = uid
    step.state = 'running'
    step.task_group_id = body['taskGroupId']
    step.scheduler_api = body['schedulerAPI']

    log.info('creating taskcluster step %s for task_group_id %s', step.uid, step.task_group_id)
    db.session.add(step)

    try:
        db.session.commit()
    except IntegrityError as e:
        # TODO is there a better way to do this?
        if 'shipit_taskcluster_steps_pkey' in str(e):
            title = 'Step with that uid already exists'
        elif 'shipit_taskcluster_steps_task_group_id_key' in str(e):
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
        exception = 'Taskcluster step could not be found by given uid: {}'.format(uid)
        log.exception(exception)
        abort(404, exception)

    db.session.delete(step)
    db.session.commit()

    return {}
