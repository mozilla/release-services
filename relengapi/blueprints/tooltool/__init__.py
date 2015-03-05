# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import current_app
from flask import g
from flask import redirect
from relengapi.blueprints.tooltool import tables
from relengapi.blueprints.tooltool import types
from relengapi.lib import api
from relengapi.lib import time
from werkzeug.exceptions import BadRequest

metadata = {
    'repository_of_record': 'https://git.mozilla.org/?p=build/tooltool.git;a=summary',
    'bug_report_url': 'http://goo.gl/XZpyie',  # bugzilla saved new-bug form
}

bp = Blueprint('tooltool', __name__)


# TODO: ensure signed upload URLs specify storage class, ACLs
# TODO: support '?region=..' on most API methods as a preference, otherwise choose randomly

@bp.route('/batch', methods=['PUT'])
@api.apimethod(types.UploadBatch, body=types.UploadBatch)
def upload_batch(body):
    """Create a new upload batch.  The response object will contain a
    ``put_url`` for each file which needs to be uploaded -- which may not be
    all!  The caller is then responsible for uploading to those URLs.  The
    resulting signed URLs are valid for one hour, so uploads should begin
    within that timeframe."""
    # TODO: track pending uploads somehow - 'valid' attr on FileInstance?
    # TODO: verify permission
    # TODO: verify author
    region = current_app.config['TOOLTOOL_REGION']
    bucket = current_app.config['TOOLTOOL_BUCKET']

    if not body.message:
        raise BadRequest("message must be non-empty")

    if not body.files:
        raise BadRequest("a batch must include at least one file")

    session = g.db.session('tooltool')
    batch = tables.Batch(
        uploaded=time.now(),
        author=body.author,
        message=body.message)

    s3 = current_app.aws.connect_to('s3', region)
    for filename, info in body.files.iteritems():
        if info.algorithm != 'sha512':
            raise BadRequest("'sha512' is the only allowed digest algorithm")
        # TODO: verify form of the hash
        digest = info.digest
        file_row = tables.File.query.filter(tables.File.sha512 == digest).first()
        if file_row:
            if file_row.size != info.size:
                raise BadRequest("Size mismatch for {}".format(filename))
        else:
            file_row = tables.File(sha512=digest, size=info.size)
            # TODO: sign size?
            info.put_url = s3.generate_url(
                method='PUT', expires_in=3600, bucket=bucket,
                key='/sha512/{}'.format(info.digest),
                headers={'Content-Type': 'application/octet-stream'})
        batch.files.append(file_row)
    session.add(batch)
    session.commit()

    body.id = batch.id
    return body


@bp.route('/sha512/<digest>')
def legacy_get(digest):
    """Fetch a link to the file with the given digest; this is the legacy API and
    will only allow access to public files.  It chooses a download location
    randomly."""
    expires_in = 60
    # TODO: verify digest format
    # TODO: verify the file exists, is public
    # TODO: eventually choose a location randomly
    region = current_app.config['TOOLTOOL_REGION']
    bucket = current_app.config['TOOLTOOL_BUCKET']
    key = '/sha512/{}'.format(digest)

    s3 = current_app.aws.connect_to('s3', region)
    signed_url = s3.generate_url(
        method='GET', expires_in=expires_in, bucket=bucket, key=key)

    return redirect(signed_url)
