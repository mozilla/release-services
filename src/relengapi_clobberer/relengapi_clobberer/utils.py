# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import time


def cache(fun, cache_duration):
    def wrap(*args, **kwargs):
        key = time.time() // cache_duration
        if getattr(fun, '__cache_key', None) != key:
            fun.__cache_value = fun(*args, **kwargs)
            fun.__cache_key = key
        return getattr(fun, '__cache_value', None)
    return wrap
