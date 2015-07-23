# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wrapt

from flask import make_response


def response_headers(*headers):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        # skip apimethod __data_only__ calls
        if '_data_only_' in kwargs:
            return wrapped(*args, **kwargs)
        # mark the response to avoid caching; insert this decorator just after
        # the route decorators
        resp = make_response(wrapped(*args, **kwargs))
        if 200 <= resp.status_code < 400:
            for h, v in headers:
                resp.headers[h] = v
        return resp
    return wrapper
