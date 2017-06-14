# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import


HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}

app_config = {
    'DEBUG': True,
    'TESTING': True,
}


def clear_app(app):
    '''
    '''

    if 'db' in app.__extensions:
        app.db.drop_all()
        app.db.create_all()
