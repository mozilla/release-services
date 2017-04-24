# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os


SWAGGER_BASE_URL = os.environ.get('SWAGGER_BASE_URL')


# -- DATABASE -----------------------------------------------------------------

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise Exception("You need to specify DATABASE_URL variable.")

if not DATABASE_URL.startswith('postgresql://'):
    raise Exception('Shipit dashboard needs a postgresql:// DATABASE_URL')


SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
