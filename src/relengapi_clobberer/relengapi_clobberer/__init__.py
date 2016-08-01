# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from relengapi_common import create_app, db
from relengapi_clobberer import _app

app = create_app(__name__, [db, _app])

if __name__ == '__main__':
    app.run(debug=True)
