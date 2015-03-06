# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random
import re

from flask import Blueprint
from flask import current_app
from flask import g
from flask import redirect
from relengapi.blueprints.tooltool import tables
from relengapi.blueprints.tooltool import types
from relengapi.lib import api
from relengapi.lib import time
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound

metadata = {
    'repository_of_record': 'https://git.mozilla.org/?p=build/tooltool.git;a=summary',
    'bug_report_url': 'http://goo.gl/XZpyie',  # bugzilla saved new-bug form
}

bp = Blueprint('tooltool', __name__)

is_valid_sha512 = re.compile(r'^[0-9a-f]{128}$').match


def get_region_and_bucket(region_arg):
    cfg = current_app.config['TOOLTOOL_REGIONS']
    if region_arg and region_arg in cfg:
        return region_arg, cfg[region_arg]
    # no region specified, so return one at random
    return random.choice(cfg.items())


# TODO: ensure signed upload URLs specify storage class, ACLs

@bp.route('/batch', methods=['PUT'])
@api.apimethod(types.UploadBatch, unicode, body=types.UploadBatch)
def upload_batch(region=None, body=None):
    """Create a new upload batch.  The response object will contain a
    ``put_url`` for each file which needs to be uploaded -- which may not be
    all!  The caller is then responsible for uploading to those URLs.  The
    resulting signed URLs are valid for one hour, so uploads should begin
    within that timeframe.

    The query argument ``region=us-west-1`` indicates a preference for URLs
    in that region, although if the region is not available then URLs in
    other regions may be returned."""
    # TODO: track pending uploads somehow - 'valid' attr on FileInstance?
    # TODO: verify permission
    # TODO: verify author
    region, bucket = get_region_and_bucket(region)

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
        if not is_valid_sha512(info.digest):
            raise BadRequest("Invalid sha512 digest")
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
@api.apimethod(None, unicode, unicode, status_code=302)
def get_file(digest, region=None):
    """Fetch a link to the file with the given sha512 digest.  The response
    is a 302 redirect to a signed download URL.

    The query argument ``region=us-west-1`` indicates a preference for a URL in
    that region, although if the file is not available in tht region then a URL
    from another region may be returned."""
    if not is_valid_sha512(digest):
        raise BadRequest("Invalid sha512 digest")
    # TODO: verify the file is public
    # TODO: eventually choose a location randomly
    expires_in = 60

    # see where the file is..
    tbl = tables.File
    file_row = tbl.query.filter(tbl.sha512 == digest).first()
    if not file_row or not file_row.instances:
        raise NotFound

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
        method='GET', expires_in=expires_in, bucket=bucket, key=key)

    return redirect(signed_url)
