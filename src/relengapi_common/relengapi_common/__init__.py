# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import jinja2
import logging
import os
import sys

from flask import Flask, send_from_directory

from relengapi_common import api, auth, log, cache, cors

__APP = dict()

logger = logging.getLogger('relengapi_common')


def create_app(name, extensions=[], config=None, debug=False, **kw):
    global __APP
    if __APP and name in __APP:
        return __APP[name]

    if name == '__main__':
        log.setup_console_logging()

    logger.debug('Initializing app: {}'.format(name))

    app = __APP[name] = Flask(name, **kw)
    app.debug = debug

    # load config (settings.py)
    if config:
        app.config.update(**config)
    elif os.environ.get('RELENGAPI_SETTINGS'):  # noqa
        app.config.from_envvar('RELENGAPI_SETTINGS')
    else:
        print("Using default settings; to configure relengapi, set "
              "RELENGAPI_SETTINGS to point to your settings file")
        sys.exit(1)

    app.jinja_loader = jinja2.loaders.FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates'))

    base_extensions = [log, auth, api, cache]
    if app.debug is True:
        base_extensions.append(cors)

    for extension in base_extensions + extensions:

        if type(extension) is tuple:
            extension_name, extension_init = extension
        elif not hasattr(extension, 'init_app'):
            extension_name = None
            extension_init = extension
        else:
            extension_name = extension.__name__.split('.')[-1]
            extension_init = extension.init_app

        logger.debug('Initializing extension "{}" for ""'.format(
            extension_name or str(extension_init), name))

        _app = extension_init(app)
        if _app and extension_name is not None:
            setattr(app, extension_name, _app)

        if hasattr(app, 'log'):
            app.log.debug('extension `%s` configured.' % extension_name)

    return app


def create_apps(name, debug=False):
    app = create_app(name, debug=debug)

    @app.route('/', defaults=dict(path='index.html'), methods=['GET'])
    @app.route('/<path:path>', methods=['GET'])
    def index(path):
        base_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../../relengapi_tools/build'))
        if not os.path.exists(os.path.join(base_dir, path)):
            path = 'index.html'
        return send_from_directory(base_dir, path)

    return app
