# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import cli_common.log
import flask_cors


logger = cli_common.log.get_logger(__name__)
cors = flask_cors.CORS()


def init_app(app):
    origins = app.config.get('CORS_ORIGINS', '*').split(' ')
    cors.init_app(app, origins=origins)
    return cors
