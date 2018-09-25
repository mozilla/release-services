# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import re
import typing

import pytz


def now() -> datetime.datetime:
    return datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)


def keyname(digest: str) -> str:
    return 'sha512/{}'.format(digest)


def is_valid_sha512(sha512: str) -> typing.Optional[typing.Match[str]]:
    return re.compile(r'^[0-9a-f]{128}$').match(sha512)
