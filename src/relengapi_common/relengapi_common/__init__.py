# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import sys
import jinja2

from flask import Flask
from relengapi_common import api, auth, log

__app = None


def create_app(name, extensions=[], config=None):
    global __app
    if __app:
        return __app

    if name == '__main__':
        log.setup_console_logging()

    app = Flask(name)

    # load config (settings.py)
    if config:
        app.config.update(**config)
    elif os.environ.has_key('RELENGAPI_SETTINGS'):  # noqa
        app.config.from_envvar('RELENGAPI_SETTINGS')
    else:
        print ("Using default settings; to configure relengapi, set "
               "RELENGAPI_SETTINGS to point to your settings file")
        sys.exit(1)

    app.jinja_loader = jinja2.loaders.FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates'))

    for extension in [log, auth, api] + extensions:
        extension_name = extension.__name__.split('.')[-1]
        setattr(app, extension_name, extension.init_app(app))
        if hasattr(app, 'log'):
            app.log.debug('extension `%s` configured.' % extension_name)

    # configure/initialize specific app features
    #   aws -> tooltool, archiver (only s3 needed)
    #   memcached -> treestatus (via https://pythonhosted.org/Flask-Cache)

    return app
