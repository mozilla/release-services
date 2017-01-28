# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import flask
import jinja2
import structlog
import os
import sys

__APP = dict()
__BASE_EXTENSIONS = []

logger = structlog.get_logger()

try:
    from releng_common import log
    __BASE_EXTENSIONS.append(log)
except:
    pass

try:
    from releng_common import security
    __BASE_EXTENSIONS.append(security)
except:
    pass

try:
    from releng_common import api
    __BASE_EXTENSIONS.append(api)
except:
    pass

if 'CORS_ORIGINS' in os.environ:
    try:
        from releng_common import cors
        __BASE_EXTENSIONS.append(cors)
    except:
        pass


def create_app(name, extensions=[], config=None, debug=False, debug_src=None,
               redirect_root_to_api=True, **kw):
    global __APP
    if __APP and name in __APP:
        return __APP[name]

    logger.debug('Initializing', app=name)

    app = __APP[name] = flask.Flask(name, **kw)
    app.debug = debug

    # Support test mode
    if os.environ.get('APP_TESTING') == name:
        config = {
            'DEBUG': True,
            'TESTING': True,
            'DATABASE_URL': 'sqlite://',  # in memory db
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        }

    # load config (settings.py)
    if config:
        app.config.update(**config)
    elif os.environ.get('APP_SETTINGS'):  # noqa
        app.config.from_envvar('APP_SETTINGS')
    else:
        print("Using default settings; to configure releng, set "
              "APP_SETTINGS to point to your settings file")
        sys.exit(1)

    app.jinja_loader = jinja2.loaders.FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates'))

    for extension in __BASE_EXTENSIONS + extensions:

        if type(extension) is tuple:
            extension_name, extension_init = extension
        elif not hasattr(extension, 'init_app'):
            extension_name = None
            extension_init = extension
        else:
            extension_name = extension.__name__.split('.')[-1]
            extension_init = extension.init_app

        logger.debug('Initializing',
                     extension=extension_name or str(extension_init),
                     app=name)

        _app = extension_init(app)
        if _app and extension_name is not None:
            setattr(app, extension_name, _app)

        logger.debug('Configured',
                     extension=extension_name or str(extension_init),
                     app=name)

    if redirect_root_to_api:
        app.add_url_rule("/",
                         "root",
                         lambda: flask.redirect(app.api.swagger_url))

    def run_options():
        extra_files = []
        if debug_src:
            for base, dirs, files in os.walk(debug_src):
                for file in files:
                    if file.endswith(".yml"):
                        extra_files.append(os.path.join(base, file))

        return dict(
            host=os.environ.get('HOST', 'localhost'),
            port=int(os.environ.get('PORT', '5000')),
            debug=debug,
            use_reloader=debug,
            use_debugger=debug,
            use_evalex=debug,
            extra_files=extra_files,
        )

    app.run_options = run_options
    return app
