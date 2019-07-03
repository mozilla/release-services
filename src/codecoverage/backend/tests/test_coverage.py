# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json


def test_coverage_supported_extensions_api(client):
    # List supported extensions for coverage analysis through the API
    resp = client.get('/v2/extensions')
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert set(data) == set([
        'c', 'h', 'cpp', 'cc', 'cxx', 'hh', 'hpp',
        'hxx', 'js', 'jsm', 'xul', 'xml', 'html', 'xhtml',
    ])
