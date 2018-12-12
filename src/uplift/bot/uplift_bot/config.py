# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os.path
import tempfile

PROJECT_NAME = 'uplift/bot'
DEFAULT_CACHE = '/app/tmp' if os.path.exists('/app/tmp') else os.path.join(tempfile.gettempdir(), 'shipit_bot_cache')
UPLIFT_STATUS = ('approved', 'pending')
