# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import datetime
import mock
import pytz
import wsme

from nose.tools import eq_
from relengapi.blueprints.tooltool import tables
from relengapi.lib import time
from relengapi.lib.testing.context import TestContext

test_context = TestContext(databases=['relengapi'])


@test_context
def test_file_batches_relationship(app):
    with app.app_context():
        session = app.db.session('relengapi')

        file = tables.File(size=100, sha512='abcd', visibility='internal')
        session.add(file)

        batch = tables.Batch(
            uploaded=time.now(), author="dustin", message="hi")
        session.add(batch)

        bf = tables.BatchFile(batch=batch, file=file, filename="foo.txt")
        session.add(bf)

        session.commit()

    with app.app_context():
        file = tables.File.query.first()
        eq_(file.batches['foo.txt'].message, 'hi')

    with app.app_context():
        batch = tables.Batch.query.first()
        eq_(batch.files['foo.txt'].sha512, 'abcd')


@contextlib.contextmanager
def set_time(now):
    with mock.patch('relengapi.lib.time.now') as fake_now:
        fake_now.return_value = now
        yield


@test_context
def test_expires_to_ttl_unset(app):
    f = tables.File(size=100, sha512='ffffff',
                    visibility='internal', expires=None)
    eq_(f.to_json().ttl, wsme.Unset)


@test_context
def test_expires_to_ttl_set(app):
    now = datetime.datetime(2015, 8, 22, tzinfo=pytz.UTC)
    later = now + datetime.timedelta(hours=2)
    f = tables.File(size=100, sha512='ffffff',
                    visibility='internal', expires=later)
    with set_time(now):
        eq_(f.to_json().ttl, 7200)
