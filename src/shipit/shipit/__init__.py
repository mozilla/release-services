# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from relengapi_common import create_app


here = os.path.dirname(__file__)


def init_app(app):
    app.api.register(
        os.path.join(here, 'swagger', 'task1.yml'),
        base_url=app.config['SWAGGER_BASE_URL']['relengapi_clobberer'],
    )

app = create_app(__name__, [init_app])

if __name__ == '__main__':
    app.run(debug=True)
