# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import code_coverage_backend.config


def create_app(config=None):
    import backend_common

    app = backend_common.create_app(
        project_name=code_coverage_backend.config.PROJECT_NAME,
        app_name=code_coverage_backend.config.PROJECT_PATH,
        config=config,
        extensions=[
            'log',
            'security',
            'cors',
            'api',
        ],
    )
    # TODO: add predefined api.yml
    app.api.register(os.path.join(os.path.dirname(__file__), 'api.yml'))
    return app
