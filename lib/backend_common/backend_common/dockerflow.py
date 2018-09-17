# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''
Provide API endpoint for Dockerflow
https://github.com/mozilla-services/Dockerflow
'''

import importlib
import json

import flask

import backend_common
import backend_common.dockerflow
import cli_common.log

logger = cli_common.log.get_logger(__name__)


class HeartbeatException(Exception):
    '''Error messages that are being collected from each extension which
       implements app_heartbeat.
    '''

    def __init__(self, message, *arg, **kw):
        super().__init__(*arg, **kw)
        self.message = message


def get_version():
    version_json = {
        'source': 'https://github.com/mozilla-releng/services',
        'version': 'unknown',
        'commit': 'unknown',
        'build': 'unknown'
    }
    try:
        version_json_path = '/app/version.json'
        with open(version_json_path) as f:
            version_json = json.load(f)
    except Exception:
        pass

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
    extensions = flask.current_app.__extensions

    for extension_name in extensions:
        if extension_name not in backend_common.EXTENSIONS:
            continue

        extension_heartbeat = None
        try:
            app_heartbeat = getattr(importlib.import_module('backend_common.' + extension_name), 'app_heartbeat')
            logger.info('Testing heartbeat of {} extension'.format(extension_name))
            app_heartbeat()
        except AttributeError:
            logger.debug(f'Ignoring not implemented heartbeat of {extension_name} extension')
        except HeartbeatException as e:
            extension_heartbeat = e.message

        if extension_heartbeat is None:
            continue

        response[extension_name] = extension_heartbeat

    if len(response) == 0:
        return flask.Response('OK', headers={'Cache-Control': 'public, max-age=60'})
    else:
        return flask.Response(status=502,
                              response=json.dumps(response),
                              headers={
                                  'Content-Type': 'application/json',
                                  'Cache-Control': 'public, max-age=60',
                              })
