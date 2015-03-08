# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib
import mock
import moto
import os

from datetime import datetime
from datetime import timedelta
from flask import current_app
from nose.tools import eq_
from relengapi.blueprints.tooltool import grooming
from relengapi.blueprints.tooltool import tables
from relengapi.lib import time
from relengapi.lib.testing.context import TestContext

DATA = os.urandom(10240)
DATA_DIGEST = hashlib.sha512(DATA).hexdigest()
DATA_KEY = '/sha512/{}'.format(DATA_DIGEST)

cfg = {
    'AWS': {
        'access_key_id': 'aa',
        'secret_access_key': 'ss',
    },
    'TOOLTOOL_REGIONS': {
        'us-east-1': 'tt-use1',
        'us-west-2': 'tt-usw2',
    }
}
test_context = TestContext(config=cfg, databases=['tooltool'])


def add_file_row(size, sha512):
    session = current_app.db.session('tooltool')
    file_row = tables.File(size=size, sha512=sha512)
    session.add(file_row)
    session.commit()
    return file_row


def add_pending_upload_and_file_row(size, sha512, expires, region):
    session = current_app.db.session('tooltool')
    file_row = tables.File(size=size, sha512=sha512)
    pu_row = tables.PendingUpload(
        file=file_row, expires=expires, region=region)
    session.add(file_row)
    session.commit()
    return pu_row, file_row


def make_key(app, region, bucket, key, content):
    s3 = app.aws.connect_to('s3', region)
    bucket = s3.create_bucket(bucket)
    key = bucket.new_key(key)
    key.set_contents_from_string(content)
    return key


def key_exists(app, region, bucket, key):
    s3 = app.aws.connect_to('s3', region)
    bucket = s3.get_bucket(bucket)
    return bucket.get_key(key)


@moto.mock_s3
@test_context
def test_verify_file_instance_bad_size(app):
    """verify_file_instance returns False if the sizes are different"""
    with app.app_context():
        file_row = add_file_row(len(DATA) + 2, DATA_DIGEST)
        key = make_key(app, 'us-east-1', 'tt-use1', DATA_KEY, DATA)
        assert not grooming.verify_file_instance(file_row, key)


@moto.mock_s3
@test_context
def test_verify_file_instance_bad_digest(app):
    """verify_file_instance returns False if the digests are different"""
    with app.app_context():
        file_row = add_file_row(len(DATA), DATA_DIGEST)
        content = os.urandom(len(DATA))
        key = make_key(app, 'us-east-1', 'tt-use1', DATA_KEY, content)
        assert not grooming.verify_file_instance(file_row, key)


@moto.mock_s3
@test_context
def test_verify_file_instance(app):
    """verify_file_instance returns True if the size and digest match"""
    with app.app_context():
        file_row = add_file_row(len(DATA), DATA_DIGEST)
        key = make_key(app, 'us-east-1', 'tt-use1', DATA_KEY, DATA)
        assert grooming.verify_file_instance(file_row, key)


@test_context
def test_check_pending_upload_expired(app):
    """check_pending_upload deletes an expired pending upload"""
    with app.app_context():
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, datetime(1999, 1, 1), 'us-west-2')
        session = app.db.session('tooltool')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted


@moto.mock_s3
@test_context
def test_check_pending_upload_bad_region(app):
    """check_pending_upload deletes a pending upload with a bad region"""
    with app.app_context():
        expires = time.now() + timedelta(days=1)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-1')
        session = app.db.session('tooltool')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted


@moto.mock_s3
@test_context
def test_check_pending_upload_no_upload(app):
    """check_pending_upload leaves the PU in place if the upload is
    not complete"""
    with app.app_context():
        expires = time.now() + timedelta(days=1)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        session = app.db.session('tooltool')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        # PU has not been deleted
        assert tables.PendingUpload.query.first().file.sha512 == DATA_DIGEST


@moto.mock_s3
@test_context
def test_check_pending_upload_not_valid(app):
    """check_pending_upload deletes the PU and the key if the upload is
    invalid."""
    with app.app_context():
        expires = time.now() + timedelta(days=1)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        make_key(app, 'us-west-2', 'tt-usw2', DATA_KEY, 'xxx')
        session = app.db.session('tooltool')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted
        assert not key_exists(app, 'us-west-2', 'tt-usw2', DATA_KEY)


@moto.mock_s3
@test_context
def test_check_pending_upload_success(app):
    """check_pending_upload deletes the PU and adds a FileInstance if valid"""
    with app.app_context():
        expires = time.now() + timedelta(days=1)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        make_key(app, 'us-west-2', 'tt-usw2', DATA_KEY, DATA)
        session = app.db.session('tooltool')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted
        eq_(len(tables.File.query.first().instances), 1)  # FileInstance exists
        assert key_exists(app, 'us-west-2', 'tt-usw2', DATA_KEY)


@test_context
def test_check_pending_uploads(app):
    """check_pending_uploads calls check_pending_upload for each PU"""
    with app.app_context():
        expires = time.now() + timedelta(days=1)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        with mock.patch('relengapi.blueprints.tooltool.grooming.check_pending_upload') as cpu:
            pending_uploads = []
            cpu.side_effect = lambda sess, pu: pending_uploads.append(pu)
            grooming.check_pending_uploads(None)  # job_status is unsed
            assert len(pending_uploads) == 1


@test_context
def test_check_file_pending_uploads(app):
    """check_file_pending_uploads calls check_pending_upload for each PU for the file"""
    with app.app_context():
        expires = time.now() + timedelta(days=1)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        with mock.patch('relengapi.blueprints.tooltool.grooming.check_pending_upload') as cpu:
            pending_uploads = []
            cpu.side_effect = lambda sess, pu: pending_uploads.append(pu)
            grooming.check_file_pending_uploads(DATA_DIGEST)
            assert len(pending_uploads) == 1
