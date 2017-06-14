# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import flask_talisman
import flask_talisman.talisman


# TODO: we need to remove unsafe-inline
DEFAULT_CSP_POLICY = {
    'default-src': '\'none\'',
    'script-src': '\'self\' \'unsafe-inline\'',
    'style-src': '\'self\' \'unsafe-inline\'',
    'img-src': '\'self\'',
    'connect-src': '\'self\'',
}


DEFAULT_CONFIG = dict(
    force_https=True,
    force_https_permanent=False,
    force_file_save=False,
    frame_options=flask_talisman.talisman.SAMEORIGIN,
    frame_options_allow_from=None,
    strict_transport_security=True,
    strict_transport_security_preload=False,
    strict_transport_security_max_age=flask_talisman.talisman.ONE_YEAR_IN_SECS,
    strict_transport_security_include_subdomains=True,
    content_security_policy=DEFAULT_CSP_POLICY,
    content_security_policy_report_uri=None,
    content_security_policy_report_only=False,
    session_cookie_secure=True,
    session_cookie_http_only=True,
)

security = flask_talisman.Talisman()


def init_app(app):
    config = app.config.get('SECURITY', DEFAULT_CONFIG)
    security.init_app(app, **config)
    return security
