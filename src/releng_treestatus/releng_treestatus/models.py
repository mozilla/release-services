# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json
import pytz
import sqlalchemy as sa

from sqlalchemy import types
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relation

from backend_common.db import db


class UTCDateTime(types.TypeDecorator):
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            # Convert to UTC
            value = pytz.UTC.normalize(value.astimezone(pytz.UTC))
            # MySQL stores datetimes without any timezone information, similar
            # to a naive Python datetime.  Passing it a tz-aware datetime
            # causes a warning ('Out of range value for column ..'), so we make
            # it naive.
            if dialect.name == 'mysql':
                value = value.replace(tzinfo=None)
        # else assume UTC
        return value

    def process_result_value(self, value, dialect):
        # We expect UTC dates back, so populate with tzinfo
        if value is not None:
            return value.replace(tzinfo=pytz.UTC)


class Tree(db.Model):

    __tablename__ = 'releng_treestatus_trees'

    tree = sa.Column(sa.String(32), primary_key=True)
    status = sa.Column(sa.String(64), default='open', nullable=False)
    reason = sa.Column(sa.Text, default='', nullable=False)
    message_of_the_day = sa.Column(sa.Text, default='', nullable=False)

    def to_dict(self):
        return dict(
            tree=self.tree,
            status=self.status,
            reason=self.reason,
            message_of_the_day=self.message_of_the_day,
        )


class Log(db.Model):

    __tablename__ = 'releng_treestatus_log'

    id = sa.Column(sa.Integer, primary_key=True)
    tree = sa.Column(sa.String(32), nullable=False, index=True)
    when = sa.Column(UTCDateTime, nullable=False, index=True)
    who = sa.Column(sa.Text, nullable=False)
    status = sa.Column(sa.String(64), nullable=False)
    reason = sa.Column(sa.Text, nullable=False)
    _tags = sa.Column('tags', sa.Text, nullable=False)

    def __init__(self, tags=None, **kwargs):
        if tags is not None:
            kwargs['_tags'] = json.dumps(tags)
        super(Log, self).__init__(**kwargs)

    @hybrid_property
    def tags(self):
        return json.loads(self._tags)

    def to_dict(self):
        return dict(
            tree=self.tree,
            when=self.when,
            who=self.who,
            status=self.status,
            reason=self.reason,
            tags=self.tags,
        )


class StatusChange(db.Model):

    __tablename__ = 'releng_treestatus_changes'

    id = sa.Column(sa.Integer, primary_key=True)
    who = sa.Column(sa.Text, nullable=False)
    reason = sa.Column(sa.Text, nullable=False)
    when = sa.Column(UTCDateTime, nullable=False, index=True)
    status = sa.Column(sa.String(64), nullable=False)

    def to_dict(self):
        return dict(
            trees=[t.tree for t in self.trees],
            status=self.status,
            when=self.when,
            who=self.who,
            reason=self.reason,
            id=self.id,
        )


class StatusChangeTree(db.Model):

    __tablename__ = 'releng_treestatus_change_trees'

    id = sa.Column(sa.Integer, primary_key=True)
    stack_id = sa.Column(sa.Integer,
                         sa.ForeignKey(StatusChange.id), index=True)
    tree = sa.Column(sa.String(32), nullable=False, index=True)
    last_state = sa.Column(sa.Text, nullable=False)

    stack = relation(StatusChange, backref='trees')
