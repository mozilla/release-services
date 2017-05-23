# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import enum

import sqlalchemy as sa

# TODO install backend to venv
from backend_common.db import db


# TODO use shared step backend base class for statuses
class SigningStatus(enum.Enum):
    starting = 'starting'
    running = 'running'
    stopping = 'stopping'
    exception = 'exception'
    completed = 'completed'
    failed = 'failed'


# TODO use shared step backend base class for db steps
class TaskclusterStep(db.Model):
    """
    Recording taskcluster steps as distinct entities
    """

    __tablename__ = 'shipit_taskcluster_steps'

    uid = sa.Column(sa.String(80), primary_key=True)
    state = sa.Column(sa.Enum(SigningStatus), default=SigningStatus.starting)
    status_message = sa.Column(sa.String(200), nullable=True)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime, nullable=True)
    task_group_id = sa.Column(sa.String(80), nullable=False)

    def delete(self):
        """
        Delete step
        """
        db.session.delete(self)
        db.session.commit()
