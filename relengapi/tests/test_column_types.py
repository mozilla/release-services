# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import sqlalchemy as sa
from nose.tools import eq_

from relengapi.lib import db


def test_no_DateTime_columns():
    """No DB columns are of SQLAlchemy type `DateTime`"""
    dt_cols = ["{}:{}".format(dbname, str(col))
               for dbname, base in db._declarative_bases.iteritems()
               for tname, tbl in base.metadata.tables.iteritems()
               for col in tbl.c
               if type(col.type) == sa.DateTime]
    eq_(dt_cols, [],
        "Found DateTime columns -- {} - use relengapi.db.UTCDateTime "
        "to get proper timezone behavior on MySQL".format("; ".join(dt_cols)))
