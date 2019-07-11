# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

import connexion
import flask
import flask_cors
import flask_talisman
import flask_talisman.talisman
import structlog
import werkzeug

from .dockerflow import get_version
from .dockerflow import heartbeat_response
from .dockerflow import lbheartbeat_response

logger = structlog.get_logger(__name__)


TALISMAN_CONFIG = dict(
    # on heroku force https redirect
    force_https='DYNO' in os.environ,
    force_https_permanent=False,
    force_file_save=False,
    frame_options=flask_talisman.talisman.SAMEORIGIN,
    frame_options_allow_from=None,
    strict_transport_security=True,
    strict_transport_security_preload=False,
    strict_transport_security_max_age=flask_talisman.talisman.ONE_YEAR_IN_SECS,
    strict_transport_security_include_subdomains=True,
    content_security_policy={
        'default-src': '\'none\'',
        # unsafe-inline is needed for the Swagger UI
        'script-src': '\'self\' \'unsafe-inline\'',
        'style-src': '\'self\' \'unsafe-inline\'',
        'img-src': '\'self\'',
        'connect-src': '\'self\'',
    },
    content_security_policy_report_uri=None,
    content_security_policy_report_only=False,
    session_cookie_secure=True,
    session_cookie_http_only=True,
)


def handle_default_exceptions(e):
    error = {
        'type': 'about:blank',
        'title': str(e),
        'status': getattr(e, 'code', 500),
        'detail': getattr(e, 'description', str(e)),
        'instance': 'about:blank',
    }
    return flask.jsonify(error), error['status']


def build_flask_app(project_name, app_name, openapi):
    '''
    Create a new Flask backend application
    app_name is the Python application name, used as Flask import_name
    project_name is a "nice" name, used to identify the application
    '''
    assert os.path.exists(openapi), 'Missing openapi file {}'.format(openapi)
    logger.debug('Initializing', app=app_name, openapi=openapi)

    # Start OpenAPI app
    app = connexion.App(import_name=app_name)
    app.name = project_name
    app.add_api(openapi)

    # Enable security
    security = flask_talisman.Talisman()
    security.init_app(app.app, **TALISMAN_CONFIG)

    # Enable wildcard CORS
    cors = flask_cors.CORS()
    cors.init_app(app.app, origins=['*'])

    # Add exception Json renderer
    for code, exception in werkzeug.exceptions.default_exceptions.items():
        app.app.register_error_handler(exception, handle_default_exceptions)

    # Redirect root to API
    app.add_url_rule('/', 'root', lambda: flask.redirect(app.options.openapi_console_ui_path))

    # Dockerflow checks
    app.add_url_rule('/__heartbeat__', view_func=heartbeat_response)
    app.add_url_rule('/__lbheartbeat__', view_func=lbheartbeat_response)
    app.add_url_rule('/__version__', view_func=get_version)

    logger.debug('Initialized', app=app.name)
    return app
