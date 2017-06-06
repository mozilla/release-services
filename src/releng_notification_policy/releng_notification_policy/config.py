# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import os


PROJECT_NAME = 'releng-notification-policy'

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

RELENG_NOTIFICATION_IDENTITY_ENDPOINT = os.getenv('RELENG_NOTIFICATION_IDENTITY_ENDPOINT', 'https://localhost:8007')
RELENG_NOTIFICATION_SOURCE_EMAIL = os.getenv('RELENG_NOTIFICATION_SOURCE_EMAIL')
