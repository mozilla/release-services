# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa
import time

from relengapi.lib import db

DB_DECLARATIVE_BASE = 'clobberer'


class ClobbererBase(db.declarative_base(DB_DECLARATIVE_BASE)):
    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)
    branch = sa.Column(sa.String(50), index=True)
    builddir = sa.Column(sa.String(100), index=True)


class Build(ClobbererBase, db.UniqueMixin):
    "A clobberable build."

    __tablename__ = 'builds'

    buildername = sa.Column(sa.String(100))
    last_build_time = sa.Column(
        sa.Integer,
        nullable=False,
        default=int(time.time())
    )

    @classmethod
    def unique_hash(cls, branch, builddir, buildername, *args, **kwargs):
        return "{}:{}:{}".format(branch, builddir, buildername)

    @classmethod
    def unique_filter(cls, query, branch, builddir, buildername, *args, **kwargs):
        return query.filter(
            cls.branch == branch,
            cls.builddir == builddir,
            cls.buildername == buildername
        )


class ClobberTime(ClobbererBase, db.UniqueMixin):
    "A clobber request."

    __tablename__ = 'clobber_times'
    __table_args__ = (
        # Index to speed up lastclobber lookups
        sa.Index('ix_get_clobber_times', 'slave', 'builddir', 'branch'),
    )
    slave = sa.Column(sa.String(30), index=True)
    lastclobber = sa.Column(
        sa.Integer,
        nullable=False,
        default=int(time.time()),
        index=True
    )
    who = sa.Column(sa.String(50))

    @classmethod
    def unique_hash(cls, branch, slave, builddir, *args, **kwargs):
        return "{}:{}:{}".format(branch, slave, builddir)

    @classmethod
    def unique_filter(cls, query, branch, slave, builddir, *args, **kwargs):
        return query.filter(
            cls.branch == branch,
            cls.slave == slave,
            cls.builddir == builddir,
        )
