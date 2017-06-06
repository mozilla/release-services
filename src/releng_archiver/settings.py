# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import cli_common.taskcluster
import releng_archiver.config


DEBUG = bool(os.environ.get('DEBUG', False))


# -- LOAD SECRETS -------------------------------------------------------------

required = [
    'DATABASE_URL',
]

XXX = os.environ.get('TASKCLUSTER_CLIENT_ID')
YYY = os.environ.get('TASKCLUSTER_ACCESS_TOKEN')
secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    releng_archiver.config.PROJECT_NAME,
    required=required,
    existing={x: os.environ.get(x) for x in required},
    taskcluster_client_id=XXX,
    taskcluster_access_token=YYY,
)

locals().update(secrets)


# -- DATABASE -----------------------------------------------------------------

SQLALCHEMY_DATABASE_URI = secrets['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False
