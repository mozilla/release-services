# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import flask
import os
import werkzeug.exceptions
import typing

import backend_common
import backend_common.api
import tooltool_api.aws
import tooltool_api.cli
import tooltool_api.config
import tooltool_api.models  # noqa


def custom_handle_default_exceptions(e: Exception) -> typing.Tuple[int, str]:
    '''Conform structure of errors as before, to make it work with client (tooltool.py).
    '''
    error = backend_common.api.handle_default_exceptions_raw(e)
    error['name'] = error['title']
    error['description'] = error['detail']
    import flask  # for some reason flask needs to be imported here
    return flask.jsonify(dict(error=error)), error['status']


def create_app(config: dict=None) -> flask.Flask:
    app = backend_common.create_app(
        project_name=tooltool_api.config.PROJECT_NAME,
        app_name=tooltool_api.config.APP_NAME,
        config=config,
        extensions=[
            'log',
            'security',
            'cors',
            'api',
            'auth',
            'db',
            'pulse',
        ],
    )
    app.api.register(os.path.join(os.path.dirname(__file__), 'api.yml'))
    app.aws = tooltool_api.aws.AWS(app.config['S3_REGIONS_ACCESS_KEY_ID'],
                                   app.config['S3_REGIONS_SECRET_ACCESS_KEY'])

    for code, exception in werkzeug.exceptions.default_exceptions.items():
        app.register_error_handler(exception, custom_handle_default_exceptions)

    @app.cli.command()
    def worker():
        tooltool_api.cli.cmd_worker(app)

    @app.cli.command()
    def replicate():
        tooltool_api.cli.cmd_replicate(app)

    @app.cli.command()
    def check_pending_uploads():
        tooltool_api.cli.cmd_check_pending_uploads(app)

    return app
