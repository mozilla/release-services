# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib
import logging
import sqlalchemy as sa

from datetime import timedelta
from flask import current_app
from relengapi.blueprints.tooltool import tables
from relengapi.blueprints.tooltool import util
from relengapi.lib import badpenny
from relengapi.lib import celery
from relengapi.lib import time

log = logging.getLogger(__name__)


@badpenny.periodic_task(seconds=600)
def check_pending_uploads(job_status):
    """Check for any pending uploads and verify them if found."""
    session = current_app.db.session('relengapi')
    for pu in tables.PendingUpload.query.all():
        check_pending_upload(session, pu)
    session.commit()


@badpenny.periodic_task(seconds=3600)
def replicate(job_status):
    """Replicate objects between regions as necessary"""
    # fetch all files with at least one instance, but not a full complement
    # of instances
    num_regions = len(current_app.config['TOOLTOOL_REGIONS'])
    fi_tbl = tables.FileInstance
    f_tbl = tables.File
    session = current_app.db.session('relengapi')
    subq = session.query(
        fi_tbl.file_id,
        sa.func.count('*').label('instance_count'))
    subq = subq.group_by(fi_tbl.file_id)
    subq = subq.subquery()
    q = session.query(f_tbl)
    q = q.join(subq, f_tbl.id == subq.c.file_id)
    q = q.filter(subq.c.instance_count < num_regions)
    q = q.all()
    for file in q:
        replicate_file(session, file)
    session.commit()


def replicate_file(session, file, _test_shim=lambda: None):
    config = current_app.config['TOOLTOOL_REGIONS']
    regions = set(config)
    file_regions = set([i.region for i in file.instances])
    # only use configured source regions; if a region is removed
    # from the configuration, we can't copy from it.
    source_regions = file_regions & regions
    if not source_regions:
        # this should only happen when the only region containing a
        # file is removed from the configuration
        log.warning("no source regions for {}".format(file.sha512))
        return
    source_region = source_regions.pop()
    source_bucket = config[source_region]
    target_regions = regions - file_regions
    log.info("replicating {} from {} to {}".format(
        file.sha512, source_region, ', '.join(target_regions)))

    key_name = util.keyname(file.sha512)
    for target_region in target_regions:
        target_bucket = config[target_region]
        conn = current_app.aws.connect_to('s3', target_region)
        bucket = conn.get_bucket(target_bucket)

        # commit the session before replicating, since the DB connection may
        # otherwise go away while we're distracted.
        session.commit()
        _test_shim()
        bucket.copy_key(new_key_name=key_name,
                        src_key_name=key_name,
                        src_bucket_name=source_bucket,
                        storage_class='STANDARD',
                        preserve_acl=False)
        try:
            session.add(tables.FileInstance(file=file, region=target_region))
            session.commit()
        except sa.exc.IntegrityError:
            session.rollback()


@celery.task
def check_file_pending_uploads(sha512):
    """Check for pending uploads for a single file"""
    session = current_app.db.session('relengapi')
    file = tables.File.query.filter(tables.File.sha512 == sha512).first()
    if file:
        for pu in file.pending_uploads:
            check_pending_upload(session, pu)
    session.commit()


def verify_file_instance(sha512, size, key):
    """Verify that the given S3 Key matches the given size and digest."""
    if key.size != size:
        log.warning("Uploaded file {} has unexpected size {}; expected "
                    "{}".format(sha512, key.size, size))
        return False

    m = hashlib.sha512()
    for bytes in key:
        m.update(bytes)

    if m.hexdigest() != sha512:
        log.warning("Digest of file {} does not match".format(sha512))
        return False

    # verify some settings on the key, in case the uploader configured
    # it differently
    if key.storage_class != 'STANDARD':
        log.warning("File {} was uploaded with incorrect storage "
                    "class {}".format(sha512, key.storage_class))
        return False

    if key.get_redirect():  # pragma: no cover
        # (not covered because moto doesn't support redirects)
        log.warning("File {} was uploaded with a website redirect set"
                    .format(sha512, key.storage_class))
        return False

    # verifying the ACL is a bit tricky, so just set it correctly
    key.set_acl('private')

    return True


def check_pending_upload(session, pu, _test_shim=lambda: None):
    # we can check the upload any time between the expiration of the URL
    # (after which the user can't make any more changes, but the upload
    # may yet be incomplete) and 1 day afterward (ample time for the upload
    # to complete)
    sha512 = pu.file.sha512
    size = pu.file.size

    if time.now() < pu.expires:
        # URL is not expired yet
        return
    elif time.now() > pu.expires + timedelta(days=1):
        # Upload will probably never complete
        log.info(
            "Deleting abandoned pending upload for {}".format(sha512))
        session.delete(pu)
        return

    # connect and see if the file exists..
    s3 = current_app.aws.connect_to('s3', pu.region)
    cfg = current_app.config.get('TOOLTOOL_REGIONS')
    if not cfg or pu.region not in cfg:
        log.warning("Pending upload for {} was to an un-configured "
                    "region".format(sha512))
        session.delete(pu)
        return

    bucket = s3.get_bucket(cfg[pu.region], validate=False)
    key = bucket.get_key(util.keyname(sha512))
    if not key:
        # not uploaded yet
        return

    # commit the session before verifying the file instance, since the
    # DB connection may otherwise go away while we're distracted.
    session.commit()
    _test_shim()

    if not verify_file_instance(sha512, size, key):
        log.warning(
            "Upload of {} was invalid; deleting key".format(sha512))
        key.delete()
        session.delete(pu)
        session.commit()
        return

    log.info("Upload of {} considered valid".format(sha512))
    # add a file instance, but it's OK if it already exists
    try:
        tables.FileInstance(file=pu.file, region=pu.region)
        session.commit()
    except sa.exc.IntegrityError:
        session.rollback()

    # and delete the pending upload
    session.delete(pu)
    session.commit()

    # note that we don't try to copy the file out just yet; that can wait for
    # the next scheduled distribution, and in the interim everyone will hit
    # this one instance.
