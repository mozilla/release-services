# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import pickle

from flask import abort, request
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from cli_common import log
from backend_common.auth0 import auth0
from backend_common.db import db

from shipit_signoff.db_services import get_step_by_uid, insert_new_signature
from shipit_signoff.models import SignoffStep, SigningStatus
from shipit_signoff.policies import check_whether_policy_can_be_signed, is_sign_off_policy_met, \
    UnauthorizedUserError, NoSignoffLeftError


logger = log.get_logger(__name__)

# provided by https://auth.mozilla.auth0.com/.well-known/openid-configuration
AUTH0_FIELDS = [
    "openid", "profile", "offline_access", "name", "given_name", "family_name",
    "nickname", "email", "email_verified", "picture", "created_at",
    "identities", "phone", "address",
]

STEPS = {}
SIGNOFFS = {}


@auth0.require_login
def login(callback_url):
    """Log a user in, using auth0

    Returns the user to callback_url when finished.
    """
    pass


def signoffstep_to_status(step):
    """
    Given a Signoff Step, extract and return only the data needed for its
    current status
    """
    status = dict(
        uid=step.uid,
        state=step.state.value,  # it's an enum
        message="{}".format(step.status_message),
        created=str(step.created),
    )

    if step.completed:
        status['completed'] = str(step.completed)

    return status


def list_steps():
    """
    List all the known steps with a given status, or running ones if not
    specified.
    """
    logger.info('listing steps')

    desired_state = request.args.get('state', 'running')

    try:
        steps = db.session.query(SignoffStep)\
            .filter(SignoffStep.state == SigningStatus[desired_state])\
            .all()
    except NoResultFound:
        return list()

    logger.info("list_steps(): {}".format(steps))
    return [signoffstep_to_status(step) for step in steps]


def get_step(uid):
    """
    Get a sign-off step definition
    """
    logger.info('getting step %s', uid)

    try:
        step = db.session.query(SignoffStep).filter(
            SignoffStep.uid == uid).one()
    except NoResultFound:
        abort(404)

    return dict(uid=uid, policy=step.policy_data, parameters={})


def get_step_status(uid):
    """
    Get the current status of a sign-off step, including who has signed
    """
    logger.info('getting step status %s', uid)

    try:
        step = db.session.query(SignoffStep).filter(
            SignoffStep.uid == uid).one()
    except NoResultFound:
        abort(404)

    return signoffstep_to_status(step)


def create_step(uid):
    """
    Create a sign-off step
    """
    logger.info('creating step %s', uid)

    step = SignoffStep()

    step.uid = uid
    step.state = 'running'
    step.policy = pickle.dumps(request.json['policy'])

    db.session.add(step)

    try:
        db.session.commit()
    except IntegrityError as e:
        return {
            'error_title': 'Step with that uid already exists',
            'error_message': str(e),
        }, 409  # Conflict

    return {}


def delete_step(uid):
    logger.info('deleting step %s', uid)
    try:
        step = SignoffStep.query.filter_by(uid=uid).one()
    except:
        logger.error("Missing step when deleting: %s", uid)
        abort(404)

    step.delete()
    return {}


def is_user_in_group(group):
    """
    Dummy function while auth0 wrappers are not in place.
    """
    return True

    if auth0.user_loggedin:
        group_membership = auth0.user_getinfo(['groups']).get('groups')
        return group in group_membership
    return False


def get_logged_in_email():
    """
    TODO: move to backend_common.auth0
    TODO: write equivalent functions for groups, email_verified. Or get a user
          dict?
    """
    return 'sfraser@mozilla.com'

    if auth0.user_loggedin:
        return auth0.user_getinfo(['email']).get('email')
    return None


def sign_off(uid):
    logger.info('Signing off step %s', uid)
    logger.info('Fetching step %s', uid)

    try:
        step = get_step_by_uid(uid)
    except NoResultFound:
        abort(404)

    claim_group = request.json['group']

    # TODO: is the claim_group in the policy for step uid?

    if not is_user_in_group(claim_group):
        abort(403)

    existing_signatures = step.signatures
    email = get_logged_in_email()
    # TODO Process the definition only if "local" is set
    policy_definition = step.policy_data['definition']

    try:
        check_whether_policy_can_be_signed(email, claim_group, policy_definition, existing_signatures)
    except UnauthorizedUserError as e:
        abort(403, str(e))
    except NoSignoffLeftError as e:
        abort(409, str(e))

    insert_new_signature(step, email, claim_group)
    all_signatures = step.signatures

    if is_sign_off_policy_met(policy_definition, all_signatures):
        # TODO: Do something more useful
        print('Step fully signed off!')

    return {}


def delete_signature(uid):
    """
    TODO: implement
    """
    logger.info("Removing signature from step %s", uid)
    if uid not in STEPS:
        return None, 404
    SIGNOFFS[uid] = False
    STEPS[uid] = 'running'
    return None
