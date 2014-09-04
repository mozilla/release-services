# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import os
import sqlalchemy as sa

from nose.tools import eq_, ok_, with_setup, assert_not_equal
from nose.tools import assert_raises
import pytz

from relengapi.testing import TestContext
from relengapi import db
from relengapi.util import tz

_old_system_timezone = None


def set_system_timezone_no_utc():
    global _old_system_timezone
    _old_system_timezone = os.environ.get('TZ', None)
    os.environ['TZ'] = "US/Pacific"


def restore_system_timezone():
    if _old_system_timezone:
        os.environ['TZ'] = _old_system_timezone
    else:
        del os.environ['TZ']


class DevTable(db.declarative_base('test_db')):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True)
    date = sa.Column(db.UTCDateTime(timezone=True))


@TestContext(databases=['test_db'])
def test_ensure_empty(app):
    session = app.db.session('test_db')
    instances = session.query(DevTable).all()
    eq_(0, len(instances))


@TestContext(databases=['test_db'])
def test_UTCDateTime_datetime_object(app):
    session = app.db.session('test_db')
    utcnow = datetime.datetime.utcnow()
    session.add(DevTable(date=utcnow))
    session.commit()
    instances = session.query(DevTable).all()
    eq_(1, len(instances))
    ok_(isinstance(instances[0].date, datetime.datetime))
    eq_(instances[0].date.tzinfo, pytz.UTC)
    eq_(instances[0].date, utcnow.replace(tzinfo=pytz.UTC))


@TestContext(databases=['test_db'])
def test_UTCDateTime_null(app):
    session = app.db.session('test_db')
    session.add(DevTable(date=None))
    session.commit()
    instances = session.query(DevTable).all()
    eq_(1, len(instances))
    eq_(instances[0].date, None)


@TestContext(databases=['test_db'])
@with_setup(setup=set_system_timezone_no_utc, teardown=restore_system_timezone)
def test_UTCDateTime_converts(app):
    session = app.db.session('test_db')
    now = datetime.datetime.now().replace(tzinfo=pytz.timezone("US/Pacific"))
    session.add(DevTable(date=now))
    session.commit()
    instance = session.query(DevTable).all()[0]
    assert_not_equal(
        instance.date.replace(tzinfo=None), now.replace(tzinfo=None))


@TestContext(databases=['test_db'])
@with_setup(setup=set_system_timezone_no_utc, teardown=restore_system_timezone)
def test_UTCDateTime_no_convert_utc(app):
    session = app.db.session('test_db')
    now = tz.utcnow()
    session.add(DevTable(date=now))
    session.commit()
    instances = session.query(DevTable).all()
    eq_(1, len(instances))
    ok_(isinstance(instances[0].date, datetime.datetime))
    eq_(instances[0].date.replace(tzinfo=None), now.replace(tzinfo=None))


@TestContext(databases=['test_db'])
def test_UTCDateTime_converts_daylight(app):
    session = app.db.session('test_db')
    daylight = datetime.datetime(2011, 6, 27, 2, 0, 0)
    daylight = pytz.timezone("US/Pacific").localize(daylight, is_dst=True)
    eq_(daylight.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
        '2011-06-27 02:00:00 PDT-0700')
    session.add(DevTable(date=daylight))
    session.commit()
    instances = session.query(DevTable).all()
    eq_(1, len(instances))
    ok_(isinstance(instances[0].date, datetime.datetime))
    eq_(instances[0].date.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
        '2011-06-27 09:00:00 UTC+0000')


@TestContext(databases=['test_db'])
def test_UTCDateTime_converts_standard(app):
    session = app.db.session('test_db')
    standard = datetime.datetime(
        2011, 6, 27, 2, 0, 0, tzinfo=pytz.timezone("US/Pacific"))
    eq_(standard.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
        '2011-06-27 02:00:00 PST-0800')
    session.add(DevTable(date=standard))
    session.commit()
    instances = session.query(DevTable).all()
    eq_(1, len(instances))
    ok_(isinstance(instances[0].date, datetime.datetime))
    eq_(instances[0].date.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
        '2011-06-27 10:00:00 UTC+0000')


class Uniqueness_Table(db.declarative_base('test_db'), db.UniqueMixin):
    __tablename__ = 'uniqueness_test'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(18), nullable=False, unique=True)
    other = sa.Column(sa.String(18), nullable=True)

    @classmethod
    def unique_hash(cls, name, *args, **kwargs):
        return name

    @classmethod
    def unique_filter(cls, query, name, *args, **kwargs):
        return query.filter(Uniqueness_Table.name == name)


@TestContext(databases=['test_db'])
def test_unique_mixin(app):
    session = app.db.session('test_db')
    row1 = Uniqueness_Table.as_unique(session, name='r1')
    row2 = Uniqueness_Table.as_unique(session, name='r2')
    row3 = Uniqueness_Table.as_unique(session, name='r3')
    row1b = Uniqueness_Table.as_unique(session, name='r1')
    row4 = Uniqueness_Table.as_unique(session, name='r4', other="row4a")
    row4b = Uniqueness_Table.as_unique(session, name='r4', other="row4b")
    ok_(row1 is row1b)
    assert_not_equal(row1, row2)
    assert_not_equal(row1, row3)
    assert_not_equal(row2, row3)
    ok_(row4 is row4b)
    eq_(row4b.other, "row4a")
    session.commit()
    instances = session.query(Uniqueness_Table).all()
    eq_(4, len(instances))
    ok_(instances[2].name, 'r2')


@TestContext(databases=['test_db'])
def test_unique_request_expires_cache(app):
    with app.test_request_context():
        session = app.db.session('test_db')
        Uniqueness_Table.as_unique(session, name='r1')
        session.commit()
        instances = session.query(Uniqueness_Table).all()
        eq_(1, len(instances))
        row2 = Uniqueness_Table.as_unique(session, name='r2')
        row3 = Uniqueness_Table.as_unique(session, name='r3', other='row3a')
        # don't commit

    with app.test_request_context():
        session = app.db.session('test_db')
        instances = session.query(Uniqueness_Table).all()
        eq_(1, len(instances))
        row2b = Uniqueness_Table.as_unique(session, name='r2')
        assert_not_equal(row2, row2b)
        row3b = Uniqueness_Table.as_unique(session, name='r3', other='row3b')
        assert_not_equal(row3, row3b)
        eq_(row3b.other, 'row3b')
        session.commit()
        instances = session.query(Uniqueness_Table).all()
        eq_(3, len(instances))


@TestContext(databases=['test_db'])
def test_unique_session_rollback(app):
    session = app.db.session('test_db')
    Uniqueness_Table.as_unique(session, name='r1')
    session.commit()
    instances = session.query(Uniqueness_Table).all()
    eq_(1, len(instances))
    Uniqueness_Table.as_unique(session, name='r2')
    row3 = Uniqueness_Table.as_unique(session, name='r3', other='row3a')
    instances = session.query(Uniqueness_Table).all()
    eq_(3, len(instances))
    session.rollback()
    instances = session.query(Uniqueness_Table).all()
    session.rollback()
    instances = session.query(Uniqueness_Table).all()
    eq_(1, len(instances))
    Uniqueness_Table.as_unique(session, name='r2')
    row3b = Uniqueness_Table.as_unique(session, name='r3', other='row3b')
    instances = session.query(Uniqueness_Table).all()
    eq_(3, len(instances))
    assert_not_equal(row3, row3b)
    eq_(row3b.other, 'row3b')
    session.commit()


@TestContext(databases=['test_db'])
def test_unique_races(app):
    session = app.db.session('test_db')
    unique_args = (session, Uniqueness_Table, Uniqueness_Table.unique_hash,
                   Uniqueness_Table.unique_filter, Uniqueness_Table, (),
                   {'name': 'r1'})
    results = {}
    # one call to _unique nested in the middle of another..

    def inner():
        results['inner'] = db._unique(*unique_args)

    def outer():
        return db._unique(*unique_args, _test_hook=inner)
    assert_raises(sa.exc.IntegrityError, outer)


@TestContext(databases=['test_db'])
def test_database_names(app):
    with app.app_context():
        # the full list of database names depends on the loaded
        # blueprints, so just assert that test_db is in there.
        assert 'test_db' in app.db.database_names
