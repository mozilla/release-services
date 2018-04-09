# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import defaultdict

import requests
from flask import current_app as app

from shipit_signoff.models import SigningStatus


def get_current_user_roles():
    user_info = requests.get(
        '{}/users/current'.format(app.config['BALROG_API_ROOT']),
        auth=(app.config['BALROG_USERNAME'], app.config['BALROG_PASSWORD']),
    )
    return user_info.get('roles', {}).keys()


def make_signoffs_uri(policy_definition):
    return '{}/scheduled_changes/{}/{}/signoffs'.format(
        app.config['BALROG_API_ROOT'],
        policy_definition['object'],
        policy_definition['sc_id'],
    )


def get_signoff_status(policy_definition):
    # TODO: switch this to a GET to /scheduled_changes/{object}/{sc_id} when that endpoint exists
    scheduled_changes = requests.get(
        '{}/scheduled_changes/{}?all=1'.format(app.config['BALROG_API_ROOT'],
                                               policy_definition['object'])
    ).json().get('scheduled_changes', {})
    for sc in scheduled_changes:
        if sc['sc_id'] == policy_definition['sc_id']:
            return sc['signoffs'], sc['required_signoffs']

    return None, None


def all_signoffs_are_done(required_signoffs, signoffs):
    obtained_signoffs = defaultdict(int)
    for user, role in signoffs.items():
        obtained_signoffs[role] += 1
    for role, number in required_signoffs.items():
        if required_signoffs.get(role, 0) > obtained_signoffs[role]:
            return False
    return True


def get_balrog_signoff_state(policy_definition):
    signoffs, required_signoffs = get_signoff_status(policy_definition)
    if all_signoffs_are_done(required_signoffs, signoffs):
        return SigningStatus.completed
    return SigningStatus.running
