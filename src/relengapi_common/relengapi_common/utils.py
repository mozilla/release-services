# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import urlparse
import wrapt

from flask import request
from flask import url_for


_mime_types = ('application/json', 'text/html')


def synchronized(lock):
    @wrapt.decorator
    def wrap(wrapper, instance, args, kwargs):
        with lock:
            return wrapper(*args, **kwargs)
    return wrap


def is_browser():
    """Is the current request from a browser?"""
    # all subrequests are not from browsers
    if hasattr(request._get_current_object(), 'is_subrequest') and \
            request.is_subrequest:
        return False
    best_match = request.accept_mimetypes.best_match(_mime_types)
    return best_match == 'text/html'


def safe_redirect_path(url):
    parts = urlparse.urlparse(url)
    if parts.scheme or parts.netloc:
        return url_for('root')
    # note that Werkzeug takes care of making redirect URLs absolute,
    # so there's no need to do so here.
    return url
