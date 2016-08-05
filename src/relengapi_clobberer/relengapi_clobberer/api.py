# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from flask import g, current_app
from relengapi_clobberer import models


def get_buildbot():
    return models.buildbot_branches(g.db.session)


def post_buildbot(body):
    result = []

    try:
        for clobber in body:
            result.append(
                models.clobber_buildbot(
                    g.db.session,
                    branch=clobber['branch'],
                    builddir=clobber['builddir'],
                    slave=clobber['slave']
                )
            )
        g.db.session.commit()

    except Exception as e:
        g.db.session.rollback()
        return dict(error=str(e.message))

    return result


def get_taskcluster():
    caches_to_skip = current_app.config.get('TASKCLUSTER_CACHES_TO_SKIP', [])
    return models.taskcluster_branches(caches_to_skip)


def post_taskcluster():
    # TODO: need to make this route work
    credentials = []

    # XXX: it should get authenticated via Authenticated header
    client_id = current_app.config.get('TASKCLUSTER_CLIENT_ID')
    access_token = current_app.config.get('TASKCLUSTER_ACCESS_TOKEN')

    if client_id and access_token:
        credentials = [dict(
            credentials=dict(
                clientId=client_id,
                accessToken=access_token,
            ))]

    purge_cache = taskcluster.PurgeCache(*credentials)

    for item in body:
        purge_cache.purgeCache(item.provisionerId,
                               item.workerType,
                               dict(cacheName=item.cacheName))

    return None
