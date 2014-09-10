# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests

from flask import Response
from flask import current_app
from flask import stream_with_context


def _get_requests_session():
    try:
        return current_app.proxy_requests_session
    except AttributeError:
        current_app.proxy_requests_session = requests.Session()
        return current_app.proxy_requests_session


def proxy(url):
    req = _get_requests_session().get(url)
    return Response(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])
