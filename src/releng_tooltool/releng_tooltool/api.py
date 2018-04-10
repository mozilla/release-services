# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import random
import time

import flask
import flask_login
import sqlalchemy as sa
import werkzeug
import werkzeug.exceptions

import backend_common.auth
import cli_common.log
import releng_tooltool.aws
import releng_tooltool.models
import releng_tooltool.utils

logger = cli_common.log.get_logger(__name__)


def _get_region_and_bucket(region, regions):
    if region and region in regions:
        return region, regions[region]
    # no region specified, so return one at random
    return random.choice(regions.items())


def search_batches(q):
    return [row.to_dict()
            for row in releng_tooltool.models.Batch.query.filter(
                sa.or_(releng_tooltool.models.Batch.author.contains(q),
                       releng_tooltool.models.Batch.message.contains(q))).all()]


def get_batch(id):
    row = releng_tooltool.models.Batch.query.filter(releng_tooltool.models.Batch.id == id).first()
    if not row:
        raise werkzeug.exceptions.NotFound
    return row.to_dict()


def upload_batch(region, body):
    if not body['message']:
        raise werkzeug.exceptions.BadRequest('message must be non-empty')

    if not body['files']:
        raise werkzeug.exceptions.BadRequest('a batch must include at least one file')

    if body['author']:
        raise werkzeug.exceptions.BadRequest('Author must not be specified for upload')

    UPLOAD_EXPIRES_IN = flask.current_app.config['UPLOAD_EXPIRES_IN']
    if type(UPLOAD_EXPIRES_IN) is not int:
        raise werkzeug.exceptions.InternalServerError('UPLOAD_EXPIRES_IN should be of type int.')

    S3_REGIONS = flask.current_app.config['S3_REGIONS']
    if type(S3_REGIONS) is not dict:
        raise werkzeug.exceptions.InternalServerError('S3_REGIONS should be of type dict.')
    region, bucket = _get_region_and_bucket(region, S3_REGIONS)

    body['author'] = flask_login.current_user.get_id()

    # verify permissions based on visibilities
    visibilities = set(f.visibility for f in body['files'].itervalues())
    for visibility in visibilities:
        prm = flask_login.current_user.has_permissions('project:releng:tooltool/upload/{}'.format(visibility))
        if not prm or not prm.can():
            raise werkzeug.exceptions.Forbidden('no permission to upload {} files'.format(visibility))

    session = flask.g.db.session

    batch = releng_tooltool.models.Batch(
        uploaded=releng_tooltool.utils.now(),
        author=body.author,
        message=body.message,
    )

    s3 = flask.current_app.aws.connect_to('s3', region)

    for filename, info in body.files.iteritems():

        logger2 = logger.bind(tooltool_sha512=info.digest,
                              tooltool_operation='upload',
                              tooltool_batch_id=batch.id,
                              mozdef=True)

        if info.algorithm != 'sha512':
            raise werkzeug.exceptions.BadRequest('`sha512` is the only allowed digest algorithm')

        if not releng_tooltool.utils.is_valid_sha512(info.digest):
            raise werkzeug.exceptions.BadRequest('Invalid sha512 digest'
                                                 )
        digest = info.digest
        file = releng_tooltool.models.File.query.filter(releng_tooltool.models.File.sha512 == digest).first()
        if file and file.visibility != info.visibility:
            raise werkzeug.exceptions.BadRequest('Cannot change a file\'s visibility level')

        if file and file.instances != []:
            if file.size != info.size:
                raise werkzeug.exceptions.BadRequest('Size mismatch for {}'.format(filename))
        else:
            if not file:
                file = releng_tooltool.models.File(sha512=digest,
                                                   visibility=info.visibility,
                                                   size=info.size)
                session.add(file)

            logger2.info('Generating signed S3 PUT URL to {} for {}; expiring in {}s'.format(info.digest[:10],
                                                                                             flask_login.current_user,
                                                                                             UPLOAD_EXPIRES_IN))

            info.put_url = s3.generate_url(method='PUT',
                                           expires_in=UPLOAD_EXPIRES_IN,
                                           bucket=bucket,
                                           key=releng_tooltool.utils.keyname(info.digest),
                                           headers={'Content-Type': 'application/octet-stream'})

            # The PendingUpload row needs to reflect the updated expiration
            # time, even if there's an existing pending upload that expires
            # earlier.  The `merge` method does a SELECT and then either
            # UPDATEs or INSERTs the row.  However, merge needs the file_id,
            # rather than just a reference to the file object; and for that, we
            # need to flush the inserted file.
            session.flush()
            expires = time.now() + datetime.timedelta(seconds=UPLOAD_EXPIRES_IN)
            pu = releng_tooltool.models.PendingUpload(file_id=file.id,
                                                      region=region,
                                                      expires=expires)
            session.merge(pu)

        session.add(releng_tooltool.models.BatchFile(filename=filename, file=file, batch=batch))

    session.add(batch)
    session.commit()

    body.id = batch.id
    return body


def upload_complete(digest):

    if not releng_tooltool.utils.is_valid_sha512(digest):
        raise werkzeug.exceptions.BadRequest('Invalid sha512 digest')

    # if the pending upload is still valid, then we can't check this file
    # yet, so return 409 Conflict.  If there is no PU, or it's expired,
    # then we can proceed.
    file = releng_tooltool.models.File.query.filter(releng_tooltool.models.File.sha512 == digest).first()
    if file:
        for pending_upload in file.pending_uploads:
            until = pending_upload.expires - time.now()
            if until > datetime.timedelta(0):
                # add 1 second to avoid rounding / skew errors
                headers = {'X-Retry-After': str(1 + int(until.total_seconds()))}
                return werkzeug.Response(status=409, headers=headers)

    # start a celery task in the background and return immediately
    # TODO: grooming.check_file_pending_uploads.delay(digest)

    return '{}', 202


def search_files(q):
    session = flask.g.db.session
    query = session.query(releng_tooltool.models.File).join(releng_tooltool.models.BatchFile)
    query = query.filter(sa.or_(releng_tooltool.models.BatchFile.filename.contains(q),
                                releng_tooltool.models.File.sha512.startswith(q)))
    return [row.to_dict() for row in query.all()]


def get_file(digest):

    if not releng_tooltool.utils.is_valid_sha512(digest):
        raise werkzeug.exceptions.BadRequest('Invalid sha512 digest')

    row = releng_tooltool.models.File.query.filter(releng_tooltool.models.File.sha512 == digest).first()
    if not row:
        raise werkzeug.exceptions.NotFound

    return row.to_dict(include_instances=True)


@backend_common.auth.auth.require_scopes(['project:releng:tooltool/manage'])
def patch_file(digest, body):
    S3_REGIONS = flask.current_app.config['S3_REGIONS']
    if type(S3_REGIONS) is not dict:
        raise werkzeug.exceptions.InternalServerError('S3_REGIONS should be of type dict.')

    session = flask.current_app.db.session

    file = session.query(releng_tooltool.models.File).filter(releng_tooltool.models.File.sha512 == digest).first()
    if not file:
        raise werkzeug.exceptions.NotFound

    for change in body:

        if 'op' not in change:
            raise werkzeug.exceptions.BadRequest('No op.')

        if change['op'] == 'delete_instances':
            key_name = releng_tooltool.utils.keyname(digest)

            for instance in file.instances:
                conn = flask.current_app.aws.connect_to('s3', instance.region)

                region_bucket = S3_REGIONS.get(instance.region)
                if region_bucket is None:
                    raise werkzeug.exceptions.InternalServerError(
                        'No bucket for region `{}` defined.'.format(instance.region))

                bucket = conn.get_bucket(region_bucket)
                bucket.delete_key(key_name)

                session.delete(instance)

        elif change['op'] == 'set_visibility':
            if change['visibility'] not in ('internal', 'public'):
                raise werkzeug.exceptions.BadRequest('bad visibility level')
            file.visibility = change['visibility']

        else:
            raise werkzeug.exceptions.BadRequest('Unknown op')

    session.commit()

    return file.to_dict(include_instances=True)


def download_file(digest, region=None):
    logger2 = logger.bind(tooltool_sha512=digest, tooltool_operation='download_file')

    S3_REGIONS = flask.current_app.config['S3_REGIONS']
    if type(S3_REGIONS) is not dict:
        raise werkzeug.exceptions.InternalServerError('S3_REGIONS should be of type dict.')

    DOWLOAD_EXPIRES_IN = flask.current_app.config['DOWLOAD_EXPIRES_IN']
    if type(DOWLOAD_EXPIRES_IN) is not int:
        raise werkzeug.exceptions.InternalServerError('DOWLOAD_EXPIRES_IN should be of type int.')

    ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD = flask.current_app.config['ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD']
    if type(ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD) is not bool:
        raise werkzeug.exceptions.InternalServerError('ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD should be of type bool.')

    logger2.debug('Looking for file in following regions: {}'.format(', '.join(S3_REGIONS.keys())))

    if not releng_tooltool.utils.is_valid_sha512(digest):
        raise werkzeug.exceptions.BadRequest('Invalid sha512 digest')

    # see where the file is.
    file_row = releng_tooltool.models.File.query.filter(
        releng_tooltool.models.File.sha512 == digest).first()
    if not file_row or not file_row.instances:
        raise werkzeug.exceptions.NotFound

    # check visibility
    if file_row.visibility != 'public' or not ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD:
        if not flask_login.current_user.has_permissions('project:releng:tooltool/download/{}'.format(file_row.visibility)):
            raise werkzeug.exceptions.Forbidden

    # figure out which region to use, and from there which bucket
    selected_region = None
    for file_instance in file_row.instances:
        if file_instance.region == region:
            selected_region = file_instance.region
            break
    else:
        # preferred region not found, so pick one from the available set
        selected_region = random.choice([inst.region for inst in file_row.instances])

    bucket = S3_REGIONS.get(selected_region)
    if bucket is None:
        raise werkzeug.exceptions.InternalServerError(
            'Region `{}` can not be found in S3_REGIONS.'.format(selected_region))

    key = releng_tooltool.utils.keyname(digest)

    s3 = flask.current_app.aws.connect_to('s3', selected_region)
    logger2.info('Generating signed S3 GET URL for {}, expiring in {}s'.format(digest[:10], DOWLOAD_EXPIRES_IN))
    signed_url = s3.generate_url(method='GET', expires_in=DOWLOAD_EXPIRES_IN, bucket=bucket, key=key)

    return flask.redirect(signed_url)
