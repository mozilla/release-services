# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import cli_common.taskcluster
import codecoverage_backend.config

secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    codecoverage_backend.config.PROJECT_NAME,
    required=['GOOGLE_CLOUD_STORAGE', 'APP_CHANNEL'],
    existing={x: os.environ.get(x) for x in ['REDIS_URL'] if x in os.environ},
    taskcluster_client_id=os.environ.get('TASKCLUSTER_CLIENT_ID'),
    taskcluster_access_token=os.environ.get('TASKCLUSTER_ACCESS_TOKEN'),
)

REDIS_URL = secrets['REDIS_URL'] if 'REDIS_URL' in secrets else 'redis://localhost:6379'
DATADOG_API_KEY = secrets.get('DATADOG_API_KEY')
APP_CHANNEL = secrets['APP_CHANNEL']
GOOGLE_CLOUD_STORAGE = secrets.get('GOOGLE_CLOUD_STORAGE')
