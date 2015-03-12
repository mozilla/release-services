# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import urlparse

from flask import url_for


def safe_redirect_path(url):
    parts = urlparse.urlparse(url)
    if parts.scheme or parts.netloc:
        return url_for('root')
    # note that Werkzeug takes care of making redirect URLs absolute,
    # so there's no need to do so here.
    return url
