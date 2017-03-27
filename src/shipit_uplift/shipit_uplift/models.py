# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import pickle
import enum
import sqlalchemy as sa

from backend_common.db import db


# M2M link between analysis & bug
bugs = db.Table(
    'shipit_uplift_analysis_bugs',
    sa.Column('analysis_id', sa.Integer, sa.ForeignKey('shipit_uplift_analysis.id')),  # noqa
    sa.Column('bug_id', sa.Integer, sa.ForeignKey('shipit_uplift_bug.id')),
    sa.UniqueConstraint('analysis_id', 'bug_id', name='shipit_uplift_uniq_ba')  # noqa
)


class BugAnalysis(db.Model):
    """
    A template to build some cached analysis
    by listing several bugs from Bugzilla, with
    their analysus
    """
    __tablename__ = 'shipit_uplift_analysis'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), nullable=False)
    version = sa.Column(sa.Integer, nullable=False)
    parameters = sa.Column(sa.Text())
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    bugs = db.relationship('BugResult', secondary=bugs, backref=db.backref('analysis', lazy='dynamic'), order_by='BugResult.bugzilla_id')  # noqa

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Analysis {} {}'.format(self.name, self.version)

    @staticmethod
    def with_bugs():
        """
        List all analysis with bugs count
        Uses a single sql request
        """
        return \
            db.session \
            .query(
                 BugAnalysis,
                 sa.func.count(bugs.c.bug_id.distinct())
             ) \
            .join(bugs, isouter=True) \
            .group_by(BugAnalysis)


class BugResult(db.Model):
    """
    The cached result of an analysis run
    """
    __tablename__ = 'shipit_uplift_bug'

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

    def list_contributors(self):
        """
        List contributors with roles in one SQL query
        """
        return \
            db.session \
            .query(Contributor, BugContributor) \
            .join(BugContributor) \
            .filter_by(bug_id=self.id) \
            .all()

    def delete(self):
        """
        Delete bug and its dependencies
        """
        # Delete links, avoid StaleDataError
        db.engine.execute(sa.text('delete from shipit_uplift_analysis_bugs where bug_id = :bug_id'), bug_id=self.id)  # noqa
        db.engine.execute(sa.text('delete from shipit_uplift_patch_status where bug_id = :bug_id'), bug_id=self.id)  # noqa

        # Delete the bug
        db.session.delete(self)
        db.session.commit()


class Contributor(db.Model):
    """
    An active Mozilla contributor
    """
    __tablename__ = 'shipit_uplift_contributor'
    id = sa.Column(sa.Integer, primary_key=True)
    bugzilla_id = sa.Column(sa.Integer, unique=True)
    name = sa.Column(sa.String(250))
    email = sa.Column(sa.String(250))
    avatar_url = sa.Column(sa.String(250))
    karma = sa.Column(sa.Integer, default=0)
    comment_private = sa.Column(sa.Text, default='')
    comment_public = sa.Column(sa.Text, default='')


class BugContributor(db.Model):
    """
    M2M link between contributor & bug
    """
    __tablename__ = 'shipit_uplift_contributor_bugs'
    __table_args__ = (
        sa.UniqueConstraint('contributor_id', 'bug_id', name='uniq_contrib_bug'),  # noqa
    )

    id = sa.Column(sa.Integer, primary_key=True)
    contributor_id = sa.Column(sa.Integer, sa.ForeignKey('shipit_uplift_contributor.id'))  # noqa
    bug_id = sa.Column(sa.Integer, sa.ForeignKey('shipit_uplift_bug.id'))  # noqa
    roles = sa.Column(sa.String(250))

    bug = db.relationship(BugResult, backref="contributors")
    contributor = db.relationship(Contributor, backref="bugs")


class MergeStatus(enum.Enum):
    failed = 'failed'
    merged = 'merged'
    skipped = 'skipped'


class PatchStatus(db.Model):
    """
    Patch merge status at a specific time
    """
    __tablename__ = 'shipit_uplift_patch_status'
    __table_args__ = (
        sa.UniqueConstraint('bug_id', 'revision', 'revision_parent', 'branch', name='uniq_patch_status'),  # noqa
        sa.UniqueConstraint('bug_id', 'group', 'branch', 'revision', name="uniq_patch_status_group")  # noqa
    )

    id = sa.Column(sa.Integer, primary_key=True)
    group = sa.Column(sa.Integer, default=1, nullable=False)
    bug_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('shipit_uplift_bug.id'),
        nullable=False
    )

    revision = sa.Column(sa.String(50), nullable=False)
    revision_parent = sa.Column(sa.String(50), nullable=False)
    branch = sa.Column(sa.String(50), nullable=False)
    message = sa.Column(sa.Text())
    created = sa.Column(
        sa.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )
    status = sa.Column(sa.Enum(MergeStatus), default=MergeStatus.merged)

    bug = db.relationship(BugResult, backref="patch_status")
