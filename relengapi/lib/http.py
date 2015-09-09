# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import wrapt
from flask import make_response
from werkzeug.exceptions import HTTPException

_status_ranges = {
    '2xx': lambda c: 200 <= c < 300,
    '3xx': lambda c: 300 <= c < 400,
    '4xx': lambda c: 400 <= c < 500,
    '5xx': lambda c: 500 <= c < 600,
}


def response_headers(*headers, **kwargs):
    assert set(kwargs.keys()) <= set(['status_codes'])
    status_codes = kwargs.pop('status_codes', None)
    if not status_codes:
        def status_match(c):
            return True
    elif callable(status_codes):
        status_match = status_codes
    elif isinstance(status_codes, (unicode, str)):
        if status_codes in _status_ranges:
            status_match = _status_ranges[status_codes]
        else:
            raise ValueError("invalid status_codes " + status_codes)
    elif isinstance(status_codes, int):
        code = status_codes

        def status_match(c):
            return c == code
    else:
        codeset = set(status_codes)

        def status_match(c):
            return c in codeset

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        # skip apimethod __data_only__ calls
        if '_data_only_' in kwargs:
            return wrapped(*args, **kwargs)
        try:
            resp = make_response(wrapped(*args, **kwargs))
        except HTTPException as e:
            if status_match(e.code):
                resp = e.get_response()
                for h, v in headers:
                    resp.headers[h] = v
                return resp
            raise
        if status_match(resp.status_code):
            for h, v in headers:
                resp.headers[h] = v
        return resp
    return wrapper
