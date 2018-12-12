# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import enum
import pickle
import urllib.parse

import sqlalchemy as sa

from backend_common.db import db

# M2M link between analysis & bug
bugs = db.Table(
    'uplift_backend_analysis_bugs',
    sa.Column('analysis_id', sa.Integer, sa.ForeignKey('uplift_backend_analysis.id')),  # noqa
    sa.Column('bug_id', sa.Integer, sa.ForeignKey('uplift_backend_bug.id')),
    sa.UniqueConstraint('analysis_id', 'bug_id', name='uplift_backend_uniq_ba')  # noqa
)


class BugAnalysis(db.Model):
    '''
    A template to build some cached analysis
    by listing several bugs from Bugzilla, with
    their analysus
    '''
    __tablename__ = 'uplift_backend_analysis'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), nullable=False)
    version = sa.Column(sa.Integer, nullable=False)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    bugs = db.relationship('BugResult', secondary=bugs, backref=db.backref('analysis', lazy='dynamic'), order_by='BugResult.bugzilla_id')  # noqa

    def __init__(self, name, version=1):
        self.name = name
        self.version = version

    def __repr__(self):
        return 'Analysis {} {}'.format(self.name, self.version)

    @staticmethod
    def with_bugs():
        '''
        List all analysis with bugs count
        Uses a single sql request
        '''
        return \
            db.session \
            .query(
                 BugAnalysis,
                 sa.func.count(bugs.c.bug_id.distinct())
             ) \
            .join(bugs, isouter=True) \
            .group_by(BugAnalysis)

    @property
    def bugzilla_name(self):
        '''
        Helper to build release name according to Bugzilla rules
        '''
        name = self.name.lower()
        if name.startswith('esr'):
            name += str(self.version)
        return name

    def build_parameters_approved(self):
        '''
        Build parameters for uplift grafts
        '''
        statuses = 'fixed verified wontfix unaffected disabled'

        if self.bugzilla_name.startswith('esr'):
            # Special case for ESR
            # Can't use common
            parameters = {
                'order': 'cf_last_resolved',
                'field0-0-0': 'flagtypes.name',
                'type0-0-0': 'equals',
                'value0-0-0': 'approval-mozilla-{}+'.format(self.bugzilla_name),
                'field0-1-0': 'cf_status_firefox_{}'.format(self.bugzilla_name),
                'type0-1-0': 'nowordssubstr',
                'value0-1-0': statuses,
            }

        elif self.bugzilla_name in ('release', 'beta'):

            # Calc nightly version offset
            nightly_offset = self.bugzilla_name == 'release' and 2 or 1
            parameters = {
                'f1': 'OP',
                'f2': 'OP',
                'f3': 'flagtypes.name',
                'f5': 'CP',
                'f6': 'OP',
                'f7': 'cf_status_firefox{}'.format(self.version),
                'f8': 'CP',
                'f9': 'OP',
                'f10': 'cf_status_firefox{}'.format(self.version + nightly_offset),
                'f12': 'CP',
                'f14': 'CP',
                'o3': 'equals',
                'o7': 'nowordssubstr',
                'o10': 'anywordssubstr',
                'query_format': 'advanced',
                'v3': 'approval-mozilla-{}+'.format(self.bugzilla_name),
                'v7': statuses,
                'v10': 'fixed verified',
            }

            # Add specific release parameters
            # as a list of tuples (2 bug_status values)
            if self.bugzilla_name == 'release':
                parameters = list(parameters.items()) + [
                    ('bug_status', 'RESOLVED'),
                    ('bug_status', 'VERIFIED'),
                    ('resolution', 'FIXED'),
                ]

        else:
            # Don't support other versions
            parameters = {}

        return urllib.parse.urlencode(parameters)

    def build_parameters_pending(self):
        '''
        Build parameters for uplift bug search
        '''
        if self.bugzilla_name.startswith('esr'):
            # Esr releases
            approval = 'approval-{}'.format(self.bugzilla_name)
            v3 = 'approval-mozilla-{}?'.format(self.bugzilla_name)
        else:
            # Normal releases
            approval = 'approval-mozilla-{}'.format(self.bugzilla_name)
            v3 = 'approval-mozilla-{}?'.format(self.bugzilla_name)

        parameters = {
            # Common parameters
            'f0': 'OP',
            'f1': 'OP',
            'f10': 'requestees.login_name',
            'f11': 'CP',
            'f12': 'CP',
            'f2': 'flagtypes.name',
            'f3': 'flagtypes.name',
            'f4': 'flagtypes.name',
            'f5': 'flagtypes.name',
            'f6': 'CP',
            'f7': 'CP',
            'f8': 'OP',
            'f9': 'OP',
            'j1': 'OR',
            'j9': 'OR',
            'o10': 'substring',
            'o2': 'substring',
            'o3': 'substring',
            'o4': 'substring',
            'o5': 'substring',
            'query_format': 'advanced',

            # Version specific parameters
            'known_name': approval,
            'query_based_on': approval,
            'v3': v3,
        }

        return urllib.parse.urlencode(parameters)


class BugResult(db.Model):
    '''
    The cached result of an analysis run
    '''
    __tablename__ = 'uplift_backend_bug'

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
        '''
        List contributors with roles in one SQL query
        '''
        return \
            db.session \
            .query(Contributor, BugContributor) \
            .join(BugContributor) \
            .filter_by(bug_id=self.id) \
            .all()

    def delete(self):
        '''
        Delete bug and its dependencies
        '''
        # Delete links, avoid StaleDataError
        db.engine.execute(sa.text('delete from uplift_backend_analysis_bugs where bug_id = :bug_id'), bug_id=self.id)  # noqa
        db.engine.execute(sa.text('delete from uplift_backend_patch_status where bug_id = :bug_id'), bug_id=self.id)  # noqa

        # Delete the bug
        db.session.delete(self)
        db.session.commit()


class Contributor(db.Model):
    '''
    An active Mozilla contributor
    '''
    __tablename__ = 'uplift_backend_contributor'
    id = sa.Column(sa.Integer, primary_key=True)
    bugzilla_id = sa.Column(sa.Integer, unique=True)
    name = sa.Column(sa.String(250))
    email = sa.Column(sa.String(250))
    avatar_url = sa.Column(sa.String(250))
    karma = sa.Column(sa.Integer, default=0)
    comment_private = sa.Column(sa.Text, default='')
    comment_public = sa.Column(sa.Text, default='')


class BugContributor(db.Model):
    '''
    M2M link between contributor & bug
    '''
    __tablename__ = 'uplift_backend_contributor_bugs'
    __table_args__ = (
        sa.UniqueConstraint('contributor_id', 'bug_id', name='uniq_contrib_bug'),  # noqa
    )

    id = sa.Column(sa.Integer, primary_key=True)
    contributor_id = sa.Column(sa.Integer, sa.ForeignKey('uplift_backend_contributor.id'))  # noqa
    bug_id = sa.Column(sa.Integer, sa.ForeignKey('uplift_backend_bug.id'))  # noqa
    roles = sa.Column(sa.String(250))

    bug = db.relationship(BugResult, backref='contributors')
    contributor = db.relationship(Contributor, backref='bugs')


class MergeStatus(enum.Enum):
    failed = 'failed'
    merged = 'merged'
    skipped = 'skipped'


class PatchStatus(db.Model):
    '''
    Patch merge status at a specific time
    '''
    __tablename__ = 'uplift_backend_patch_status'
    __table_args__ = (
        sa.UniqueConstraint('bug_id', 'revision', 'revision_parent', 'branch', name='uniq_patch_status'),  # noqa
        sa.UniqueConstraint('bug_id', 'group', 'branch', 'revision', name='uniq_patch_status_group')  # noqa
    )

    id = sa.Column(sa.Integer, primary_key=True)
    group = sa.Column(sa.Integer, default=1, nullable=False)
    bug_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('uplift_backend_bug.id'),
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

    bug = db.relationship(BugResult, backref='patch_status')
