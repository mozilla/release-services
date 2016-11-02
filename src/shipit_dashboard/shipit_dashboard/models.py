# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import


import sqlalchemy as sa
from releng_common.db import db

import datetime
import pickle

# M2M link between analysis & bug
bugs = db.Table(
    'analysis_bugs',
    sa.Column('analysis_id', sa.Integer, sa.ForeignKey('shipit_bug_analysis.id')),
    sa.Column('bug_id', sa.Integer, sa.ForeignKey('shipit_bug_result.id'))
)


class BugAnalysis(db.Model):
    """
    A template to build some cached analysis
    by listing several bugs from Bugzilla, with
    their analysus
    """
    __tablename__ = 'shipit_bug_analysis'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80))
    parameters = sa.Column(sa.Text())
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    bugs = db.relationship('BugResult', secondary=bugs, backref=db.backref('analysis', lazy='dynamic'))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'AnalysisTemplate {}'.format(self.name)


class BugResult(db.Model):
    """
    The cached result of an analysis run
    """
    __tablename__ = 'shipit_bug_result'

    id = sa.Column(sa.Integer, primary_key=True)
    bugzilla_id = sa.Column(sa.Integer, unique=True)
    payload = sa.Column(sa.Binary())
    payload_hash = sa.Column(sa.String(40))

    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, bugzilla_id):
        self.bugzilla_id = bugzilla_id

    def __repr__(self):
        return 'BugResult {}'.format(self.bugzilla_id)

    @property
    def payload_data(self):
        if not self.payload:
            return None
        return pickle.loads(self.payload)

    def delete(self):
        """
        Delete bug and its dependencies
        """
        # Delete links, avoid StaleDataError
        db.engine.execute(sa.text('delete from analysis_bugs where bug_id = :bug_id'), bug_id=self.id)

        # Delete the bug
        db.session.delete(self)
        db.session.commit()
