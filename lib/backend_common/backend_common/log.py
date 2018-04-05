# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logbook

import cli_common.log


def init_app(app):
    '''
    Init logger from a Flask Application
    '''
    level = logbook.INFO
    if app.debug:
        level = logbook.DEBUG

    cli_common.log.init_logger(
        app.name,
        level=level,
        channel=app.config.get('APP_CHANNEL'),
        PAPERTRAIL_HOST=app.config.get('PAPERTRAIL_HOST'),
        PAPERTRAIL_PORT=app.config.get('PAPERTRAIL_PORT'),
        SENTRY_DSN=app.config.get('SENTRY_DSN'),
        MOZDEF=app.config.get('MOZDEF'),
        flask_app=app,
    )
