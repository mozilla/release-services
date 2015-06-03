# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import boto
import hashlib
import mock
import moto
import os

from contextlib import contextmanager
from datetime import datetime
from datetime import timedelta
from flask import current_app
from nose.tools import eq_
from relengapi.blueprints.tooltool import grooming
from relengapi.blueprints.tooltool import tables
from relengapi.blueprints.tooltool import util
from relengapi.lib import time
from relengapi.lib.testing.context import TestContext

DATA = os.urandom(10240)
DATA_DIGEST = hashlib.sha512(DATA).hexdigest()
DATA_KEY = util.keyname(DATA_DIGEST)

NOW = 1425592922

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
test_context = TestContext(config=cfg, databases=['relengapi'])


def assert_file_instances(app, digest, exp_regions):
    with app.app_context():
        tbl = tables.File
        file = tbl.query.filter(tbl.sha512 == digest).first()
        regions = [i.region for i in file.instances]
        eq_(set(regions), set(exp_regions))


def add_file_row(size, sha512, instances=[]):
    session = current_app.db.session('relengapi')
    file_row = tables.File(size=size, visibility='public', sha512=sha512)
    session.add(file_row)
    for region in instances:
        session.add(tables.FileInstance(file=file_row, region=region))
    session.commit()
    return file_row


def add_pending_upload_and_file_row(size, sha512, expires, region):
    session = current_app.db.session('relengapi')
    file_row = tables.File(size=size, visibility='public', sha512=sha512)
    pu_row = tables.PendingUpload(
        file=file_row, expires=expires, region=region)
    session.add(file_row)
    session.commit()
    return pu_row, file_row


def make_bucket(app, region, bucket):
    s3 = app.aws.connect_to('s3', region)
    try:
        return s3.create_bucket(bucket)
    except boto.exception.S3ResponseError:
        return s3.get_bucket(bucket)


def make_key(app, region, bucket, key, content, storage_class='STANDARD'):
    bucket = make_bucket(app, region, bucket)
    key = bucket.new_key(key)
    key.storage_class = storage_class
    key.set_contents_from_string(content)
    return key


def key_exists(app, region, bucket, key):
    s3 = app.aws.connect_to('s3', region)
    bucket = s3.get_bucket(bucket)
    return bucket.get_key(key)


@contextmanager
def set_time(now=NOW):
    with mock.patch('time.time') as fake:
        fake.return_value = now
        yield

# tests


@moto.mock_s3
@test_context
def test_verify_file_instance_bad_size(app):
    """verify_file_instance returns False if the sizes are different"""
    with app.app_context():
        key = make_key(app, 'us-east-1', 'tt-use1', DATA_KEY, DATA)
        assert not grooming.verify_file_instance(
            DATA_DIGEST, len(DATA) + 2, key)


@moto.mock_s3
@test_context
def test_verify_file_instance_bad_digest(app):
    """verify_file_instance returns False if the digests are different"""
    with app.app_context():
        bogus_digest = hashlib.sha512(os.urandom(len(DATA))).hexdigest()
        key = make_key(app, 'us-east-1', 'tt-use1', DATA_KEY, DATA)
        assert not grooming.verify_file_instance(bogus_digest, len(DATA), key)


@moto.mock_s3
@test_context
def test_verify_file_instance_bad_storage_class(app):
    """verify_file_instance returns False if the key's storage class is not STANDARD."""
    with app.app_context():
        key = make_key(
            app, 'us-east-1', 'tt-use1', DATA_KEY, DATA, storage_class='RRS')
        assert not grooming.verify_file_instance(DATA_DIGEST, len(DATA), key)


@moto.mock_s3
@test_context
def test_verify_file_instance_bad_acl(app):
    """verify_file_instance returns True if the key has a bad URL, but fixes it."""
    with app.app_context():
        key = make_key(app, 'us-east-1', 'tt-use1', DATA_KEY, DATA)
        key.set_acl('public-read')
        assert grooming.verify_file_instance(DATA_DIGEST, len(DATA), key)
        # moto doesn't support acls yet, so that's the best we can do


@moto.mock_s3
@test_context
def test_verify_file_instance(app):
    """verify_file_instance returns True if the size and digest match"""
    with app.app_context():
        key = make_key(app, 'us-east-1', 'tt-use1', DATA_KEY, DATA)
        assert grooming.verify_file_instance(DATA_DIGEST, len(DATA), key)


@test_context
def test_check_pending_upload_not_expired(app):
    """check_pending_upload doesn't check anything if the URL isn't expired yet"""
    with app.app_context(), set_time():
        expires = time.now() + timedelta(seconds=10)  # 10s shy
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        session = app.db.session('relengapi')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(len(tables.PendingUpload.query.all()), 1)  # PU still exists


@test_context
def test_check_pending_upload_abandoned(app):
    """check_pending_upload deletes an abandoned pending upload when it's very old"""
    with app.app_context():
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, datetime(1999, 1, 1), 'us-west-2')
        session = app.db.session('relengapi')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted


@moto.mock_s3
@test_context
def test_check_pending_upload_bad_region(app):
    """check_pending_upload deletes a pending upload with a bad region"""
    with app.app_context(), set_time():
        expires = time.now() - timedelta(seconds=90)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-1')
        session = app.db.session('relengapi')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted


@moto.mock_s3
@test_context
def test_check_pending_upload_no_upload(app):
    """check_pending_upload leaves the PU in place if the upload is
    not complete"""
    with app.app_context(), set_time():
        expires = time.now() - timedelta(seconds=90)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        session = app.db.session('relengapi')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        # PU has not been deleted
        assert tables.PendingUpload.query.first().file.sha512 == DATA_DIGEST


@moto.mock_s3
@test_context
def test_check_pending_upload_not_valid(app):
    """check_pending_upload deletes the PU and the key if the upload is
    invalid."""
    with app.app_context(), set_time():
        expires = time.now() - timedelta(seconds=90)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        make_key(app, 'us-west-2', 'tt-usw2', DATA_KEY, 'xxx')
        session = app.db.session('relengapi')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted
        assert not key_exists(app, 'us-west-2', 'tt-usw2', DATA_KEY)


@moto.mock_s3
@test_context
def test_check_pending_upload_race(app):
    """If check_pending_upload fails to add a file instance because it already
    exists, as might happen when the function races with itself, the function
    still succeeds."""
    with app.app_context(), set_time():
        expires = time.now() - timedelta(seconds=90)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        make_key(app, 'us-west-2', 'tt-usw2', DATA_KEY, DATA)
        session = app.db.session('relengapi')

        def test_shim():
            session.add(tables.FileInstance(file=file_row, region='us-west-2'))
            session.commit()
        grooming.check_pending_upload(session, pu_row, _test_shim=test_shim)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted
        eq_(len(tables.File.query.first().instances), 1)  # FileInstance exists
        assert key_exists(app, 'us-west-2', 'tt-usw2', DATA_KEY)


@moto.mock_s3
@test_context
def test_check_pending_upload_success(app):
    """check_pending_upload deletes the PU and adds a FileInstance if valid"""
    with app.app_context(), set_time():
        expires = time.now() - timedelta(seconds=90)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        make_key(app, 'us-west-2', 'tt-usw2', DATA_KEY, DATA)
        session = app.db.session('relengapi')
        grooming.check_pending_upload(session, pu_row)
        session.commit()
        eq_(tables.PendingUpload.query.all(), [])  # PU is deleted
        eq_(len(tables.File.query.first().instances), 1)  # FileInstance exists
        assert key_exists(app, 'us-west-2', 'tt-usw2', DATA_KEY)


@test_context
def test_check_pending_uploads(app):
    """check_pending_uploads calls check_pending_upload for each PU"""
    with app.app_context(), set_time():
        expires = time.now() - timedelta(seconds=90)
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
    with app.app_context(), set_time():
        expires = time.now() - timedelta(seconds=90)
        pu_row, file_row = add_pending_upload_and_file_row(
            len(DATA), DATA_DIGEST, expires, 'us-west-2')
        with mock.patch('relengapi.blueprints.tooltool.grooming.check_pending_upload') as cpu:
            pending_uploads = []
            cpu.side_effect = lambda sess, pu: pending_uploads.append(pu)
            grooming.check_file_pending_uploads(DATA_DIGEST)
            assert len(pending_uploads) == 1


@test_context
def test_replicate(app):
    """The periodic replication only tries to replicate files with at least one
    but not a full set of instances."""
    with app.app_context():
        regions = sorted(cfg['TOOLTOOL_REGIONS'])
        files = []
        for i in range(0, len(regions) + 1):
            data = os.urandom((i + 1) * 1024)
            data_digest = hashlib.sha512(data).hexdigest()
            files.append((add_file_row(len(data),
                                       data_digest,
                                       instances=regions[:i]),
                          0 < i < len(regions)))
        with mock.patch('relengapi.blueprints.tooltool.grooming.replicate_file') as rep_file:
            grooming.replicate(None)
        replicated_files = [call[1][1] for call in rep_file.mock_calls]
        exp_replicated_files = [
            file for file, should_replicate in files if should_replicate]
        eq_(replicated_files, exp_replicated_files)


@test_context
def test_replicate_file_no_instances(app):
    """When a file has no instances matching the config, replicate_file does
    nothing."""
    with app.app_context():
        # us-west-1 isn't in cfg['TOOLTOOL_REGIONS']
        file = add_file_row(len(DATA), DATA_DIGEST, instances=['us-west-1'])
        grooming.replicate_file(app.db.session('relengapi'), file)
    assert_file_instances(app, DATA_DIGEST, ['us-west-1'])


@moto.mock_s3
@test_context
def test_replicate_file_already_exists(app):
    """If a target object already exists in S3 during replication, it is
    deleted rather than being trusted to be correct."""
    with app.app_context():
        file = add_file_row(len(DATA), DATA_DIGEST, instances=['us-east-1'])
        make_key(app, 'us-east-1', 'tt-use1', util.keyname(DATA_DIGEST), DATA)
        make_key(app, 'us-west-2', 'tt-usw2', util.keyname(DATA_DIGEST), "BAD")
        grooming.replicate_file(app.db.session('relengapi'), file)
    assert_file_instances(app, DATA_DIGEST, ['us-east-1', 'us-west-2'])
    assert key_exists(app, 'us-east-1', 'tt-use1', util.keyname(DATA_DIGEST))
    k = key_exists(app, 'us-west-2', 'tt-usw2', util.keyname(DATA_DIGEST))
    eq_(k.get_contents_as_string(), DATA)  # not "BAD"


@moto.mock_s3
@test_context
def test_replicate_file(app):
    """Replicating a file initiates copy operations from regions where the file
    exists to regions where it does not."""
    with app.app_context():
        file = add_file_row(len(DATA), DATA_DIGEST, instances=['us-east-1'])
        make_key(app, 'us-east-1', 'tt-use1', util.keyname(DATA_DIGEST), DATA)
        make_bucket(app, 'us-west-2', 'tt-usw2')
        grooming.replicate_file(app.db.session('relengapi'), file)
    assert_file_instances(app, DATA_DIGEST, ['us-east-1', 'us-west-2'])
    assert key_exists(app, 'us-east-1', 'tt-use1', util.keyname(DATA_DIGEST))
    assert key_exists(app, 'us-west-2', 'tt-usw2', util.keyname(DATA_DIGEST))


@moto.mock_s3
@test_context
def test_replicate_file_race(app):
    """If, while replicating a file, another replication completes and the
    subsequent database insert fails, the replication function nonetheless
    succeeds."""
    with app.app_context():
        file = add_file_row(len(DATA), DATA_DIGEST, instances=['us-east-1'])
        make_key(app, 'us-east-1', 'tt-use1', util.keyname(DATA_DIGEST), DATA)
        make_bucket(app, 'us-west-2', 'tt-usw2')

        def test_shim():
            session = app.db.session('relengapi')
            session.add(tables.FileInstance(file=file, region='us-west-2'))
            session.commit()
        grooming.replicate_file(app.db.session('relengapi'), file,
                                _test_shim=test_shim)
    assert_file_instances(app, DATA_DIGEST, ['us-east-1', 'us-west-2'])
