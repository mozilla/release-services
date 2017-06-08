# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import time
import flask
import flask_login
import random
import sqlalchemy as sa
import werkzeug
import werkzeug.exceptions

from cli_common import log
from releng_tooltool.models import Batch, File, PendingUpload, BatchFile
from releng_tooltool.aws import AWS
from releng_tooltool.utils import (
    get_region_and_bucket, now, is_valid_sha512, keyname
)


logger = log.get_logger(__name__)

# This value should be fairly short (and its value is included in the
# `upload_batch` docstring).  Uploads cannot be validated until this
# time has elapsed, otherwise a malicious uploader could alter a file
# after it had been verified.
UPLOAD_EXPIRES_IN = 60
GET_EXPIRES_IN = 60


def search_batches(query):
    return [
        row.to_json()
        for row in Batch.query.filter(
                        sa.or_(Batch.author.contains(query),
                               Batch.message.contains(query))).all()
    ]


def upload_batch(region, body):
    region, bucket = get_region_and_bucket(region)

    if not body.message:
        raise werkzeug.exceptions.BadRequest(
            "message must be non-empty"
        )

    if not body.files:
        raise werkzeug.exceptions.BadRequest(
            "a batch must include at least one file"
        )

    if body.author:
        raise werkzeug.exceptions.BadRequest(
            "Author must not be specified for upload"
        )
    try:
        body.author = flask_login.current_user.authenticated_email
    except AttributeError:
        # no authenticated_email -> use the stringified user (probably a token
        # ID)
        body.author = str(flask_login.current_user)

    # verify permissions based on visibilities
    visibilities = set(f.visibility for f in body.files.itervalues())
    for visibility in visibilities:
        # TODO: check for scope with visibility
        # prm = p.get('tooltool.upload.{}'.format(v))
        # if not prm or not prm.can():
        #     raise Forbidden("no permission to upload {} files".format(v))
        pass

    session = flask.g.db.session

    batch = Batch(
        uploaded=now(),
        author=body.author,
        message=body.message,
    )

    aws = AWS(flask.current_app.config.get('AWS', {}))
    s3 = aws.connect_to('s3', region)

    for filename, info in body.files.iteritems():
        log = logger.bind(
            tooltool_sha512=info.digest,
            tooltool_operation='upload',
            tooltool_batch_id=batch.id,
            mozdef=True,
        )
        if info.algorithm != 'sha512':
            raise werkzeug.exceptions.BadRequest(
                "'sha512' is the only allowed digest algorithm"
            )
        if not is_valid_sha512(info.digest):
            raise werkzeug.exceptions.BadRequest(
                "Invalid sha512 digest"
            )
        digest = info.digest
        file = File.query.filter(File.sha512 == digest).first()
        if file and file.visibility != info.visibility:
            raise werkzeug.exceptions.BadRequest(
                "Cannot change a file's visibility level"
            )
        if file and file.instances != []:
            if file.size != info.size:
                raise werkzeug.exceptions.BadRequest(
                    "Size mismatch for {}".format(filename)
                )
        else:
            if not file:
                file = File(
                    sha512=digest,
                    visibility=info.visibility,
                    size=info.size)
                session.add(file)
            log.info(
                "generating signed S3 PUT URL to {} for {}; expiring in "
                "{}s".format(
                    info.digest[:10],
                    flask_login.current_user,
                    UPLOAD_EXPIRES_IN,
                )
            )
            info.put_url = s3.generate_url(
                method='PUT', expires_in=UPLOAD_EXPIRES_IN, bucket=bucket,
                key=keyname(info.digest),
                headers={'Content-Type': 'application/octet-stream'})

            # The PendingUpload row needs to reflect the updated expiration
            # time, even if there's an existing pending upload that expires
            # earlier.  The `merge` method does a SELECT and then either
            # UPDATEs or INSERTs the row.  However, merge needs the file_id,
            # rather than just a reference to the file object; and for that, we
            # need to flush the inserted file.
            session.flush()
            expires = time.now()
            expires += datetime.timedelta(seconds=UPLOAD_EXPIRES_IN)
            pu = PendingUpload(
                file_id=file.id,
                region=region,
                expires=time.now() + datetime.timedelta(seconds=UPLOAD_EXPIRES_IN),  # noqa
            )
            session.merge(pu)

        session.add(BatchFile(filename=filename, file=file, batch=batch))

    session.add(batch)
    session.commit()

    body.id = batch.id
    return body


def get_batch(id):
    row = Batch.query.filter(Batch.id == id).first()
    if not row:
        raise werkzeug.exceptions.NotFound
    return row.to_json()


def upload_complete(digest):
    if not is_valid_sha512(digest):
        raise werkzeug.exceptions.BadRequest("Invalid sha512 digest")

    # if the pending upload is still valid, then we can't check this file
    # yet, so return 409 Conflict.  If there is no PU, or it's expired,
    # then we can proceed.
    file = File.query.filter(File.sha512 == digest).first()
    if file:
        for pu in file.pending_uploads:
            until = pu.expires - time.now()
            if until > datetime.timedelta(0):
                # add 1 second to avoid rounding / skew errors
                hdr = {'X-Retry-After': str(1 + int(until.total_seconds()))}
                return werkzeug.Response(status=409, headers=hdr)

    # start a celery task in the background and return immediately
    # TODO: grooming.check_file_pending_uploads.delay(digest)
    return '{}', 202


def search_files(query):
    session = flask.g.db.session
    _query = session.query(File).join(BatchFile)
    _query = query.filter(sa.or_(BatchFile.filename.contains(query),
                                 File.sha512.startswith(query)))
    return [row.to_json() for row in _query.all()]


def get_file(digest):
    row = File.query.filter(File.sha512 == digest).first()
    if not row:
        raise werkzeug.exceptions.NotFound
    return row.to_json(include_instances=True)


def download_file(digest, region):
    log = logger.bind(tooltool_sha512=digest, tooltool_operation='download')
    if not is_valid_sha512(digest):
        raise werkzeug.exceptions.BadRequest("Invalid sha512 digest")

    # see where the file is..
    file_row = File.query.filter(File.sha512 == digest).first()
    if not file_row or not file_row.instances:
        raise werkzeug.exceptions.NotFound

    # check visibility
    allow_pub_dl = flask.current_app.config.get('TOOLTOOL_ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD')  # noqa
    if file_row.visibility != 'public' or not allow_pub_dl:
        # TODO: check scope
        # if not p.get('tooltool.download.{}'.format(file_row.visibility)).can():  # noqa
        #     raise Forbidden
        pass

    # figure out which region to use, and from there which bucket
    cfg = flask.current_app.config['TOOLTOOL_REGIONS']
    selected_region = None
    for inst in file_row.instances:
        if inst.region == region:
            selected_region = inst.region
            break
    else:
        # preferred region not found, so pick one from the available set
        selected_region = random.choice(
            [inst.region for inst in file_row.instances])
    bucket = cfg[selected_region]

    key = keyname(digest)

    s3 = flask.current_app.aws.connect_to('s3', selected_region)
    log.info("generating signed S3 GET URL for {}.. expiring in {}s".format(
        digest[:10], GET_EXPIRES_IN))
    signed_url = s3.generate_url(
        method='GET', expires_in=GET_EXPIRES_IN, bucket=bucket, key=key)

    return flask.redirect(signed_url)


def patch_file(digest, body):
    session = flask.current_app.db.session
    file = session.query(File).filter(File.sha512 == digest).first()
    if not file:
        raise werkzeug.exceptions.NotFound

    for change in body:
        if 'op' not in change:
            raise werkzeug.exceptions.BadRequest("no op")
        if change['op'] == 'delete_instances':
            key_name = keyname(digest)
            cfg = flask.current_app.config.get('TOOLTOOL_REGIONS')
            for i in file.instances:
                conn = flask.current_app.aws.connect_to('s3', i.region)
                bucket = conn.get_bucket(cfg[i.region])
                bucket.delete_key(key_name)
                session.delete(i)
        elif change['op'] == 'set_visibility':
            if change['visibility'] not in ('internal', 'public'):
                raise werkzeug.exceptions.BadRequest("bad visibility level")
            file.visibility = change['visibility']
        else:
            raise werkzeug.exceptions.BadRequest("unknown op")
    session.commit()
    return file.to_json(include_instances=True)
