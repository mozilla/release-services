# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import datetime
import hashlib
import json

import flask
import pytz
import sqlalchemy as sa

import cli_common.log
import cli_common.pulse
import tooltool_api.config
import tooltool_api.models
import tooltool_api.utils

logger = cli_common.log.get_logger(__name__)


def replicate_file(session, file, regions_config, aws):
    logger2 = logger.bind(tooltool_sha512=file.sha512)

    regions = set(regions_config)
    file_regions = set([i.region for i in file.instances])

    # only use configured source regions; if a region is removed
    # from the configuration, we can't copy from it.
    source_regions = file_regions & regions
    if not source_regions:

        # this should only happen when the only region containing a
        # file is removed from the configuration
        logger2.warning('no source regions for {}'.format(file.sha512))
        return

    source_region = source_regions.pop()
    source_bucket = regions_config[source_region]
    target_regions = regions - file_regions
    logger2.info('replicating {} from {} to {}'.format(
        file.sha512, source_region, ', '.join(target_regions)))

    key_name = tooltool_api.utils.keyname(file.sha512)
    for target_region in target_regions:
        target_bucket = regions_config[target_region]
        conn = aws.connect_to('s3', target_region)
        bucket = conn.get_bucket(target_bucket)

        # commit the session before replicating, since the DB connection may
        # otherwise go away while we're distracted.
        session.commit()
        bucket.copy_key(
            new_key_name=key_name,
            src_key_name=key_name,
            src_bucket_name=source_bucket,
            storage_class='STANDARD',
            preserve_acl=False,
        )
        try:
            session.add(tooltool_api.models.FileInstance(file=file, region=target_region))
            session.commit()
        except sa.exc.IntegrityError:
            session.rollback()


def verify_file_instance(sha512, size, key):
    '''Verify that the given S3 Key matches the given size and digest.
    '''

    logger2 = logger.bind(tooltool_sha512=sha512)
    if key.size != size:
        logger2.warning('Uploaded file {} has unexpected size {}; expected {}'.format(sha512, key.size, size))
        return False

    m = hashlib.sha512()
    for bytes in key:
        m.update(bytes)

    if m.hexdigest() != sha512:
        logger2.warning('Digest of file {} does not match'.format(sha512))
        return False

    # verify some settings on the key, in case the uploader configured
    # it differently
    if key.storage_class != 'STANDARD':
        logger2.warning('File {} was uploaded with incorrect storage class {}'.format(sha512, key.storage_class))
        return False

    if key.get_redirect():  # pragma: no cover
        # (not covered because moto doesn't support redirects)
        logger2.warning('File {} was uploaded with a website redirect set'.format(sha512, key.storage_class))
        return False

    # verifying the ACL is a bit tricky, so just set it correctly
    key.set_acl('private')

    return True


def check_pending_upload(session, pending_upload):
    # we can check the upload any time between the expiration of the URL
    # (after which the user can't make any more changes, but the upload
    # may yet be incomplete) and 1 day afterward (ample time for the upload
    # to complete)
    sha512 = pending_upload.file.sha512
    size = pending_upload.file.size

    logger2 = logger.bind(tooltool_sha512=sha512)

    if tooltool_api.utils.now() < pending_upload.expires.replace(tzinfo=pytz.UTC):
        # URL is not expired yet
        return
    elif tooltool_api.utils.now() > (pending_upload.expires + datetime.timedelta(days=1)).replace(tzinfo=pytz.UTC):
        # Upload will probably never complete
        logger2.info('Deleting abandoned pending upload for {}'.format(sha512))
        session.delete(pending_upload)
        return

    # connect and see if the file exists..
    s3 = flask.current_app.aws.connect_to('s3', pending_upload.region)
    s3_regions = flask.current_app.config.get('S3_REGIONS')
    if not s3_regions or pending_upload.region not in s3_regions:
        logger2.warning('Pending upload for {} was to an un-configured region'.format(sha512))
        session.delete(pending_upload)
        return

    bucket = s3.get_bucket(s3_regions[pending_upload.region], validate=False)
    key = bucket.get_key(tooltool_api.utils.keyname(sha512))
    if not key:
        # not uploaded yet
        return

    # commit the session before verifying the file instance, since the
    # DB connection may otherwise go away while we're distracted.
    session.commit()

    if not verify_file_instance(sha512, size, key):
        logger2.warning('Upload of {} was invalid; deleting key'.format(sha512))
        key.delete()
        session.delete(pending_upload)
        session.commit()
        return

    logger2.info('Upload of {} considered valid'.format(sha512))

    # add a file instance, but it's OK if it already exists
    try:
        tooltool_api.models.FileInstance(
            file=pending_upload.file,
            region=pending_upload.region,
        )
        session.commit()
    except sa.exc.IntegrityError:
        session.rollback()

    # and delete the pending upload
    session.delete(pending_upload)
    session.commit()

    # note that we don't try to copy the file out just yet; that can wait for
    # the next scheduled distribution, and in the interim everyone will hit
    # this one instance.


async def check_file_pending_uploads(channel, body, envelope, properties):
    '''Check for pending uploads for a single file.
    '''
    body = json.loads(body.decode('utf-8'))
    digest = body['payload']['digest']
    session = flask.current_app.db.session
    file = tooltool_api.models.File.query.filter(
        tooltool_api.models.File.sha512 == digest).first()
    if file:
        for pending_upload in file.pending_uploads:
            check_pending_upload(session, pending_upload)
    session.commit()


def cmd_check_pending_uploads(app):
    '''Check for any pending uploads and verify them if found.
    '''
    session = app.db.session
    pending_uploads = tooltool_api.models.PendingUpload.query.all()
    for pending_upload in pending_uploads:
        check_pending_upload(session, pending_upload)
    session.commit()


def cmd_replicate(app):
    '''Replicate objects between regions as necessary.
    '''
    # fetch all files with at least one instance, but not a full complement
    # of instances
    regions = app.config['S3_REGIONS']
    session = app.db.session
    subq = session.query(
        tooltool_api.models.FileInstance.file_id,
        sa.func.count('*').label('instance_count'),
    )
    subq = subq.group_by(tooltool_api.models.FileInstance.file_id)
    subq = subq.subquery()

    q = session.query(tooltool_api.models.File)
    q = q.join(subq, tooltool_api.models.File.id == subq.c.file_id)
    q = q.filter(subq.c.instance_count < len(regions))
    q = q.all()

    for file in q:
        replicate_file(session, file, regions, app.aws)
    session.commit()


def cmd_worker(app):
    '''Check for pending uploads for a single file.
    '''
    consumer = cli_common.pulse.create_consumer(
        app.config['PULSE_USER'],
        app.config['PULSE_PASSWORD'],
        tooltool_api.config.PROJECT_NAME,
        tooltool_api.config.PULSE_ROUTE_CHECK_FILE_PENDING_UPLOADS,
        check_file_pending_uploads,
    )

    queue = 'exchange/{}/{}'.format(
        flask.current_app.config['PULSE_USER'],
        tooltool_api.config.PROJECT_NAME,
    )
    logger.info(
        'Listening for new messages on',
        queue=queue,
        route=tooltool_api.config.PULSE_ROUTE_CHECK_FILE_PENDING_UPLOADS,
    )

    cli_common.pulse.run_consumer(asyncio.gather(consumer))
