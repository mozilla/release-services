# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import pytz
import re


def now():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)


def keyname(digest):
    return 'sha512/{}'.format(digest)


is_valid_sha512 = re.compile(r'^[0-9a-f]{128}$').match
