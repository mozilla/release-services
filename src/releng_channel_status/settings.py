# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import os


DEBUG = bool(os.environ.get('DEBUG', False))

# -- Balrog Public API settings -----------------------------------------------
BALROG_API_URL = 'https://aus-api.mozilla.org/api/v1/'
RULES_ENDPOINT = 'rules'
SINGLE_RULE_ENDPOINT = 'rules/{alias}'
RELEASE_ENDPOINT = 'releases/{release}'
DEFAULT_ALIAS = 'firefox-nightly'
UPDATE_MAPPINGS = ['Firefox-mozilla-central-nightly-latest']
DEFAULT_LOCALE = 'en-US'
DEFAULT_PLATFORM = 'Linux_x86_64-gcc3'
