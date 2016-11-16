# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

STEPS = {}
SIGNOFFS = {}


def list_steps():
    return list(STEPS.keys())


def get_step(uid):
    if uid not in STEPS:
        return None, 404
    return dict(uid=uid, input={}, parameters={})


def get_step_status(uid):
    return dict(
        state=STEPS[uid]
    )


def create_step(uid):
    STEPS[uid] = 'running'
    SIGNOFFS[uid] = False
    return None


def delete_step(uid):
    del STEPS[uid]
    del SIGNOFFS[uid]
    return None


def signoff(uid):
    SIGNOFFS[uid] = True
    STEPS[uid] = 'completed'
    return None
