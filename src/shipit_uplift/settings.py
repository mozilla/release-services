# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

DATABASE_URL = os.environ.get('DATABASE_URL')
CACHE = {x: os.environ.get(x) for x in os.environ.keys() if x.startswith('CACHE_')}   # noqa
SWAGGER_BASE_URL = os.environ.get('SWAGGER_BASE_URL')


if 'CACHE_DEFAULT_TIMEOUT' not in CACHE:
    CACHE['CACHE_DEFAULT_TIMEOUT'] = 60 * 5


if 'REDIS_URL' in os.environ:
    CACHE['CACHE_TYPE'] = 'redis'
    CACHE['CACHE_REDIS_URL'] = os.environ['REDIS_URL']

if not DATABASE_URL:
    raise Exception("You need to specify DATABASE_URL variable.")
if not DATABASE_URL.startswith('postgresql://') \
  and not DATABASE_URL.startswith('postgres://'):
    raise Exception('Shipit uplift needs a postgresql:// DATABASE_URL')

if not CACHE:
    raise Exception("You need to specify CACHE variable.")

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
