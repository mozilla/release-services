# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import backend_common
import releng_channel_status.config


def create_app(config=None):
    app = backend_common.create_app(
        project_name=releng_channel_status.config.PROJECT_NAME,
        app_name=releng_channel_status.config.APP_NAME,
        config=config,
        extensions=[
            'log'
        ],
        redirect_root_to_api=False,
        template_folder='templates'
    )
    return app
