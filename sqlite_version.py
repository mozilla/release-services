# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa

engine = sa.create_engine('sqlite://')
conn = engine.contextual_connect()
try:
    r = conn.execute("SELECT sqlite_version()")
    vers_row = r.fetchone()
    r.close()
except:
    print (0,)
if vers_row:
    try:
        print tuple(map(int, vers_row[0].split('.')))
    except (TypeError, ValueError):
        print (0,)
else:
    print (0,)
