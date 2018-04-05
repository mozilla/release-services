# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

PROJECT_NAME = 'shipit-uplift'
APP_NAME = 'shipit_uplift'

# Tasckcluster scopes
SCOPES_USER = [
    'project:shipit:user',
    'project:shipit:analysis/use',
    'project:shipit:bugzilla'
]
SCOPES_ADMIN = SCOPES_USER + [
    'project:shipit:admin',
]
SCOPES_BOT = [
    'project:shipit:bot',
    'project:shipit:analysis/manage',
]
