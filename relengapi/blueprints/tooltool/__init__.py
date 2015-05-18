# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import logging
import random
import re
import sqlalchemy as sa

from flask import Blueprint
from flask import current_app
from flask import g
from flask import redirect
from flask import url_for
from flask.ext.login import current_user
from flask.ext.login import login_required
from relengapi.blueprints.tooltool import grooming
from relengapi.blueprints.tooltool import tables
from relengapi.blueprints.tooltool import types
from relengapi.blueprints.tooltool import util
from relengapi.lib import angular
from relengapi.lib import api
from relengapi.lib import time
from relengapi.lib.permissions import p
from werkzeug import Response
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import NotFound

metadata = {
    'repository_of_record': 'https://git.mozilla.org/?p=build/tooltool.git;a=summary',
    'bug_report_url': 'http://goo.gl/XZpyie',  # bugzilla saved new-bug form
}

bp = Blueprint('tooltool', __name__,
               template_folder='templates',
               static_folder='static')

is_valid_sha512 = re.compile(r'^[0-9a-f]{128}$').match

p.tooltool.download.public.doc("Download PUBLIC files from tooltool")
p.tooltool.upload.public.doc("Upload PUBLIC files to tooltool")
# note that internal does not imply public; that's up to the user.
p.tooltool.download.internal.doc("Download INTERNAL files from tooltool")
p.tooltool.upload.internal.doc("Upload INTERNAL files to tooltool")
p.tooltool.manage.doc("Manage tooltool files, including deleting and changing visibility levels")

# This value should be fairly short (and its value is included in the
# `upload_batch` docstring).  Uploads cannot be validated until this
# time has elapsed, otherwise a malicious uploader could alter a file
# after it had been verified.
UPLOAD_EXPIRES_IN = 60
GET_EXPIRES_IN = 60

log = logging.getLogger(__name__)


def get_region_and_bucket(region_arg):
    cfg = current_app.config['TOOLTOOL_REGIONS']
    if region_arg and region_arg in cfg:
        return region_arg, cfg[region_arg]
    # no region specified, so return one at random
    return random.choice(cfg.items())

bp.root_widget_template(
    'tooltool_root_widget.html', priority=100,
    condition=lambda: not current_user.is_anonymous())


@bp.route('/')
@login_required
def root():
    return angular.template('tooltool.html',
                            url_for('.static', filename='tooltool.js'),
                            url_for('.static', filename='tooltool.css'))


@bp.route('/upload')
@api.apimethod([types.UploadBatch], unicode)
def search_batches(q):
    """Search upload batches.  The required query parameter ``q`` can match a
    substring of an author's email or a batch message."""
    tbl = tables.Batch
    q = tbl.query.filter(sa.or_(
        tbl.author.contains(q),
        tbl.message.contains(q)))
    return [row.to_json() for row in q.all()]


@bp.route('/upload/<int:id>')
@api.apimethod(types.UploadBatch, int)
def get_batch(id):
    """Get a specific upload batch by id."""
    row = tables.Batch.query.filter(tables.Batch.id == id).first()
    if not row:
        raise NotFound
    return row.to_json()


@bp.route('/upload', methods=['POST'])
@api.apimethod(types.UploadBatch, unicode, body=types.UploadBatch)
def upload_batch(region=None, body=None):
    """Create a new upload batch.  The response object will contain a
    ``put_url`` for each file which needs to be uploaded -- which may not be
    all!  The caller is then responsible for uploading to those URLs.  The
    resulting signed URLs are valid for one hour, so uploads should begin
    within that timeframe.  Consider using Amazon's MD5-verification
    capabilities to ensure that the uploaded files are transferred correctly,
    although the tooltool server will verify the integrity anyway.  The
    upload must have the header ``Content-Type: application/octet-stream```.

    The query argument ``region=us-west-1`` indicates a preference for URLs
    in that region, although if the region is not available then URLs in
    other regions may be returned.

    The returned URLs are only valid for 60 seconds, so all upload requests
    must begin within that timeframe.  Clients should therefore perform all
    uploads in parallel, rather than sequentially.  This limitation is in
    place to prevent malicious modification of files after they have been
    verified."""
    region, bucket = get_region_and_bucket(region)

    if not body.message:
        raise BadRequest("message must be non-empty")

    if not body.files:
        raise BadRequest("a batch must include at least one file")

    if body.author:
        raise BadRequest("Author must not be specified for upload")
    try:
        body.author = current_user.authenticated_email
    except AttributeError:
        raise BadRequest("Could not determine authenticated username")

    # validate permission first
    visibilities = set(f.visibility for f in body.files.itervalues())
    for v in visibilities:
        if not p.get('tooltool.upload.{}'.format(v)).can():
            raise Forbidden("no permission to upload {} files".format(v))

    session = g.db.session('relengapi')
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
                session.add(file)
            log.info("generating signed PUT URL to {} for {}, expires in {}s".format(
                     info.digest, current_user, UPLOAD_EXPIRES_IN))
            info.put_url = s3.generate_url(
                method='PUT', expires_in=UPLOAD_EXPIRES_IN, bucket=bucket,
                key=util.keyname(info.digest),
                headers={'Content-Type': 'application/octet-stream'})
            # The PendingUpload row needs to reflect the updated expiration
            # time, even if there's an existing pending upload that expires
            # earlier.  The `merge` method does a SELECT and then either UPDATEs
            # or INSERTs the row.  However, merge needs the file_id, rather than
            # just a reference to the file object; and for that, we need to flush
            # the inserted file.
            session.flush()
            pu = tables.PendingUpload(
                file_id=file.id,
                region=region,
                expires=time.now() + datetime.timedelta(seconds=UPLOAD_EXPIRES_IN))
            session.merge(pu)
        session.add(tables.BatchFile(filename=filename, file=file, batch=batch))
    session.add(batch)
    session.commit()

    body.id = batch.id
    return body


@bp.route('/upload/complete/sha512/<digest>')
@api.apimethod(unicode, unicode, status_code=202)
def upload_complete(digest):
    """Signal that a file has been uploaded and the server should begin
    validating it.  This is merely an optimization: the server also polls
    occasionally for uploads and validates them when they appear.

    Uploads cannot be safely validated until the upload URL has expired, which
    occurs a short time after the URL is generated (currently 60 seconds but
    subject to change).

    If the upload URL has expired, then the response is an HTTP 202 indicating
    that the signal has been accepted.  If the URL has not expired, then the
    response is an HTTP 409, and the ``X-Retry-After`` header gives a time,
    in seconds, that the client should wait before trying again."""
    if not is_valid_sha512(digest):
        raise BadRequest("Invalid sha512 digest")

    # if the pending upload is still valid, then we can't check this file
    # yet, so return 409 Conflict.  If there is no PU, or it's expired,
    # then we can proceed.
    file = tables.File.query.filter(tables.File.sha512 == digest).first()
    if file:
        for pu in file.pending_uploads:
            until = pu.expires - time.now()
            if until > datetime.timedelta(0):
                # add 1 second to avoid rounding / skew errors
                hdr = {'X-Retry-After': str(1 + int(until.total_seconds()))}
                return Response(status=409, headers=hdr)

    # start a celery task in the background and return immediately
    grooming.check_file_pending_uploads.delay(digest)
    return '{}', 202


@bp.route('/file')
@api.apimethod([types.File], unicode)
def search_files(q):
    """Search for files matching the query ``q``.  The query matches against
    prefixes of hashes (at least 8 characters) or against filenames."""
    session = g.db.session('relengapi')
    query = session.query(tables.File).join(tables.BatchFile)
    query = query.filter(sa.or_(
        tables.BatchFile.filename.contains(q),
        tables.File.sha512.startswith(q)))
    return [row.to_json() for row in query.all()]


@bp.route('/file/sha512/<digest>')
@api.apimethod(types.File, unicode, unicode)
def get_file(digest):
    """Get a single file, by its digest.  Filenames are associated with upload
    batches, not directly with files, so use ``GET /uploads`` to find files by
    filename.

    The returned File instance contains an ``instances`` attribute showing the
    regions in which the file exists."""
    row = tables.File.query.filter(tables.File.sha512 == digest).first()
    if not row:
        raise NotFound
    return row.to_json(include_instances=True)


@bp.route('/file/sha512/<digest>', methods=['PATCH'])
@p.tooltool.manage.require()
@api.apimethod(types.File, unicode, body=[{unicode: unicode}])
def patch_file(digest, body):
    """Make administrative changes to an existing file.  The body is a list of
    changes to apply, each represented by a JSON object.

    The object ``{"op": "delete_instances"}`` will cause all instances of the
    file to be deleted.  The file record itself will not be deleted, as it is
    still a part of one or more upload batches, but until and unless someone
    uploads a new copy, the content will not be available for download.

    If the change has op ``"set_visibility"``, then the file's visibility will
    be set to the value given by the change's ``visibility`` attribute.  For
    example, ``{"op": "set_visibility", "visibility": "internal"}`` will mark a
    file as "internal" after someone has accidentally uploaded it with public
    visibility.

    The returned File instance contains an ``instances`` attribute showing any
    changes."""
    session = current_app.db.session('relengapi')
    file = session.query(tables.File).filter(tables.File.sha512 == digest).first()
    if not file:
        raise NotFound

    for change in body:
        if 'op' not in change:
            raise BadRequest("no op")
        if change['op'] == 'delete_instances':
            key_name = util.keyname(digest)
            cfg = current_app.config.get('TOOLTOOL_REGIONS')
            for i in file.instances:
                conn = current_app.aws.connect_to('s3', i.region)
                bucket = conn.get_bucket(cfg[i.region])
                bucket.delete_key(key_name)
                session.delete(i)
        elif change['op'] == 'set_visibility':
            if change['visibility'] not in ('internal', 'public'):
                raise BadRequest("bad visibility level")
            file.visibility = change['visibility']
        else:
            raise BadRequest("unknown op")
    session.commit()
    return file.to_json(include_instances=True)


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
    allow_pub_dl = current_app.config.get('TOOLTOOL_ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD')
    if file_row.visibility != 'public' or not allow_pub_dl:
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

    key = util.keyname(digest)

    s3 = current_app.aws.connect_to('s3', selected_region)
    log.info("generating signed GET URL to {} for {}, expires in {}s".format(
             digest, current_user, GET_EXPIRES_IN))
    signed_url = s3.generate_url(
        method='GET', expires_in=GET_EXPIRES_IN, bucket=bucket, key=key)

    return redirect(signed_url)
