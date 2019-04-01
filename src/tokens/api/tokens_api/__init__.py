# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import backend_common
import tokens_api.config


def create_app(config=None):
    app = backend_common.create_app(
        project_name=tokens_api.config.PROJECT_NAME,
        app_name=tokens_api.config.APP_NAME,
        config=config,
        extensions=[
            'log',
            'security',
            'cors',
            'api',
            'auth',
            'db',
        ],
    )
    app.api.register(os.path.join(os.path.dirname(__file__), 'api.yml'))
    return app
