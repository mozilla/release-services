# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa

from relengapi.lib import db

allowed_regions = ('us-east-1', 'us-west-1', 'us-west-2')


class File(db.declarative_base('tooltool')):

    """An file, identified by size and digest.  The server may have zero
    or many copies of a file."""

    __tablename__ = 'tooltool_files'

    id = sa.Column(sa.Integer, primary_key=True)
    size = sa.Column(sa.Integer, nullable=False)
    sha512 = sa.Column(sa.String(128), unique=True, nullable=False)
    visibility = sa.Column(sa.Enum('public', 'internal'), nullable=False)

    instances = sa.orm.relationship('FileInstance', backref='file')

    # note that changes to this dictionary will not be reflected to the DB;
    # add or delete BatchFile instances directly instead.
    @property
    def batches(self):
        return {bf.filename: bf.batch for bf in self._batches}


class FileInstance(db.declarative_base('tooltool')):

    """A verified instance of a file in a single region."""

    __tablename__ = 'tooltool_file_instances'

    file_id = sa.Column(
        sa.Integer, sa.ForeignKey('tooltool_files.id'), primary_key=True)
    region = sa.Column(
        sa.Enum(*allowed_regions), primary_key=True)


class BatchFile(db.declarative_base('tooltool')):

    """An association of upload batches to files, with filenames"""

    __tablename__ = 'tooltool_batch_files'

    file_id = sa.Column(sa.Integer, sa.ForeignKey('tooltool_files.id'), primary_key=True)
    file = sa.orm.relationship("File", backref="_batches")
    batch_id = sa.Column(sa.Integer, sa.ForeignKey('tooltool_batches.id'), primary_key=True)
    batch = sa.orm.relationship("Batch", backref="_files")

    filename = sa.Column(sa.Text, nullable=False)


class Batch(db.declarative_base('tooltool')):

    """Upload batches, with batch metadata, linked to the uploaded files"""

    __tablename__ = 'tooltool_batches'

    id = sa.Column(sa.Integer, primary_key=True)
    uploaded = sa.Column(db.UTCDateTime, index=True, nullable=False)
    author = sa.Column(sa.Text, nullable=False)
    message = sa.Column(sa.Text, nullable=False)

    # note that changes to this dictionary will not be reflected to the DB;
    # add or delete BatchFile instances directly instead.
    @property
    def files(self):
        return {bf.filename: bf.file for bf in self._files}


class PendingUpload(db.declarative_base('tooltool')):

    """Files for which upload URLs have been generated, but which haven't yet
    been uploaded.  This table is used to poll for completed uploads."""

    __tablename__ = 'tooltool_pending_upload'

    id = sa.Column(sa.Integer, primary_key=True)
    expires = sa.Column(db.UTCDateTime, index=True, nullable=False)
    file_id = sa.Column(
        sa.Integer, sa.ForeignKey('tooltool_files.id'), nullable=False)
    region = sa.Column(
        sa.Enum(*allowed_regions), nullable=False)

    file = sa.orm.relationship('File', backref='pending_uploads')
