# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

import backend_common
import backend_common.db


DEBUG = bool(os.environ.get('DEBUG', __name__ == '__main__'))
HERE = os.path.dirname(os.path.abspath(__file__))
APP_SETTINGS = os.path.abspath(os.path.join(HERE, '..', 'settings.py'))


def init_app(app):
    return app.api.register(
        os.path.join(os.path.dirname(__file__), 'api.yml'))


if not os.environ.get('APP_SETTINGS') and \
       os.path.isfile(APP_SETTINGS):
    os.environ['APP_SETTINGS'] = APP_SETTINGS


app = backend_common.create_app(
    "releng_archiver",
    extensions=[init_app, backend_common.db],
    debug=DEBUG,
    debug_src=HERE,
)


if __name__ == "__main__":
    app.run(**app.run_options())
