# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import jinja2
import logging
import os
import sys

from flask import Flask, send_from_directory

import relengapi_common

__APP = dict()

logger = logging.getLogger('relengapi_common')


def create_app(name, extensions=[], config=None, debug=False, debug_src=None,
               **kw):
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
    elif os.environ.get('APP_SETTINGS'):  # noqa
        app.config.from_envvar('APP_SETTINGS')
    else:
        print("Using default settings; to configure relengapi, set "
              "APP_SETTINGS to point to your settings file")
        sys.exit(1)

    app.jinja_loader = jinja2.loaders.FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates'))

    base_extensions = [
        relengapi_common.log,
        relengapi_common.auth,
        relengapi_common.api,
    ]
    if app.debug is True:
        base_extensions.append(relengapi_common.cors)

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

    def get_run_options():
        extra_files = []
        if debug_src:
            for base, dirs, files in os.walk(debug_src):
                for file in files:
                    if file.endswith(".yml"):
                        extra_files.append(os.path.join(base, file))

        return dict(
            host=os.environ.get('HOST', 'localhost'),
            port=int(os.environ.get('PORT', '5000')),
            debug=DEBUG,
            use_reloader=debug,
            use_debugger=debug,
            use_evalex=debug,
            extra_files=extra_files,
        )

    app.get_run_options = get_run_options
    return app
