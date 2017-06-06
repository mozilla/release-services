# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import os


PROJECT_NAME = 'releng-notification-policy'
PROJECT_PATH_NAME = PROJECT_NAME.replace('-', '_')

TASKCLUSTER_CLIENT_ID = os.getenv('TASKCLUSTER_CLIENT_ID')
TASKCLUSTER_ACCESS_TOKEN = os.getenv('TASKCLUSTER_ACCESS_TOKEN')

RELENG_NOTIFICATION_IDENTITY_ENDPOINT = os.getenv('RELENG_NOTIFICATION_IDENTITY_ENDPOINT', 'https://localhost:8007')
