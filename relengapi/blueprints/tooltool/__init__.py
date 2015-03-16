# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import random
import re

from flask import Blueprint
from flask import current_app
from flask import g
from flask import redirect
from flask.ext.login import current_user
from relengapi.blueprints.tooltool import grooming
from relengapi.blueprints.tooltool import tables
from relengapi.blueprints.tooltool import types
from relengapi.lib import api
from relengapi.lib import time
from relengapi.lib.permissions import p
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import NotFound

metadata = {
    'repository_of_record': 'https://git.mozilla.org/?p=build/tooltool.git;a=summary',
    'bug_report_url': 'http://goo.gl/XZpyie',  # bugzilla saved new-bug form
}

bp = Blueprint('tooltool', __name__)

is_valid_sha512 = re.compile(r'^[0-9a-f]{128}$').match

p.tooltool.download.public.doc("Download PUBLIC files from tooltool")
p.tooltool.upload.public.doc("Upload PUBLIC files to tooltool")
# note that internal does not imply public; that's up to the user.
p.tooltool.download.internal.doc("Download INTERNAL files from tooltool")
p.tooltool.upload.internal.doc("Upload INTERNAL files to tooltool")
p.tooltool.manage.doc("Manage tooltool files, including deleting and changing visibility levels")

GET_EXPIRES_IN = 60
UPLOAD_EXPIRES_IN = 3600


def get_region_and_bucket(region_arg):
    cfg = current_app.config['TOOLTOOL_REGIONS']
    if region_arg and region_arg in cfg:
        return region_arg, cfg[region_arg]
    # no region specified, so return one at random
    return random.choice(cfg.items())


@bp.route('/upload')
@api.apimethod([types.UploadBatch])
def list_batches():
    """Get a list of all upload batches."""
    # TODO: eager load the files for these batches
    # TODO: ?digest=.. to filter batches containing a digest
    # TODO: ?filename=.. to filter batches containing a digest
    # TODO: ?author=.. to filter batches to a particular author
    # TODO: ?search=.. to search author, message, digest, and filenames
    return [row.to_json() for row in tables.Batch.query.all()]


@bp.route('/upload/<int:id>')
@api.apimethod(types.UploadBatch, int)
def get_batch(id):
    """Get a specific upload batch by id."""
    row = tables.Batch.query.filter(tables.Batch.id == id).first()
    if not row:
        raise NotFound
    return row.to_json()


@bp.route('/upload', methods=['PUT'])
@api.apimethod(types.UploadBatch, unicode, body=types.UploadBatch)
def upload_batch(region=None, body=None):
    """Create a new upload batch.  The response object will contain a
    ``put_url`` for each file which needs to be uploaded -- which may not be
    all!  The caller is then responsible for uploading to those URLs.  The
    resulting signed URLs are valid for one hour, so uploads should begin
    within that timeframe.  Consider using Amazon's MD5-verification
    capabilities to ensure that the uploaded files are transferred correctly,
    although the tooltool server will verify the integrity anyway.

    The query argument ``region=us-west-1`` indicates a preference for URLs
    in that region, although if the region is not available then URLs in
    other regions may be returned."""
    region, bucket = get_region_and_bucket(region)

    if not body.message:
        raise BadRequest("message must be non-empty")

    if not body.files:
        raise BadRequest("a batch must include at least one file")

    try:
        user = current_user.authenticated_email
    except AttributeError:
        user = None
    if body.author != user:
        raise BadRequest("Author must match your logged-in username")

    # validate permission first
    visibilities = set(f.visibility for f in body.files.itervalues())
    for v in visibilities:
        if not p.get('tooltool.upload.{}'.format(v)).can():
            raise Forbidden("no permission to upload {} files".format(v))

    session = g.db.session('tooltool')
    batch = tables.Batch(
        uploaded=time.now(),
        author=body.author,
        message=body.message)

    s3 = current_app.aws.connect_to('s3', region)
    for filename, info in body.files.iteritems():
        if info.algorithm != 'sha512':
            raise BadRequest("'sha512' is the only allowed digest algorithm")
        if not is_valid_sha512(info.digest):
            raise BadRequest("Invalid sha512 digest")
        digest = info.digest
        file = tables.File.query.filter(tables.File.sha512 == digest).first()
        if file and file.visibility != info.visibility:
            raise BadRequest("Cannot change a file's visibility level")
        if file and file.instances != []:
            if file.size != info.size:
                raise BadRequest("Size mismatch for {}".format(filename))
        else:
            if not file:
                file = tables.File(
                    sha512=digest,
                    visibility=info.visibility,
                    size=info.size)
            info.put_url = s3.generate_url(
                method='PUT', expires_in=UPLOAD_EXPIRES_IN, bucket=bucket,
                key='/sha512/{}'.format(info.digest),
                headers={'Content-Type': 'application/octet-stream'})
            pu = tables.PendingUpload(
                file=file,
                region=region,
                expires=time.now() + datetime.timedelta(days=1))
            session.add(pu)
        session.add(tables.BatchFile(filename=filename, file=file, batch=batch))
    session.add(batch)
    session.commit()

    body.id = batch.id
    return body


@bp.route('/upload/complete/<digest>')
@api.apimethod(unicode, unicode, status_code=202)
def upload_complete(digest):
    """Signal that a file has been uploaded and the server should begin
    validating it.  This is merely an optimization: the server also polls
    occasionally for uploads and validates them when they appear.  The
    response is an HTTP 202 indicating the signal has been accepted."""
    if not is_valid_sha512(digest):
        raise BadRequest("Invalid sha512 digest")
    # start a celery task in the background and return immediately
    grooming.check_file_pending_uploads.delay(digest)
    return '{}', 202


@bp.route('/file')
@api.apimethod([types.File])
def get_files():
    """Get a list of all files."""
    return [row.to_json() for row in tables.File.query.all()]


@bp.route('/file/<algorithm>/<digest>')
@api.apimethod(types.File, unicode, unicode)
def get_file(algorithm, digest):
    """Get a single file, by its digest.  Filenames are associated with upload batches,
    not directly with files, so use ``GET /uploads`` to find files by filename."""
    if algorithm != 'sha512':
        raise NotFound("Unknown algorithm")
    row = tables.File.query.filter(tables.File.sha512 == digest).first()
    if not row:
        raise NotFound
    # TODO: include instances here
    return row.to_json()


@bp.route('/file/<algorithm>/<digest>', methods=['CLEAR'])
@p.tooltool.manage.require()
@api.apimethod(types.File, unicode, unicode)
def clear_file(algorithm, digest):
    """Clear all instances of the given file.  The file itself remains, but
    until and unless someone uploads a new copy, it will not be available for
    download."""
    session = current_app.db.session('tooltool')
    if algorithm != 'sha512':
        raise NotFound("Unknown algorithm")
    row = session.query(tables.File).filter(tables.File.sha512 == digest).first()
    if not row:
        raise NotFound
    key_name = '/{}/{}'.format(algorithm, digest)
    cfg = current_app.config.get('TOOLTOOL_REGIONS')
    for i in row.instances:
        conn = current_app.aws.connect_to('s3', i.region)
        bucket = conn.get_bucket(cfg[i.region])
        bucket.delete_key(key_name)
        session.delete(i)
    session.commit()
    # TODO: include instances here
    return row.to_json()


@bp.route('/sha512/<digest>')
@api.apimethod(None, unicode, unicode, status_code=302)
def download_file(digest, region=None):
    """Fetch a link to the file with the given sha512 digest.  The response
    is a 302 redirect to a signed download URL.

    The query argument ``region=us-west-1`` indicates a preference for a URL in
    that region, although if the file is not available in tht region then a URL
    from another region may be returned."""
    if not is_valid_sha512(digest):
        raise BadRequest("Invalid sha512 digest")

    # see where the file is..
    tbl = tables.File
    file_row = tbl.query.filter(tbl.sha512 == digest).first()
    if not file_row or not file_row.instances:
        raise NotFound

    # check visibility
    if not p.get('tooltool.download.{}'.format(file_row.visibility)).can():
        raise Forbidden

    # figure out which region to use, and from there which bucket
    cfg = current_app.config['TOOLTOOL_REGIONS']
    selected_region = None
    for inst in file_row.instances:
        if inst.region == region:
            selected_region = inst.region
            break
    else:
        # preferred region not found, so pick one from the available set
        selected_region = random.choice([inst.region for inst in file_row.instances])
    bucket = cfg[selected_region]

    key = '/sha512/{}'.format(digest)

    s3 = current_app.aws.connect_to('s3', selected_region)
    signed_url = s3.generate_url(
        method='GET', expires_in=GET_EXPIRES_IN, bucket=bucket, key=key)

    return redirect(signed_url)
