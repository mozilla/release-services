# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# RelengAPI can use multiple databases when several blueprints are installed.  Each is
# configured with a key in this dictionary.  For example:
#
# SQLALCHEMY_DATABASE_URIS = {
#    'relengapi': 'sqlite:////tmp/relengapi.db',
#    'clobberer': 'sqlite:////tmp/clobberer.db',
#    # .. add other database URIs here, as appropriate for the blueprints
# }
#
# You can use any SQLAlchemy-style database URI.  The default, if no URI
# configuration is present, is to use '*.db' files in the directory containing
# the RelengAPI source code.

# set to True to log SQLAlchemy engine activities (very verbose!)
# SQLALCHEMY_DB_LOG = False

# ===== Authentication and Authorization =====

RELENGAPI_AUTHENTICATION = {
    # use the default, browserid:
    'type': 'browserid',

    # .. or based on a header from a proxy:
    # 'type': 'external',
    # 'header': 'Remote-User',
}

RELENGAPI_PERMISSIONS = {
    'type': 'static',
    'permissions': {
        # 'dustin@mozilla.com': ['some.permission'],
    },
}

# ===== Celery =====
# Any Celery configuration option can be included here; see
# http://docs.celeryproject.org/en/master/configuration.html#configuration
