# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging

log = logging.getLogger(__name__)

PIPELINES = {}


def list_pipelines():
    log.info('listing pipelines')
    return list(PIPELINES.keys())


def get_pipeline(uid):
    log.info('getting pipeline %s', uid)
    if uid not in PIPELINES:
        return None, 404
    return dict(uid=uid, input={}, parameters={})


def get_pipeline_status(uid):
    log.info('getting pipeline status %s', uid)
    return dict(
        state=PIPELINES[uid]
    )


def create_pipeline(uid):
    log.info('creating pipeline %s', uid)
    PIPELINES[uid] = 'running'
    return None


def delete_pipeline(uid):
    log.info('deleting pipeline %s', uid)
    del PIPELINES[uid]
    return None


def ticktock():
    log.info('refreshing pipelines')
    return None
