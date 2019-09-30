# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

PROJECT_NAME = 'treestatus/api'
APP_NAME = 'treestatus_api'

SCOPE_PREFIX = 'project:releng:treestatus'
SCOPE_TREES_UPDATE = f'{SCOPE_PREFIX}/trees/update'
SCOPE_TREES_CREATE = f'{SCOPE_PREFIX}/trees/create'
SCOPE_TREES_DELETE = f'{SCOPE_PREFIX}/trees/delete'
SCOPE_REVERT_CHANGES = f'{SCOPE_PREFIX}/recent_changes/revert'

DEFAULT_TREE = dict(
    reason='New tree',
    status='closed',
    tags=[],
    log_id=None,
)
