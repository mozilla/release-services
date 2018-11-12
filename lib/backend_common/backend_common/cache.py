# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import uuid

import flask
import flask_cache

import backend_common.dockerflow
import cli_common.log

logger = cli_common.log.get_logger(__name__)
cache = flask_cache.Cache()


def init_app(app):
    cache_config = app.config.get('CACHE', {'CACHE_TYPE': 'simple'})
    cache.init_app(app, config=cache_config)
    return cache


def app_heartbeat():
    cache_key = str(uuid.uuid4().get_hex().upper()[0:6])
    cache_value = str(uuid.uuid4().get_hex().upper()[0:6])
    try:
        cache = flask.current_app.cache
        assert cache.cache.get(cache_key) is None
        assert cache.cache.set(cache_key, cache_value) is True
        assert cache.cache.get(cache_key) == cache_value
        assert cache.cache.delete(cache_key) is True
        assert cache.cache.get(cache_key)
    except Exception as e:
        logger.exception(e)
        raise backend_common.dockerflow.HeartbeatException('Cannot get/set/delete items to the cache.')
