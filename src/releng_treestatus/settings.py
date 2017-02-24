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


# -- CACHE --------------------------------------------------------------------

CACHE = {
    x: os.environ.get(x)
    for x in os.environ.keys()
    if x.startswith('CACHE_')
}

if 'REDIS_URL' in os.environ:
    CACHE['CACHE_TYPE'] = 'redis'
    CACHE['CACHE_REDIS_URL'] = os.environ['REDIS_URL']

if 'CACHE_DEFAULT_TIMEOUT' not in CACHE:
    CACHE['CACHE_DEFAULT_TIMEOUT'] = 60 * 5
else:
    CACHE['CACHE_DEFAULT_TIMEOUT'] = float(CACHE['CACHE_DEFAULT_TIMEOUT'])

if 'CACHE_KEY_PREFIX' not in CACHE:
    CACHE['CACHE_KEY_PREFIX'] = "releng_treestatus-"


# -- CACHE --------------------------------------------------------------------

PULSE_USE_SSL = os.environ.get('PULSE_USE_SSL', True)
PULSE_CONNECTION_TIMEOUT = int(os.environ.get('PULSE_CONNECTION_TIMEOUT', 5))
PULSE_HOST = os.environ.get('PULSE_HOST', 'pulse.mozilla.org')
PULSE_PORT = int(os.environ.get('PULSE_PORT', 5671))
PULSE_USER = os.environ.get('PULSE_USER')
PULSE_PASSWORD = os.environ.get('PULSE_PASSWORD')
PULSE_VIRTUAL_HOST = os.environ.get('PULSE_VIRTUAL_HOST', '/')

if not PULSE_USER:
    raise Exception('PULSE_USER not provided.')

if not PULSE_PASSWORD:
    raise Exception('PULSE_PASSWORD not provided.')


PULSE_TREESTATUS_ENABLE = True
PULSE_TREESTATUS_EXCHANGE = os.environ.get(
    'PULSE_TREESTATUS_EXCHANGE',
    'exchange/{}/treestatus'.format(PULSE_USER),
)

if PULSE_TREESTATUS_ENABLE and not PULSE_TREESTATUS_EXCHANGE:
    raise Exception('PULSE_TREESTATUS_EXCHANGE not provided.')
