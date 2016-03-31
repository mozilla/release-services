# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from alembic import context

from relengapi.lib.alembic import env_py_main


def main():
    dbname = os.path.basename(os.path.dirname(__file__))
    env_py_main(context, dbname)

main()
