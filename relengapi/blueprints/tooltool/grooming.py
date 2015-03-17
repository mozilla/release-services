# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib
import logging

from datetime import timedelta
from flask import current_app
from relengapi.blueprints.tooltool import tables
from relengapi.lib import badpenny
from relengapi.lib import celery
from relengapi.lib import time

log = logging.getLogger(__name__)


@badpenny.periodic_task(seconds=600)
def check_pending_uploads(job_status):
    """Check for any pending uploads and verify them if found."""
    session = current_app.db.session('tooltool')
    for pu in tables.PendingUpload.query.all():
        check_pending_upload(session, pu)
    session.commit()


@celery.task
def check_file_pending_uploads(sha512):
    """Check for pending uploads for a single file"""
    session = current_app.db.session('tooltool')
    file = tables.File.query.filter(tables.File.sha512 == sha512).first()
    if file:
        for pu in file.pending_uploads:
            check_pending_upload(session, pu)
    session.commit()


def configure_key(key):
    """Configure the given S3 key as necessary for use with tooltool."""
    # TODO


def verify_file_instance(file, key):
    """Verify that the given File table row and the given S3 Key match
    in size and digest."""
    if key.size != file.size:
        log.warning("Uploaded file {} has unexpected size {}; expected "
                    "{}".format(file.sha512, key.size, file.size))
        return False

    m = hashlib.sha512()
    for bytes in key:
        m.update(bytes)

    if m.hexdigest() != file.sha512:
        log.warning("Digest of file {} does not match".format(file.sha512))
        return False

    return True


def check_pending_upload(session, pu):
    # we can check the upload any time between the expiration of the URL
    # (after which the user can't make any more changes, but the upload
    # may yet be incomplete) and 1 day afterward (ample time for the upload
    # to complete)
    if time.now() < pu.expires:
        # URL is not expired yet
        return
    elif time.now() > pu.expires + timedelta(days=1):
        # Upload will probably never complete
        log.info(
            "Deleting abandoned pending upload for {}".format(pu.file.sha512))
        session.delete(pu)
        return

    # connect and see if the file exists..
    s3 = current_app.aws.connect_to('s3', pu.region)
    cfg = current_app.config.get('TOOLTOOL_REGIONS')
    if not cfg or pu.region not in cfg:
        log.info("Pending upload for {} was to an un-configured "
                 "region".format(pu.file.sha512))
        session.delete(pu)
        return

    bucket = s3.get_bucket(cfg[pu.region], validate=False)
    key = bucket.get_key('/sha512/{}'.format(pu.file.sha512))
    if not key:
        # not uploaded yet
        return

    if not verify_file_instance(pu.file, key):
        log.warning(
            "Upload of {} was invalid; deleting key".format(pu.file.sha512))
        key.delete()
        session.delete(pu)
        return

    # the file is good, so just set up its its configuration in S3
    configure_key(key)

    fi = tables.FileInstance(file=pu.file, region=pu.region)
    session.add(fi)
    session.delete(pu)

    # note that we don't try to copy the file out just yet; that can wait for
    # the next scheduled distribution, and in the interim everyone will hit
    # this one instance.
