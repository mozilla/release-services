# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

SQLALCHEMY_DATABASE_URIS = {
    'relengapi': 'sqlite:////path/to/my.db',
    # .. add other database URIs here, as appropriate for the blueprints
}

##
# Authentication and Authorization

RELENGAPI_AUTHENTICATION = {
    # use the default, browserid:
    'type': 'browserid',

    # .. or based on a header from a proxy:
    # 'type': 'external',
    # 'header': 'Remote-User',
}

RELENGAPI_ACTIONS = {
    'type': 'static',
    'actions': {
        # 'dustin@mozilla.com': ['some.permission'],
    },
}

## Celery
# Any Celery configuration option can be included here; see
# http://docs.celeryproject.org/en/master/configuration.html#configuration

