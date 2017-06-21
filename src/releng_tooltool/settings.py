# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import cli_common.taskcluster
import releng_tooltool.config


DEBUG = bool(os.environ.get('DEBUG', False))


# -- LOAD SECRETS -------------------------------------------------------------

required = [
    'SECRET_KEY',
    'DATABASE_URL',
    # https://github.com/mozilla/build-cloud-tools/blob/master/configs/cloudformation/tooltool.py
    'S3_REGIONS',
    # https://github.com/mozilla/build-cloud-tools/blob/master/configs/cloudformation/iam_relengapi.py
    'S3_REGIONS_ACCESS_KEY_ID',
    'S3_REGIONS_SECRET_ACCESS_KEY',
]

existing = {x: os.environ.get(x) for x in required if x in os.environ}
existing['ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD'] = False
# This value should be fairly short (and its value is included in the
# `upload_batch` docstring).  Uploads cannot be validated until this
# time has elapsed, otherwise a malicious uploader could alter a file
# after it had been verified.
existing['UPLOAD_EXPIRES_IN'] = 60
existing['DOWLOAD_EXPIRES_IN'] = 60

secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    releng_tooltool.config.PROJECT_NAME,
    required=required,
    existing=existing,
    taskcluster_client_id=os.environ.get('TASKCLUSTER_CLIENT_ID'),
    taskcluster_access_token=os.environ.get('TASKCLUSTER_ACCESS_TOKEN'),
)

locals().update(secrets)

SECRET_KEY = os.urandom(24)

# -- DATABASE -----------------------------------------------------------------

SQLALCHEMY_DATABASE_URI = secrets['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False
