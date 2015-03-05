# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa

from relengapi.lib import db


class File(db.declarative_base('tooltool')):
    __tablename__ = 'tooltool_files'

    id = sa.Column(sa.Integer, primary_key=True)
    size = sa.Column(sa.Integer, nullable=False)
    sha512 = sa.Column(sa.String(128), unique=True, nullable=False)

    instances = sa.orm.relationship('FileInstance', backref='file')


class FileInstance(db.declarative_base('tooltool')):
    __tablename__ = 'tooltool_file_instances'

    file_id = sa.Column(
        sa.Integer, sa.ForeignKey('tooltool_files.id'), primary_key=True)
    region = sa.Column(
        sa.Enum('us-east-1', 'us-west-1', 'us-west-2'), primary_key=True)


batch_files = sa.Table(
    'tooltool_batch_files', db.declarative_base('tooltool').metadata,

    sa.Column('file_id',
              sa.Integer, sa.ForeignKey('tooltool_files.id'), primary_key=True),
    sa.Column('batch_id',
              sa.Integer, sa.ForeignKey('tooltool_batches.id'), primary_key=True),
)


class Batch(db.declarative_base('tooltool')):
    __tablename__ = 'tooltool_batches'

    id = sa.Column(sa.Integer, primary_key=True)
    uploaded = sa.Column(db.UTCDateTime, index=True, nullable=False)
    author = sa.Column(sa.Text, nullable=False)
    message = sa.Column(sa.Text, nullable=False)

    files = sa.orm.relationship('File',
                                secondary=batch_files,
                                backref='batches')

# TODO: Keep a list of authorized uploads (urls to check for new files)
#       (with URL expiration time; discard uploads >12h older than that)
