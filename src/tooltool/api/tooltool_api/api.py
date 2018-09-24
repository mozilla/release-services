# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import random
import typing

import flask
import flask_login
import pytz
import sqlalchemy as sa
import werkzeug
import werkzeug.exceptions

import backend_common.auth
import cli_common.log
import tooltool_api.aws
import tooltool_api.config
import tooltool_api.models
import tooltool_api.utils

logger = cli_common.log.get_logger(__name__)


def _get_region_and_bucket(region: typing.Optional[str],
                           regions: typing.Dict[str, str],
                           ) -> typing.Tuple[str, str]:
    if region and region in regions:
        return region, regions[region]
    # no region specified, so return one at random
    return random.choice(list(regions.items()))


def search_batches(q: str) -> dict:
    return dict(
        result=[
            row.to_dict()
            for row in tooltool_api.models.Batch.query.filter(
                sa.or_(
                    tooltool_api.models.Batch.author.contains(q),
                    tooltool_api.models.Batch.message.contains(q)
                )
            ).all()
        ]
    )


def get_batch(id: int) -> dict:
    row = tooltool_api.models.Batch.query.filter(tooltool_api.models.Batch.id == id).first()
    if not row:
        raise werkzeug.exceptions.NotFound
    return row.to_dict()


def upload_batch(body: dict, region: typing.Optional[str]=None) -> dict:
    if not body['message']:
        raise werkzeug.exceptions.BadRequest('message must be non-empty')

    if not body['files']:
        raise werkzeug.exceptions.BadRequest('a batch must include at least one file')

    if 'author' in body:
        raise werkzeug.exceptions.BadRequest('Author must NOT be specified for upload.')

    UPLOAD_EXPIRES_IN = flask.current_app.config['UPLOAD_EXPIRES_IN']
    if type(UPLOAD_EXPIRES_IN) is not int:
        raise werkzeug.exceptions.InternalServerError('UPLOAD_EXPIRES_IN should be of type int.')

    S3_REGIONS = flask.current_app.config['S3_REGIONS']  # type: typing.Dict[str, str]
    if type(S3_REGIONS) is not dict:
        raise werkzeug.exceptions.InternalServerError('S3_REGIONS should be of type dict.')
    region, bucket = _get_region_and_bucket(region, S3_REGIONS)

    body['author'] = flask_login.current_user.get_id()

    # verify permissions based on visibilities
    visibilities = set(f['visibility'] for f in body['files'].values())
    for visibility in visibilities:
        permission = '{}/upload/{}'.format(
            tooltool_api.config.SCOPE_PREFIX,
            visibility,
        )
        if not flask_login.current_user.has_permissions(permission):
            raise werkzeug.exceptions.Forbidden('no permission to upload {} files'.format(visibility))

    session = flask.g.db.session

    batch = tooltool_api.models.Batch(
        uploaded=tooltool_api.utils.now(),
        author=body['author'],
        message=body['message'],
    )

    s3 = flask.current_app.aws.connect_to('s3', region)

    for filename, info in body['files'].items():

        logger2 = logger.bind(tooltool_sha512=info['digest'],
                              tooltool_operation='upload',
                              tooltool_batch_id=batch.id,
                              mozdef=True)

        if info['algorithm'] != 'sha512':
            raise werkzeug.exceptions.BadRequest('`sha512` is the only allowed digest algorithm')

        if not tooltool_api.utils.is_valid_sha512(info['digest']):
            raise werkzeug.exceptions.BadRequest('Invalid sha512 digest'
                                                 )
        digest = info['digest']
        file = tooltool_api.models.File.query.filter(tooltool_api.models.File.sha512 == digest).first()
        if file and file.visibility != info['visibility']:
            raise werkzeug.exceptions.BadRequest('Cannot change a file\'s visibility level')

        if file and file.instances != []:
            if file.size != info['size']:
                raise werkzeug.exceptions.BadRequest('Size mismatch for {}'.format(filename))
        else:
            if not file:
                file = tooltool_api.models.File(sha512=digest,
                                                visibility=info['visibility'],
                                                size=info['size'])
                session.add(file)

            logger2.info('Generating signed S3 PUT URL to {} for {}; expiring in {}s'.format(info['digest'][:10],
                                                                                             flask_login.current_user,
                                                                                             UPLOAD_EXPIRES_IN))

            info['put_url'] = s3.generate_url(
                method='PUT',
                expires_in=UPLOAD_EXPIRES_IN,
                bucket=bucket,
                key=tooltool_api.utils.keyname(info['digest']),
                headers={'Content-Type': 'application/octet-stream'},
            )

            # The PendingUpload row needs to reflect the updated expiration
            # time, even if there's an existing pending upload that expires
            # earlier.  The `merge` method does a SELECT and then either
            # UPDATEs or INSERTs the row.  However, merge needs the file_id,
            # rather than just a reference to the file object; and for that, we
            # need to flush the inserted file.
            session.flush()
            expires = tooltool_api.utils.now() + datetime.timedelta(seconds=UPLOAD_EXPIRES_IN)
            pu = tooltool_api.models.PendingUpload(file_id=file.id,
                                                   region=region,
                                                   expires=expires)
            session.merge(pu)

        session.add(tooltool_api.models.BatchFile(filename=filename, file=file, batch=batch))

    session.add(batch)
    session.commit()

    body['id'] = batch.id
    return dict(result=body)


def upload_complete(digest: str) -> typing.Union[werkzeug.Response,
                                                 typing.Tuple[str, int]]:

    if not tooltool_api.utils.is_valid_sha512(digest):
        raise werkzeug.exceptions.BadRequest('Invalid sha512 digest')

    # if the pending upload is still valid, then we can't check this file
    # yet, so return 409 Conflict.  If there is no PU, or it's expired,
    # then we can proceed.
    file = tooltool_api.models.File.query.filter(tooltool_api.models.File.sha512 == digest).first()
    if file:
        for pending_upload in file.pending_uploads:
            until = pending_upload.expires.replace(tzinfo=pytz.UTC) - tooltool_api.utils.now()
            if until > datetime.timedelta(0):
                # add 1 second to avoid rounding / skew errors
                headers = {'X-Retry-After': str(1 + int(until.total_seconds()))}
                return werkzeug.Response(status=409, headers=headers)

    exchange = 'exchange/{}/{}'.format(
        flask.current_app.config['PULSE_USER'],
        tooltool_api.config.PROJECT_NAME,
    )
    logger.info('Sending digest `{}` to queue `{}` exfor route `{}`.'.format(
        digest,
        exchange,
        tooltool_api.config.PULSE_ROUTE_CHECK_FILE_PENDING_UPLOADS,
    ))
    try:
        flask.current_app.pulse.publish(
            exchange,
            tooltool_api.config.PULSE_ROUTE_CHECK_FILE_PENDING_UPLOADS,
            dict(digest=digest),
        )
    except Exception as e:
        import traceback
        msg = 'Can\'t send notification to pulse.'
        trace = traceback.format_exc()
        logger.error('{0}\nException:{1}\nTraceback: {2}'.format(msg, e, trace))  # noqa

    return '{}', 202


def search_files(q: str) -> dict:
    session = flask.g.db.session
    query = session.query(tooltool_api.models.File).join(tooltool_api.models.BatchFile)
    query = query.filter(sa.or_(tooltool_api.models.BatchFile.filename.contains(q),
                                tooltool_api.models.File.sha512.startswith(q)))
    return dict(result=[row.to_dict() for row in query.all()])


def get_file(digest: str) -> dict:

    if not tooltool_api.utils.is_valid_sha512(digest):
        raise werkzeug.exceptions.BadRequest('Invalid sha512 digest')

    row = tooltool_api.models.File.query.filter(tooltool_api.models.File.sha512 == digest).first()
    if not row:
        raise werkzeug.exceptions.NotFound

    return row.to_dict(include_instances=True)


@backend_common.auth.auth.require_scopes([tooltool_api.config.SCOPE_PREFIX + '/manage'])
def patch_file(digest: str, body: dict) -> dict:
    S3_REGIONS = flask.current_app.config['S3_REGIONS']  # type: typing.Dict[str, str]
    if type(S3_REGIONS) is not dict:
        raise werkzeug.exceptions.InternalServerError('S3_REGIONS should be of type dict.')

    session = flask.current_app.db.session

    file = session.query(tooltool_api.models.File).filter(tooltool_api.models.File.sha512 == digest).first()
    if not file:
        raise werkzeug.exceptions.NotFound

    for change in body:

        if 'op' not in change:
            raise werkzeug.exceptions.BadRequest('No op.')

        if change['op'] == 'delete_instances':
            key_name = tooltool_api.utils.keyname(digest)

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


def download_file(digest: str, region: typing.Optional[str]=None) -> werkzeug.Response:
    logger2 = logger.bind(tooltool_sha512=digest, tooltool_operation='download_file')

    S3_REGIONS = flask.current_app.config['S3_REGIONS']  # type: typing.Dict[str, str]
    if type(S3_REGIONS) is not dict:
        raise werkzeug.exceptions.InternalServerError('S3_REGIONS should be of type dict.')

    DOWLOAD_EXPIRES_IN = flask.current_app.config['DOWLOAD_EXPIRES_IN']
    if type(DOWLOAD_EXPIRES_IN) is not int:
        raise werkzeug.exceptions.InternalServerError('DOWLOAD_EXPIRES_IN should be of type int.')

    ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD = flask.current_app.config['ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD']
    if type(ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD) is not bool:
        raise werkzeug.exceptions.InternalServerError('ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD should be of type bool.')

    logger2.debug('Looking for file in following regions: {}'.format(', '.join(S3_REGIONS.keys())))

    if not tooltool_api.utils.is_valid_sha512(digest):
        raise werkzeug.exceptions.BadRequest('Invalid sha512 digest')

    # see where the file is.
    file_row = tooltool_api.models.File.query.filter(
        tooltool_api.models.File.sha512 == digest).first()
    if not file_row or not file_row.instances:
        raise werkzeug.exceptions.NotFound

    # check visibility
    if file_row.visibility != 'public' or not ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD:
        permission = '{}/download/{}'.format(
            tooltool_api.config.SCOPE_PREFIX,
            file_row.visibility,
        )
        if not flask_login.current_user.has_permissions(permission):
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

    key = tooltool_api.utils.keyname(digest)

    s3 = flask.current_app.aws.connect_to('s3', selected_region)
    logger2.info('Generating signed S3 GET URL for {}, expiring in {}s'.format(digest[:10], DOWLOAD_EXPIRES_IN))
    signed_url = s3.generate_url(method='GET', expires_in=DOWLOAD_EXPIRES_IN, bucket=bucket, key=key)

    return flask.redirect(signed_url)
