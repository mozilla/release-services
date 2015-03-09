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


class FileInstance(db.declarative_base('tooltool')):

    """A verified instance of a file in a single region."""

    __tablename__ = 'tooltool_file_instances'

    file_id = sa.Column(
        sa.Integer, sa.ForeignKey('tooltool_files.id'), primary_key=True)
    region = sa.Column(
        sa.Enum(*allowed_regions), primary_key=True)


batch_files = sa.Table(
    'tooltool_batch_files', db.declarative_base('tooltool').metadata,

    sa.Column('file_id',
              sa.Integer, sa.ForeignKey('tooltool_files.id'), primary_key=True),
    sa.Column('batch_id',
              sa.Integer, sa.ForeignKey('tooltool_batches.id'), primary_key=True),
)


class Batch(db.declarative_base('tooltool')):

    """Upload batches, with batch metadata, linked to the uploaded files"""

    __tablename__ = 'tooltool_batches'

    id = sa.Column(sa.Integer, primary_key=True)
    uploaded = sa.Column(db.UTCDateTime, index=True, nullable=False)
    author = sa.Column(sa.Text, nullable=False)
    message = sa.Column(sa.Text, nullable=False)

    files = sa.orm.relationship('File',
                                secondary=batch_files,
                                backref='batches')


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
