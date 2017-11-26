# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests
from urllib.parse import urljoin


class HttpRequestHelper():
    def __init__(self, base_url):
        self.base_url = base_url

    def _get_url(self, endpoint):
        return urljoin(self.base_url, endpoint)

    def get(self, endpoint, **query_string):
        url = self._get_url(endpoint)
        qs_parameters = query_string if query_string else None
        resp = requests.get(url, params=qs_parameters)
        if resp.status_code == requests.codes.ok:
            return resp.json()
        return None
