# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import boto.exception
import datetime
import hashlib
import json
import mock
import moto
import pytz
import time
import urlparse

from contextlib import contextmanager
from nose.tools import eq_
from relengapi.blueprints import tooltool
from relengapi.blueprints.tooltool import tables
from relengapi.blueprints.tooltool import util
from relengapi.lib import auth
from relengapi.lib import time as relengapi_time
from relengapi.lib.permissions import p
from relengapi.lib.testing.context import TestContext


def userperms(perms, email='me'):
    u = auth.HumanUser(email)
    u._permissions = set(perms)
    return u

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
test_context = TestContext(config=cfg, databases=['relengapi'],
                           user=userperms([p.tooltool.download.public,
                                           p.tooltool.upload.public]))

allow_anon_cfg = cfg.copy()
allow_anon_cfg['TOOLTOOL_ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD'] = True

ONE = '1\n'
ONE_DIGEST = hashlib.sha512(ONE).hexdigest()
TWO = '22\n'
TWO_DIGEST = hashlib.sha512(TWO).hexdigest()

NOW = 1425592922


def mkbatch(message="a batch"):
    return {
        'message': message,
        'files': {
            'one': {
                'algorithm': 'sha512',
                'size': len(ONE),
                'digest': ONE_DIGEST,
                'visibility': 'public',
            },
        },
    }


def upload_batch(client, batch, region=None):
    region_arg = '?region={}'.format(region) if region else ''
    return client.post_json('/tooltool/upload' + region_arg, data=batch)


def add_file_to_db(app, content, regions=['us-east-1'],
                   pending_regions=[], visibility='public'):
    with app.app_context():
        session = app.db.session('relengapi')
        file_row = tables.File(size=len(content),
                               visibility=visibility,
                               sha512=hashlib.sha512(content).hexdigest())
        session.add(file_row)
        session.commit()
        for region in regions:
            session.add(tables.FileInstance(
                file_id=file_row.id, region=region))
        for region in pending_regions:
            session.add(tables.PendingUpload(
                file=file_row, region=region,
                expires=relengapi_time.now() + datetime.timedelta(seconds=60)))
        session.commit()

        return file_row


def add_batch_to_db(app, author, message, files):
    with app.app_context():
        session = app.db.session('relengapi')
        batch = tables.Batch(author=author, message=message,
                             uploaded=relengapi_time.now())
        session.add(batch)
        for filename, file in files.iteritems():
            session.add(tables.BatchFile(filename=filename, batch=batch, file=file))
        session.commit()
        return batch


def add_file_to_s3(app, content, region='us-east-1'):
    with app.app_context():
        conn = app.aws.connect_to('s3', region)
        bucket_name = cfg['TOOLTOOL_REGIONS'][region]
        try:
            conn.head_bucket(bucket_name)
        except boto.exception.S3ResponseError:
            conn.create_bucket(bucket_name)
        bucket = conn.get_bucket(bucket_name)
        key_name = util.keyname(hashlib.sha512(content).hexdigest())
        key = bucket.new_key(key_name)
        key.set_contents_from_string(content)


@contextmanager
def set_time(now=NOW):
    with mock.patch('time.time') as fake_time, \
            mock.patch('relengapi.lib.time.now') as fake_now:
        fake_time.return_value = now
        fake_now.return_value = datetime.datetime.fromtimestamp(now, pytz.UTC)
        yield


@contextmanager
def not_so_random_choice():
    with mock.patch('random.choice') as choice:
        choice.side_effect = lambda seq: sorted(seq)[0]
        yield


def assert_signed_302(resp, digest, method='GET', region=None,
                      expires_in=60, bucket=None):
    eq_(resp.status_code, 302)
    url = resp.headers['Location']
    assert_signed_url(url, digest, method=method, region=region,
                      expires_in=expires_in, bucket=bucket)


def assert_signed_url(url, digest, method='GET', region=None,
                      expires_in=60, bucket=None):
    region = region or 'us-east-1'
    bucket = bucket or cfg['TOOLTOOL_REGIONS'][region]
    if region == 'us-east-1':
        host = '{}.s3.amazonaws.com'.format(bucket)
    else:
        host = '{}.s3-{}.amazonaws.com'.format(bucket, region)
    url = urlparse.urlparse(url)
    eq_(url.scheme, 'https')
    eq_(url.netloc, host)
    eq_(url.path, '/' + util.keyname(digest))
    query = urlparse.parse_qs(url.query)
    assert 'Signature' in query
    # sadly, headers are not represented in the URL
    eq_(query['AWSAccessKeyId'][0], 'aa')
    eq_(int(query['Expires'][0]), time.time() + expires_in)


def assert_batch_response(resp, author='me', message='a batch',
                          files={}):
    eq_(resp.status_code, 200, resp.data)
    result = json.loads(resp.data)['result']
    eq_(result['author'], author)
    # TODO: eq_(result[
    eq_(result['message'], message)
    eq_(set(result['files']), set(files))
    for name, file in files.iteritems():
        for k, v in file.iteritems():
            eq_(result['files'][name][k], v,
                "result['files'][{}][{}] {} != {}".format(
                    name, k, result['files'][name][k], v))
    return result


def assert_batch_row(app, id, author='me', message='a batch', files=[]):
    with app.app_context():
        tbl = tables.Batch
        batch_row = tbl.query.filter(tbl.id == id).first()
    eq_(batch_row.author, author)
    eq_(batch_row.message, message)
    got_files = [(n, f.size, f.sha512, sorted(i.region for i in f.instances))
                 for n, f in batch_row.files.iteritems()]
    eq_(sorted(got_files), sorted(files))


def assert_pending_upload(app, digest, region, expires=None):
    with app.app_context():
        tbl = tables.File
        file = tbl.query.filter(tbl.sha512 == digest).first()
        regions = [pu.region for pu in file.pending_uploads]
        assert region in regions, regions
        if expires:
            eq_(pu.expires, expires)


def assert_no_upload_rows(app):
    with app.app_context():
        eq_(tables.Batch.query.all(), [])
        eq_(tables.PendingUpload.query.all(), [])


def assert_file_response(resp, content, visibility='public', instances=['us-east-1']):
    eq_(resp.status_code, 200)
    exp = {
        "algorithm": "sha512",
        "digest": hashlib.sha512(content).hexdigest(),
        "size": len(content),
        "visibility": visibility,
        'instances': instances,
    }
    eq_(json.loads(resp.data)['result'], exp, resp.data)


def do_patch(client, algo, digest, ops):
    return client.open(method='PATCH',
                       path='/tooltool/file/sha512/{}'.format(digest),
                       headers=[('Content-Type', 'application/json')],
                       data=json.dumps(ops))


# tests


def test_is_valid_sha512():
    """is_valid_sha512 recgnizes valid digests and rejects others"""
    assert tooltool.is_valid_sha512(ONE_DIGEST)
    assert tooltool.is_valid_sha512(TWO_DIGEST)
    assert not tooltool.is_valid_sha512(ONE_DIGEST[-1])
    assert not tooltool.is_valid_sha512(ONE_DIGEST + 'a')
    assert not tooltool.is_valid_sha512('a' + ONE_DIGEST)
    assert not tooltool.is_valid_sha512('j' * 128)


@test_context
def test_ui(client):
    """The root of the blueprint renders an angular HTML page"""
    assert 'angular' in client.get('/tooltool/').data


@moto.mock_s3
@test_context
def test_upload_batch_empty_message(app, client):
    """A POST to /upload with an empty message is rejected."""
    batch = mkbatch()
    batch['message'] = ''
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 400)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context
def test_upload_batch_author(app, client):
    """A POST to /upload with an author is rejected."""
    batch = mkbatch()
    batch['author'] = 'me'  # matches authentication
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 400)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context.specialize(user=auth.AnonymousUser())
def test_upload_batch_no_user(app, client):
    """A POST to /upload with non-user-associated authentication fails"""
    batch = mkbatch()
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 400)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context
def test_upload_batch_empty_files(app, client):
    """A POST to /upload with no files is rejected."""
    batch = mkbatch()
    batch['files'] = {}
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 400)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context
def test_upload_batch_bad_algo(app, client):
    """A POST to /upload with an algorithm that is not sha512 is rejected."""
    batch = mkbatch()
    batch['files']['one']['algorithm'] = 'md4'
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 400)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context
def test_upload_batch_bad_digest(app, client):
    """A POST to /upload with a bad sha512 digest is rejected."""
    batch = mkbatch()
    batch['files']['one']['digest'] = 'x' * 128
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 400)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context
def test_upload_batch_bad_size(app, client):
    """A POST to /upload with a file with the same digest and a different length
    is rejected"""
    batch = mkbatch()
    batch['files']['one']['size'] *= 2  # that ain't right!

    add_file_to_db(app, ONE)
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 400)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context.specialize(user=userperms([]))
def test_upload_batch_no_permissions(app, client):
    """A POST to /upload of a public file without permission to upload fails
    with 403."""
    batch = mkbatch()
    add_file_to_db(app, ONE)
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 403, resp.data)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context
def test_upload_batch_mixed_visibility_no_permissions(app, client):
    """A POST to /upload of public and internal files fails with 403 if the
    user only has permission to upload public files."""
    batch = mkbatch()
    batch['files']['two'] = {
        'algorithm': 'sha512',
        'size': len(TWO),
        'digest': TWO_DIGEST,
        'visibility': 'internal',
    }
    add_file_to_db(app, ONE)
    resp = upload_batch(client, batch)
    eq_(resp.status_code, 403, resp.data)
    assert_no_upload_rows(app)


@moto.mock_s3
@test_context
def test_upload_batch_success_fresh(client, app):
    """A POST to /upload with a good batch succeeds, returns signed URLs expiring
    in one hour, and inserts the new batch into the DB with links to files, but
    no instances, and inserts a pending upload row."""
    batch = mkbatch()
    with set_time():
        with not_so_random_choice():
            resp = upload_batch(client, batch)
        result = assert_batch_response(resp, files={
            'one': {'algorithm': 'sha512',
                    'size': len(ONE),
                    'digest': ONE_DIGEST}})
        assert_signed_url(result['files']['one']['put_url'], ONE_DIGEST,
                          method='PUT', expires_in=60)

    assert_batch_row(
        app, result['id'], files=[('one', len(ONE), ONE_DIGEST, [])])
    assert_pending_upload(app, ONE_DIGEST, 'us-east-1')


@moto.mock_s3
@test_context
def test_upload_batch_success_existing_pending_upload(client, app):
    """A successful POST to /upload updates the 'expires' column of any relevant
    pending uploads."""
    with set_time(NOW - 30):
        add_file_to_db(app, ONE, regions=[], pending_regions=['us-east-1'])
    batch = mkbatch()
    with set_time():
        with not_so_random_choice():
            resp = upload_batch(client, batch)
        result = assert_batch_response(resp, files={
            'one': {'algorithm': 'sha512',
                    'size': len(ONE),
                    'digest': ONE_DIGEST}})
        assert_signed_url(result['files']['one']['put_url'], ONE_DIGEST,
                          method='PUT', expires_in=60)
        assert_pending_upload(
            app, ONE_DIGEST, 'us-east-1',
            expires=relengapi_time.now() + datetime.timedelta(seconds=60))
        assert_batch_row(
            app, result['id'], files=[('one', len(ONE), ONE_DIGEST, [])])


@moto.mock_s3
@test_context
def test_upload_batch_success_no_instances(client, app):
    """A POST to /upload with a batch containing a file that already exists, but
    has no instances, succeeds, returns signed URLs expiring in one hour,
    inserts the new batch into the DB with links to files, but no instances,
    and inserts a pending upload row.  This could occur when, for example,
    re-trying a failed upload."""
    batch = mkbatch()
    add_file_to_db(app, ONE, regions=[])
    with set_time():
        with not_so_random_choice():
            resp = upload_batch(client, batch)
        result = assert_batch_response(resp, files={
            'one': {'algorithm': 'sha512',
                    'size': len(ONE),
                    'digest': ONE_DIGEST}})
        assert_signed_url(result['files']['one']['put_url'], ONE_DIGEST,
                          method='PUT', expires_in=60)

    assert_batch_row(
        app, result['id'], files=[('one', len(ONE), ONE_DIGEST, [])])
    assert_pending_upload(app, ONE_DIGEST, 'us-east-1')


@moto.mock_s3
@test_context
def test_upload_batch_success_some_existing_files(client, app):
    """A POST to /upload with a good batch containing some files already present
    succeeds, returns signed URLs expiring in one hour, and inserts the new
    batch into the DB with links to files, but no instances.  Also, the
    ``region`` query parameter selects a preferred region."""
    batch = mkbatch()
    batch['files']['two'] = {
        'algorithm': 'sha512',
        'size': len(TWO),
        'digest': TWO_DIGEST,
        'visibility': 'public',
    }

    # make sure ONE is already in the DB with at least once instance
    add_file_to_db(app, ONE, regions=['us-east-1'])

    with set_time():
        resp = upload_batch(client, batch, region='us-west-2')
        result = assert_batch_response(resp, files={
            'one': {'algorithm': 'sha512',
                    'size': len(ONE),
                    'digest': ONE_DIGEST},
            'two': {'algorithm': 'sha512',
                    'size': len(TWO),
                    'digest': TWO_DIGEST},
        })
        # no put_url for the existing file
        assert 'put_url' not in result['files']['one']
        assert_signed_url(result['files']['two']['put_url'], TWO_DIGEST,
                          method='PUT', expires_in=60, region='us-west-2')

    assert_batch_row(app, result['id'],
                     files=[
                         ('one', len(ONE), ONE_DIGEST, ['us-east-1']),
                         ('two', len(TWO), TWO_DIGEST, []),
    ])
    assert_pending_upload(app, TWO_DIGEST, 'us-west-2')


@test_context
def test_upload_change_visibility(client, app):
    """Uploading a file that already exists with a different visibility level
    fails with 400, even if there are no instances."""
    batch = mkbatch()
    batch['files']['one']['visibility'] = 'public'
    add_file_to_db(app, ONE, regions=[], visibility='internal')

    with set_time():
        resp = upload_batch(client, batch, region='us-west-2')
        eq_(resp.status_code, 400, resp.data)
    assert_no_upload_rows(app)


@test_context
def test_upload_complete(client, app):
    """GET /upload/complete/<digest> when the pending upload has expired causes
    a delayed call to check_file_pending_uploads and returns 202"""
    with mock.patch('relengapi.blueprints.tooltool.grooming.check_file_pending_uploads') as cfpu:
        with set_time(NOW - tooltool.UPLOAD_EXPIRES_IN - 1):
            add_file_to_db(app, ONE, regions=[], pending_regions=['us-east-1'])
        with set_time(NOW):
            resp = client.get('/tooltool/upload/complete/sha512/{}'.format(ONE_DIGEST))
        eq_(resp.status_code, 202, resp.data)
        cfpu.delay.assert_called_with(ONE_DIGEST)


@test_context
def test_upload_complete_not_expired(client, app):
    """GET /upload/complete/<digest> when the pending upload has not expired returns
    409 with a header giving the time until expiration."""
    with mock.patch('relengapi.blueprints.tooltool.grooming.check_file_pending_uploads') as cfpu:
        with set_time(NOW - tooltool.UPLOAD_EXPIRES_IN + 5):
            add_file_to_db(app, ONE, regions=[], pending_regions=['us-east-1'])
        with set_time(NOW):
            resp = client.get('/tooltool/upload/complete/sha512/{}'.format(ONE_DIGEST))
        eq_(resp.status_code, 409, resp.data)
        eq_(resp.headers.get('x-retry-after'), '6')  # 5 seconds + 1
        eq_(cfpu.delay.mock_calls, [])


@test_context
def test_upload_complete_bad_digest(client, app):
    """GET /upload/complete/<digest> with a bad digest returns 400"""
    with mock.patch('relengapi.blueprints.tooltool.grooming.check_file_pending_uploads') as cfpu:
        resp = client.get('/tooltool/upload/complete/sha512/xyz')
        eq_(resp.status_code, 400, resp.data)
        cfpu.delay.assert_has_calls([])


@moto.mock_s3
@test_context
def test_download_file_no_such(app, client):
    """Getting /sha512/<digest> for a file that does not exist returns 404"""
    resp = client.get('/tooltool/sha512/{}'.format(ONE_DIGEST))
    eq_(resp.status_code, 404)


@moto.mock_s3
@test_context
def test_download_file_invalid_digest(app, client):
    """Getting /sha512/<digest> for an invalid digest returns 400"""
    resp = client.get('/tooltool/sha512/abcd')
    eq_(resp.status_code, 400)


@moto.mock_s3
@test_context
def test_download_file_no_instances(app, client):
    """Getting /sha512/<digest> for a file that exists but has no instances
    returns 404"""
    add_file_to_db(app, ONE, regions=[])
    resp = client.get('/tooltool/sha512/{}'.format(ONE_DIGEST))
    eq_(resp.status_code, 404)


@moto.mock_s3
@test_context
def test_download_file_no_permission(app, client):
    """Getting /sha512/<digest> for a file with a visibility the user doesn't
    have permission for returns 404."""
    add_file_to_db(app, ONE, visibility='internal')
    resp = client.get('/tooltool/sha512/{}'.format(ONE_DIGEST))
    eq_(resp.status_code, 403)


@moto.mock_s3
@test_context
def test_download_file_exists(app, client):
    """Getting /sha512/<digest> for an exisitng file returns a 302 redirect to
    a signed URL in a region where it exists."""
    add_file_to_db(app, ONE, regions=['us-west-2', 'us-east-1'])
    with set_time():
        with not_so_random_choice():
            resp = client.get('/tooltool/sha512/{}'.format(ONE_DIGEST))
        assert_signed_302(resp, ONE_DIGEST, region='us-east-1')


@moto.mock_s3
@test_context.specialize(user=None)
def test_download_file_anonymous_forbidden(app, client):
    """Anonymously downloading a public file is forbidden if
    TOOLTOOL_ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD is not set"""
    add_file_to_db(app, ONE, regions=['us-west-2'], visibility='public')
    resp = client.get('/tooltool/sha512/{}'.format(ONE_DIGEST))
    eq_(resp.status_code, 403)


@moto.mock_s3
@test_context.specialize(user=None, config=allow_anon_cfg)
def test_download_file_anonymous_nonpublic_forbidden(app, client):
    """Anonymously downloading an i nternal file is forbidden even if
    TOOLTOOL_ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD is set"""
    add_file_to_db(app, ONE, regions=['us-west-2'], visibility='internal')
    resp = client.get('/tooltool/sha512/{}'.format(ONE_DIGEST))
    eq_(resp.status_code, 403)


@moto.mock_s3
@test_context.specialize(user=None, config=allow_anon_cfg)
def test_download_file_anonymous_allowed(app, client):
    """Anonymously downloading a public file is allowed if
    TOOLTOOL_ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD is set"""
    add_file_to_db(app, ONE, regions=['us-west-2'], visibility='public')
    resp = client.get('/tooltool/sha512/{}'.format(ONE_DIGEST))
    eq_(resp.status_code, 302)


@moto.mock_s3
@test_context
def test_download_file_exists_not_in_preferred_region(app, client):
    """Getting /sha512/<digest>?region=.. for an exisitng file that does not
    exist in the requested region returns a signed URL for a region where the
    file does exist."""
    add_file_to_db(app, ONE, regions=['us-west-2'])
    with set_time():
        resp = client.get(
            '/tooltool/sha512/{}?region=us-east-1'.format(ONE_DIGEST))
        assert_signed_302(resp, ONE_DIGEST, region='us-west-2')


@moto.mock_s3
@test_context
def test_download_file_exists_region_choice(app, client):
    """Getting /sha512/<digest> for an exisitng file returns a 302 redirect to
    a signed URL in the region where it exists."""
    add_file_to_db(app, ONE, regions=['us-west-2', 'us-east-1'])
    with set_time():
        resp = client.get(
            '/tooltool/sha512/{}?region=us-west-2'.format(ONE_DIGEST))
        assert_signed_302(resp, ONE_DIGEST, region='us-west-2')


@moto.mock_s3
@test_context
def test_search_batches(app, client):
    with set_time():
        f1 = add_file_to_db(app, ONE)
        f1j = {
            "algorithm": "sha512",
            "digest": ONE_DIGEST,
            "size": len(ONE),
            "visibility": "public"
        }
        f2 = add_file_to_db(app, TWO)
        f2j = {
            "algorithm": "sha512",
            "digest": TWO_DIGEST,
            "size": len(TWO),
            "visibility": "public"
        }
        add_batch_to_db(
            app, 'me@me.com', 'first batch', {'one': f1})
        b1j = {
            "author": "me@me.com",
            "uploaded": "2015-03-05T22:02:02+00:00",
            "files": {"one": f1j},
            "id": 1,
            "message": "first batch"
        }
        add_batch_to_db(
            app, 'me@me.com', 'second batch', {'two': f2})
        b2j = {
            "author": "me@me.com",
            "uploaded": "2015-03-05T22:02:02+00:00",
            "files": {"two": f2j},
            "id": 2,
            "message": "second batch"
        }
        add_batch_to_db(
            app, 'you@you.com', 'third batch', {'1': f1, '2': f2})
        b3j = {
            "author": "you@you.com",
            "uploaded": "2015-03-05T22:02:02+00:00",
            "files": {"1": f1j, "2": f2j},
            "id": 3,
            "message": "third batch"
        }

    for q, exp_batches in [
        ('me', [b1j, b2j]),
        ('ou@y', [b3j]),
        ('econd batc', [b2j]),
        ('', [b1j, b2j, b3j]),
    ]:
        resp = client.get('/tooltool/upload?q=' + q)
        eq_(resp.status_code, 200, resp.data)
        eq_(sorted(json.loads(resp.data)['result']), sorted(exp_batches),
            "got: {}\nexp: {}".format(resp.data, exp_batches))


@moto.mock_s3
@test_context
def test_get_batch_not_found(client):
    resp = client.get('/tooltool/upload/99')
    eq_(resp.status_code, 404, resp.data)


@moto.mock_s3
@test_context
def test_get_batch_found(client):
    batch = mkbatch()
    batch['files']['two'] = {
        'algorithm': 'sha512',
        'size': len(TWO),
        'digest': TWO_DIGEST,
        'visibility': 'public',
    }
    with set_time():
        resp = upload_batch(client, batch)
        eq_(resp.status_code, 200, resp.data)
    resp = client.get('/tooltool/upload/1')
    eq_(resp.status_code, 200, resp.data)
    eq_(json.loads(resp.data)['result'], {
        "author": "me",
        "uploaded": "2015-03-05T22:02:02+00:00",
        "files": {
            "one": {
                "algorithm": "sha512",
                "digest": ONE_DIGEST,
                "size": len(ONE),
                "visibility": "public"
            },
            "two": {
                "algorithm": "sha512",
                "digest": TWO_DIGEST,
                "size": len(TWO),
                "visibility": "public"
            }
        },
        "id": 1,
        "message": "a batch"
    }, resp.data)


@test_context
def test_get_files(app, client):
    """GETs to /file?q=.. return appropriately filtered files."""
    f1 = add_file_to_db(app, ONE)
    f1j = {
        "algorithm": "sha512",
        "digest": ONE_DIGEST,
        "size": len(ONE),
        "visibility": "public"
    }
    f2 = add_file_to_db(app, TWO)
    f2j = {
        "algorithm": "sha512",
        "digest": TWO_DIGEST,
        "size": len(TWO),
        "visibility": "public"
    }
    add_batch_to_db(
        app, 'me@me.com', 'first batch', {'one': f1})
    add_batch_to_db(
        app, 'me@me.com', 'second batch', {'two': f2})
    add_batch_to_db(
        app, 'you@you.com', 'third batch', {'1': f1, '2': f2})

    for q, exp_files in [
        ('one', [f1j]),
        ('2', [f2j]),
        (ONE_DIGEST[:8], [f1j]),
        (ONE_DIGEST[10:20], []),  # digests are prefix-only
        ('', [f1j, f2j]),
    ]:
        resp = client.get('/tooltool/file?q=' + q)
        eq_(resp.status_code, 200)
        eq_(sorted(json.loads(resp.data)['result']), sorted(exp_files))


@test_context
def test_get_file_bad_algo(client):
    """A GET to /file/<algo>/<digest> with an unknown algorithm fails with 404"""
    eq_(client.get('/tooltool/file/md4/abcd').status_code, 404)


@test_context
def test_get_file_not_found(client):
    """A GET to /file/sha512/<digest> with an unknown digest fails with 404"""
    eq_(client.get(
        '/tooltool/file/sha512/{}'.format(ONE_DIGEST)).status_code, 404)


@test_context
def test_get_file_success(app, client):
    """A GET to /file/sha512/<digest> with an known digest returns the file"""
    add_file_to_db(app, ONE)
    resp = client.get('/tooltool/file/sha512/{}'.format(ONE_DIGEST))
    assert_file_response(resp, ONE)


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_patch_no_such(app, client):
    """A PATCH to /file/<a>/<d> that doesn't exist returns 404."""
    resp = do_patch(client, 'sha512', ONE_DIGEST, [{'op': 'delete_instances'}])
    eq_(resp.status_code, 404)


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_patch_bad_algo(app, client):
    """A PATCH to /file/<a>/<d> with a bad algorithm returns 404."""
    resp = do_patch(client, 'md3', ONE_DIGEST, [{'op': 'delete_instances'}])
    eq_(resp.status_code, 404)


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_patch_no_op(app, client):
    """A PATCH to /file/<a>/<d> with change containing no 'op' returns 400."""
    add_file_to_db(app, ONE)
    resp = do_patch(client, 'sha512', ONE_DIGEST, [{'pop': 'snap'}])
    eq_(resp.status_code, 400)


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_patch_bad_op(app, client):
    """A PATCH to /file/<a>/<d> with change containing a bad 'op' returns 400."""
    add_file_to_db(app, ONE)
    resp = do_patch(client, 'sha512', ONE_DIGEST, [{'op': 'hop'}])
    eq_(resp.status_code, 400)


@moto.mock_s3
@test_context
def test_patch_no_perms(app, client):
    """A PATCH to /file/<a>/<d> without tooltool.manage fails with 403"""
    add_file_to_db(app, ONE, regions=['us-east-1'])
    resp = do_patch(client, 'sha512', ONE_DIGEST, [{'op': 'delete_instances'}])
    eq_(resp.status_code, 403)


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_delete_instances_success_no_instances(app, client):
    """A PATCH with op=delete_instances succeeds when there are no instances."""
    add_file_to_db(app, ONE, regions=[])
    resp = do_patch(client, 'sha512', ONE_DIGEST, [{'op': 'delete_instances'}])
    assert_file_response(resp, ONE, instances=[])


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_delete_instances_success(app, client):
    """A PATCH with op=delete_instances deletes its instances."""
    add_file_to_db(app, ONE, regions=['us-east-1'])
    add_file_to_s3(app, ONE, region='us-east-1')
    resp = do_patch(client, 'sha512', ONE_DIGEST, [{'op': 'delete_instances'}])
    assert_file_response(resp, ONE, instances=[])
    with app.app_context():
        # ensure instances are gone from the DB
        f = tables.File.query.first()
        eq_(f.instances, [])

        # and from S3
        conn = app.aws.connect_to('s3', 'us-east-1')
        key = conn.get_bucket(
            'tt-use1').get_key(util.keyname(ONE_DIGEST))
        assert not key, "key still exists"


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_set_visibility_invalid_vis(app, client):
    """A PATCH with op=set_visibility and an invalid visibility fails."""
    add_file_to_db(app, ONE, regions=[])
    resp = do_patch(client, 'sha512', ONE_DIGEST,
                    [{'op': 'set_visibility', 'visibility': '5-eyes'}])
    eq_(resp.status_code, 400)


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_set_visibility_success(app, client):
    """A PATCH with op=set_visibility updates the file's visibility."""
    add_file_to_db(app, ONE, visibility='public')
    resp = do_patch(client, 'sha512', ONE_DIGEST,
                    [{'op': 'set_visibility', 'visibility': 'internal'}])
    assert_file_response(resp, ONE, visibility='internal')
    with app.app_context():
        f = tables.File.query.first()
        eq_(f.visibility, 'internal')


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_set_visibility_success_no_change(app, client):
    """A PATCH with op=set_visibility with the existing visibility succeeds."""
    add_file_to_db(app, ONE, visibility='internal')
    resp = do_patch(client, 'sha512', ONE_DIGEST,
                    [{'op': 'set_visibility', 'visibility': 'internal'}])
    assert_file_response(resp, ONE, visibility='internal')
    with app.app_context():
        f = tables.File.query.first()
        eq_(f.visibility, 'internal')


@moto.mock_s3
@test_context.specialize(user=userperms([p.tooltool.manage]))
def test_multi_op_patch(app, client):
    """A PATCH with multiple ops performs all of them."""
    add_file_to_db(
        app, ONE, visibility='internal', regions=['us-east-1', 'us-west-2'])
    add_file_to_s3(app, ONE, region='us-east-1')
    add_file_to_s3(app, ONE, region='us-west-2')
    resp = do_patch(client, 'sha512', ONE_DIGEST, [
        {'op': 'set_visibility', 'visibility': 'public'},
        {'op': 'delete_instances'},
    ])
    assert_file_response(resp, ONE, visibility='public', instances=[])
    with app.app_context():
        f = tables.File.query.first()
        eq_(f.visibility, 'public')
        eq_(f.instances, [])
