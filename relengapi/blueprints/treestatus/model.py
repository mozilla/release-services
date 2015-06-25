# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging

from relengapi.lib import db
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relation

from relengapi.blueprints.treestatus import types

log = logging.getLogger(__name__)


class DbTree(db.declarative_base('treestatus')):
    __tablename__ = 'trees'
    tree = Column(String(32), primary_key=True)
    status = Column(String(64), default="open", nullable=False)
    reason = Column(String(256), default="", nullable=False)
    message_of_the_day = Column(String(800), default="", nullable=False)

    def to_json(self):
        return types.JsonTree(
            tree=self.tree,
            status=self.status,
            reason=self.reason,
            message_of_the_day=self.message_of_the_day,
        )


class DbLog(db.declarative_base('treestatus')):
    __tablename__ = 'log'

    id = Column(Integer, primary_key=True)
    tree = Column(String(32), nullable=False, index=True)
    when = Column(DateTime, nullable=False, index=True)
    who = Column(String(100), nullable=False)
    action = Column(String(16), nullable=False)
    reason = Column(String(256), nullable=False)
    _tags = Column("tags", String(256), nullable=False)

    def __init__(self, tags=None, **kwargs):
        if tags is not None:
            kwargs['_tags'] = json.dumps(tags)
        super(DbLog, self).__init__(**kwargs)

    @hybrid_property
    def tags(self):
        return json.loads(self._tags)

    @tags.setter
    def set_tags(self, val):
        self._tags = json.dumps(val)

    def to_json(self):
        return types.JsonTreeLog(
            tree=self.tree,
            when=self.when,
            who=self.who,
            action=self.action,
            reason=self.reason,
            tags=self.tags,
        )


class DbToken(db.declarative_base('treestatus')):
    __tablename__ = 'tokens'
    who = Column(String(100), nullable=False, primary_key=True)
    token = Column(String(100), nullable=False)

    @classmethod
    def delete(cls, who):
        q = cls.__table__.delete(cls.who == who)
        q.execute()

    @classmethod
    def get(cls, who):
        q = cls.__table__.select(cls.who == who)
        result = q.execute().fetchone()
        return result


class DbStatusStack(db.declarative_base('treestatus')):
    __tablename__ = 'status_stacks'
    id = Column(Integer, primary_key=True)
    who = Column(String(100), nullable=False)
    reason = Column(String(256), nullable=False)
    when = Column(DateTime, nullable=False, index=True)
    status = Column(String(64), nullable=False)

    def to_json(self):
        return types.JsonStateChange(
            trees=[t.tree for t in self.trees],
            status=self.status,
            when=self.when,
            who=self.who,
            reason=self.reason,
            id=self.id,
        )


class DbStatusStackTree(db.declarative_base('treestatus')):
    __tablename__ = 'status_stack_trees'
    id = Column(Integer, primary_key=True)
    stack_id = Column(Integer, ForeignKey(DbStatusStack.id), index=True)
    tree = Column(String(32), nullable=False, index=True)
    last_state = Column(String(1024), nullable=False)

    stack = relation(DbStatusStack, backref='trees')


class DbUser(db.declarative_base('treestatus')):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_sheriff = Column(Boolean, nullable=False, default=False)

    @classmethod
    def get(cls, name):
        q = cls.__table__.select(cls.name == name)
        result = q.execute().fetchone()
        return result
