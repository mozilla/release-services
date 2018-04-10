# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import enum
import pickle

import sqlalchemy as sa

from backend_common.db import db


class SigningStatus(enum.Enum):
    starting = 'starting'
    running = 'running'
    stopping = 'stopping'
    exception = 'exception'
    completed = 'completed'
    failed = 'failed'


class SignoffStep(db.Model):
    '''
    Recording signoff steps as distinct entities
    '''

    __tablename__ = 'shipit_signoff_steps'

    uid = sa.Column(sa.String(80), primary_key=True)
    # uid = sa.Column(sa.String(80), nullable=False)
    state = sa.Column(sa.Enum(SigningStatus), default=SigningStatus.starting)
    status_message = sa.Column(sa.String(200), nullable=True)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime, nullable=True)
    policy = sa.Column(sa.Binary())
    signatures = db.relationship('Signature')

    @property
    def policy_data(self):
        if not self.policy:
            return None
        return pickle.loads(self.policy)

    def delete(self):
        '''
        Delete step, and associated signatures
        '''
        signatures = Signature.query.filter_by(step_uid=self.uid).all()

        for signature in signatures:
            signature.delete()

        db.session.delete(self)
        db.session.commit()


class Signature(db.Model):
    '''
    Data about a signature attached to a specific step
    '''
    __tablename__ = 'shipit_signoff_signatures'

    id = sa.Column(sa.Integer, primary_key=True)
    step_uid = sa.Column(sa.String(80), sa.ForeignKey(
        'shipit_signoff_steps.uid'))
    email = sa.Column(sa.String(40))
    group = sa.Column(sa.String(40))
    timestamp = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
