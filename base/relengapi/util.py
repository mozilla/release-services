# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import wraps

def synchronized(lock):
    def dec(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrap
    return dec

