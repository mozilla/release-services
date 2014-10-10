# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from models import DB_DECLARATIVE_BASE

SQLALCHEMY_DATABASE_URIS = {
    DB_DECLARATIVE_BASE: os.environ.get('CLOBBERER_DB_URI', 'sqlite:////tmp/clobberer.db')
}
