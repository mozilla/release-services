# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os.path

from flask import jsonify
from flask import request


def fake_auth():
    username = request.args.get('access_token')
    users = json.loads(open(os.path.join(os.path.dirname(__file__), 'fakeauth.json')).read())
    if username not in users:
        return b'Unauthorized'
    else:
        return jsonify(users.get(username))
