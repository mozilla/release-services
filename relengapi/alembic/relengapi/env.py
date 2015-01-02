# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from relengapi.lib.alembic import env_py_main
import os

def main():
    dbname = os.path.basename(os.path.dirname(__file__))
    env_py_main(dbname)
