# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import cli_common.taskcluster
import releng_notification_policy.config


DEBUG = bool(os.environ.get('DEBUG', False))


# -- LOAD SECRETS -------------------------------------------------------------

required = [
    'SECRET_KEY',
    'DATABASE_URL',
    'TASKCLUSTER_CLIENT_ID',
    'TASKCLUSTER_ACCESS_TOKEN',
]

if not DEBUG:
    required += [
        'RELENG_NOTIFICATION_IDENTITY_ENDPOINT',
    ]

secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    releng_notification_policy.config.PROJECT_NAME,
    required=required,
    existing={x: os.environ.get(x) for x in required if x in os.environ},
    taskcluster_client_id=os.getenv('TASKCLUSTER_CLIENT_ID'),
    taskcluster_access_token=os.getenv('TASKCLUSTER_ACCESS_TOKEN'),
)

locals().update(secrets)


RELENG_NOTIFICATION_IDENTITY_ENDPOINT = secrets.get('RELENG_NOTIFICATION_IDENTITY_ENDPOINT')
if not RELENG_NOTIFICATION_IDENTITY_ENDPOINT:
    RELENG_NOTIFICATION_IDENTITY_ENDPOINT = 'https://localhost:8007'


# -- DATABASE -----------------------------------------------------------------


SQLALCHEMY_DATABASE_URI = secrets['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False
