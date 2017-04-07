# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging

log = logging.getLogger(__name__)

STEPS = {}
SIGNOFFS = {}


def login(callback_url):
    """Log a user in, using auth0

    Returns the user to callback_url when finished.
    """
    pass

def list_steps():
    log.info('listing steps')
    return list(STEPS.keys())


def get_step(uid):
    log.info('getting step %s', uid)
    if uid not in STEPS:
        return None, 404
    return dict(uid=uid, input={}, parameters={})


def get_step_status(uid):
    log.info('getting step status %s', uid)
    return dict(
        state=STEPS[uid]
    )


def create_step(uid):
    log.info('creating step %s', uid)
    STEPS[uid] = 'running'
    SIGNOFFS[uid] = False
    return None


def delete_step(uid):
    log.info('deleting step %s', uid)
    del STEPS[uid]
    del SIGNOFFS[uid]
    return None


def sign_off(uid):
    log.info('Signing off step %s', uid)
    if uid not in STEPS:
        return None, 404
    SIGNOFFS[uid] = True
    STEPS[uid] = 'completed'
    return None

def delete_signature(uid):
    log.info("Removing signature from step %s", uid)
    if uid not in STEPS:
        return None, 404
    SIGNOFFS[uid] = False
    STEPS[uid] = 'running'
    return None

