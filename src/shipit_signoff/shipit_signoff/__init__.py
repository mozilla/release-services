# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import backend_common
import shipit_signoff.config
import shipit_signoff.models  # noqa


def create_app(config=None):
    app = backend_common.create_app(
        name=shipit_signoff.config.PROJECT_NAME,
        config=config,
        extensions=[
            'log',
            'security',
            'cors',
            'api',
            'auth',
            'auth0',
            'db',
        ],
    )
    # TODO: add predefined api.yml
    app.api.register(os.path.join(os.path.dirname(__file__), 'api.yml'))
    return app
