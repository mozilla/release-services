# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa

from relengapi.lib import db
from relengapi.util import tz

DB_DECLARATIVE_BASE = 'relengapi'

class ClobbererBase(db.declarative_base(DB_DECLARATIVE_BASE)):
    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)
    branch = sa.Column(sa.String(50))
    master = sa.Column(sa.String(50))
    slave = sa.Column(sa.String(50))
    builddir = sa.Column(sa.String(100))


class Build(ClobbererBase, db.UniqueMixin):

    "A clobberable build."

    __tablename__ = 'builds'

    buildername = sa.Column(sa.String(100))
    last_build_time = sa.Column(
        db.UTCDateTime,
        nullable=False,
        default=tz.utcnow
    )

    @classmethod
    def unique_hash(cls, branch, slave, builddir, buildername, *args, **kwargs):
        return "{}:{}:{}:{}".format(branch, slave, builddir, buildername)

    @classmethod
    def unique_filter(cls, query, branch, slave, builddir, buildername, *args, **kwargs):
        return query.filter(
            cls.branch==branch,
            cls.slave==slave,
            cls.builddir==builddir,
            cls.buildername==buildername
        )


class ClobberTime(ClobbererBase):

    "A clobber request."

    __tablename__ = 'clobber_times'

    lastclobber = sa.Column(
        db.UTCDateTime,
        nullable=False,
        default=tz.utcnow
    )
    who = sa.Column(sa.String(50))
