# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging

log = logging.getLogger(__name__)

STEPS = {}


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
    return None


def delete_step(uid):
    log.info('deleting step %s', uid)
    del STEPS[uid]
    return None


def ticktock():
    log.info('refreshing pipelines')
    return None
