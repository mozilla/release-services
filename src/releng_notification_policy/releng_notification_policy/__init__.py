# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import backend_common
import cli_common.taskcluster
from backend_common.notifications import CHANNELS, URGENCY_LEVELS
import releng_notification_policy.config
import releng_notification_policy.models  # noqa


def create_app(config=None):
    app = backend_common.create_app(
        project_name=releng_notification_policy.config.PROJECT_NAME,
        app_name=releng_notification_policy.config.APP_NAME,
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

    # Add TaskCluster notify to service
    app.notify = cli_common.taskcluster.get_service(
        'notify',
        app.config.get('TASKCLUSTER_CLIENT_ID'),
        app.config.get('TASKCLUSTER_ACCESS_TOKEN')
    )

    # TODO: add predefined api.yml
    app.api.register(os.path.join(os.path.dirname(__file__), 'api.yml'),
                     arguments={
                         'CHANNELS': CHANNELS,
                         'URGENCY_LEVELS': URGENCY_LEVELS,
                     })
    return app
