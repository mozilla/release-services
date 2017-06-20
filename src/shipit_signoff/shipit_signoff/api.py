# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import pickle

from flask import abort, request, g
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from cli_common import log
from backend_common.auth0 import auth0, mozilla_accept_token
from backend_common.db import db

from shipit_signoff.db_services import get_step_by_uid, insert_new_signature, delete_existing_signature
from shipit_signoff.models import SignoffStep, SigningStatus
from shipit_signoff.policies import (
    check_whether_policy_can_be_signed,
    check_whether_policy_can_be_unsigned,
    is_sign_off_policy_met,
    UnauthorizedUserError, NoSignoffLeftError, NoSignaturePresentError,
    NoChangingCompletedPolicyError)


logger = log.get_logger(__name__)

# provided by https://auth.mozilla.auth0.com/.well-known/openid-configuration
AUTH0_FIELDS = [
    'openid', 'profile', 'offline_access', 'name', 'given_name', 'family_name',
    'nickname', 'email', 'email_verified', 'picture', 'created_at',
    'identities', 'phone', 'address',
]


@auth0.require_login
def login(callback_url):
    '''Log a user in, using auth0

    Returns the user to callback_url when finished.
    '''
    pass


def signoffstep_to_status(step):
    '''
    Given a Signoff Step, extract and return only the data needed for its
    current status
    '''
    status = dict(
        uid=step.uid,
        state=step.state.value,  # it's an enum
        message='{}'.format(step.status_message),
        created=str(step.created),
    )

    if step.completed:
        status['completed'] = str(step.completed)

    return status


@mozilla_accept_token()
def list_steps():
    '''
    List all the known steps with a given status, or running ones if not
    specified.
    '''
    logger.info('Listing steps')

    desired_state = request.args.get('state', 'running')

    try:
        steps = db.session.query(SignoffStep)\
            .filter(SignoffStep.state == SigningStatus[desired_state])\
            .all()
    except NoResultFound:
        return list()

    return [signoffstep_to_status(step) for step in steps]


@mozilla_accept_token()
def get_step(uid):
    '''
    Get a sign-off step definition
    '''
    logger.info('Getting step %s', uid)

    try:
        step = db.session.query(SignoffStep).filter(
            SignoffStep.uid == uid).one()
    except NoResultFound:
        abort(404)

    return dict(uid=uid, policy=step.policy_data, parameters={})


@mozilla_accept_token()
def get_step_status(uid):
    '''
    Get the current status of a sign-off step, including who has signed
    '''
    logger.info('Getting step status %s', uid)

    try:
        step = db.session.query(SignoffStep).filter(
            SignoffStep.uid == uid).one()
    except NoResultFound:
        logger.error('Step %s not found', uid)
        abort(404)

    return signoffstep_to_status(step)


@mozilla_accept_token()
def create_step(uid):
    '''
    Create a sign-off step
    '''
    logger.info('Creating step %s', uid)

    step = SignoffStep()

    step.uid = uid
    step.state = 'running'
    step.policy = pickle.dumps(request.json['policy'])

    db.session.add(step)

    try:
        db.session.commit()
    except IntegrityError as e:
        logger.error('Attempt to create duplicate step %s', uid)
        return {
            'error_title': 'Step with that uid already exists',
            'error_message': str(e),
        }, 409  # Conflict

    logger.info('Created step %s, policy %s', uid, request.json['policy'])
    return {}


@mozilla_accept_token()
def delete_step(uid):
    logger.info('Deleting step %s', uid)
    try:
        step = SignoffStep.query.filter_by(uid=uid).one()
    except:
        logger.error('Missing step when deleting: %s', uid)
        abort(404)

    step.delete()
    return {}


def is_user_in_group(group):
    '''Check a user's group membership using auth0
    '''
    group_membership = auth0.user_getinfo(
        ['groups'], access_token=g.access_token).get('groups')
    return group in group_membership


def get_logged_in_email():
    '''Get a user's verified email address using auth0
    '''
    return auth0.user_getinfo(['email'], access_token=g.access_token).get('email')


@mozilla_accept_token()
def sign_off(uid):
    logger.info('Signing off step %s', uid)

    try:
        step = get_step_by_uid(uid)
    except NoResultFound:
        abort(404)

    claim_group = request.json['group']

    if not is_user_in_group(claim_group):
        abort(403)

    existing_signatures = step.signatures
    email = get_logged_in_email()

    policy_definition = step.policy_data['definition']

    if step.policy_data['method'] == 'balrog':
        abort(400, 'Balrog method not yet implemented')
    if step.policy_data['method'] != 'local':
        logger.error('Step %s has unknown policy method: %s',
                     uid, step.policy_data['method'])
        abort(400, 'Policy method not known')

    try:
        check_whether_policy_can_be_signed(email, claim_group, policy_definition, existing_signatures)
    except UnauthorizedUserError as e:
        logger.error('User %s (%s) not allowed to sign step %s', email, claim_group, uid)
        abort(403, str(e))
    except NoSignoffLeftError as e:
        logger.error('Step %s already fully signed-off (user %s attempting)', uid, email)
        abort(409, str(e))

    insert_new_signature(step, email, claim_group)
    all_signatures = step.signatures

    if is_sign_off_policy_met(policy_definition, all_signatures):
        step.state == SigningStatus.completed
        db.session.commit()
        logger.info('Step %s fully signed off!', uid)

    return {}


@mozilla_accept_token()
def delete_signature(uid):
    '''Delete a signature from a signoff step.
    '''
    logger.info('Removing signature from step %s', uid)
    try:
        step = get_step_by_uid(uid)
    except NoResultFound:
        logger.error('No such step found %s', uid)
        abort(404)
    email = get_logged_in_email()
    claim_group = request.json['group']
    if not is_user_in_group(claim_group):
        logger.error(
            'User %s is not in the group %s when deleting signature %s', email, claim_group, uid)
        abort(403)
    existing_signatures = step.signatures
    if not existing_signatures:
        logger.error(
            'No signatures on step %s when trying to remove %s', uid, email)
        abort(409)
    if step.policy_data['method'] != 'local':
        logger.error('Unknown policy method for step %s: %s',
                     uid, step.policy_data['method'])
        abort(400, 'Unknown policy method')
    policy_definition = step.policy_data['definition']
    try:
        check_whether_policy_can_be_unsigned(
            email, claim_group, policy_definition, existing_signatures)
    except UnauthorizedUserError as e:
        logger.error(
            'User %s not permitted to remove signature from step %s', email, uid)
        abort(403, str(e))
    except NoSignaturePresentError as e:
        logger.error(
            'User %s attempting to remove missing signature from step %s', email, uid)
        abort(409, str(e))
    except NoChangingCompletedPolicyError as e:
        logger.error(
            'User %s unable to modify completed policy in step %s', email, uid)
        abort(409, str(e))
    delete_existing_signature(step, email, claim_group)
    if not is_sign_off_policy_met(policy_definition, step.signatures):
        step.state == SigningStatus.running
        db.session.commit()
        logger.info('Step %s state changed to running.', uid)
    return {}
