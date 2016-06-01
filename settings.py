# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

DATABASE_URL = os.environ.get('DATABASE_URL')
CACHE = {x: os.environ.get(x) for x in os.environ.keys() if x.startswith('CACHE_')}   # noqa

if 'CACHE_DEFAULT_TIMEOUT' not in CACHE:
    CACHE['CACHE_DEFAULT_TIMEOUT'] = 60 * 5

if not DATABASE_URL:
    raise Exception("You need to specify DATABASE_URL variable.")

if not CACHE:
    raise Exception("You need to specify DATABASE_URL variable.")

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URIS = dict(
    clobberer=DATABASE_URL
)

