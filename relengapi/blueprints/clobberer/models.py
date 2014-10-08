# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa

from relengapi.lib import db

TBL_PREFIX = 'clobberer_'


class ClobbererBase(db.declarative_base('relengapi')):
    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)
    master = sa.Column(sa.String(100))  # TODO: see about removing this field
    branch = sa.Column(sa.String(50))
    builddir = sa.Column(sa.String(100))
    slave = sa.Column(sa.String(30))


class Builds(ClobbererBase):

    "All clobberable builds."

    __tablename__ = TBL_PREFIX + 'builds'

    buildername = sa.Column(sa.String(100))
    last_build_time = sa.Column(sa.TIMESTAMP, nullable=False)


class ClobberTimes(ClobbererBase):

    "A log of clobber requests."

    __tablename__ = TBL_PREFIX + 'clobber_times'

    lastclobber = sa.Column(sa.TIMESTAMP, nullable=False)
    who = sa.Column(sa.String(50))
