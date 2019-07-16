# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json

import flask


def get_version():
    version_json = {
        'source': 'https://github.com/mozilla-releng/services',
        'version': 'unknown',
        'commit': 'unknown',
        'build': 'unknown'
    }
    return flask.jsonify(version_json)


def lbheartbeat_response():
    '''Per the Dockerflow spec:
    Respond to /__lbheartbeat__ with an HTTP 200. This is for load balancer
    checks and should not check any dependent services.'''
    return flask.Response('OK!', headers={'Cache-Control': 'no-cache'})


def heartbeat_response():
    '''Per the Dockerflow spec:
    Respond to /__heartbeat__ with a HTTP 200 or 5xx on error. This should
    depend on services like the database to also ensure they are healthy.'''
    response = dict()

    # TODO: check redis is alive
    check = True

    if check is True:
        return flask.Response('OK', headers={'Cache-Control': 'public, max-age=60'})
    else:
        return flask.Response(status=502,
                              response=json.dumps(response),
                              headers={
                                  'Content-Type': 'application/json',
                                  'Cache-Control': 'public, max-age=60',
                              })
