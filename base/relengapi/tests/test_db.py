import datetime
import os
import sqlalchemy as sa

from nose.tools import eq_, ok_, with_setup, assert_not_equal
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
@with_setup(setup=set_system_timezone_no_utc, teardown=restore_system_timezone)
def test_UTCDateTime_converts(app):
    session = app.db.session('test_db')
    now = datetime.datetime.now().replace(tzinfo=pytz.timezone("US/Pacific"))
    session.add(DevTable(date=now))
    session.commit()
    instance = session.query(DevTable).all()[0]
    assert_not_equal(instance.date.replace(tzinfo=None), now.replace(tzinfo=None))


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
    eq_(daylight.strftime('%Y-%m-%d %H:%M:%S %Z%z'), '2011-06-27 02:00:00 PDT-0700')
    session.add(DevTable(date=daylight))
    session.commit()
    instances = session.query(DevTable).all()
    eq_(1, len(instances))
    ok_(isinstance(instances[0].date, datetime.datetime))
    eq_(instances[0].date.strftime('%Y-%m-%d %H:%M:%S %Z%z'), '2011-06-27 09:00:00 UTC+0000')


@TestContext(databases=['test_db'])
def test_UTCDateTime_converts_standard(app):
    session = app.db.session('test_db')
    standard = datetime.datetime(2011, 6, 27, 2, 0, 0, tzinfo=pytz.timezone("US/Pacific"))
    eq_(standard.strftime('%Y-%m-%d %H:%M:%S %Z%z'), '2011-06-27 02:00:00 PST-0800')
    session.add(DevTable(date=standard))
    session.commit()
    instances = session.query(DevTable).all()
    eq_(1, len(instances))
    ok_(isinstance(instances[0].date, datetime.datetime))
    eq_(instances[0].date.strftime('%Y-%m-%d %H:%M:%S %Z%z'), '2011-06-27 10:00:00 UTC+0000')
