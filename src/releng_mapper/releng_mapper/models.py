# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
from backend_common.db import db
from .config import PROJECT_PATH_NAME
from sqlalchemy import orm, Column, ForeignKey, Index, Integer, String
from cli_common import log


logger = log.get_logger(__name__)


class Project(db.Model):
    '''
    Object-relational mapping between python class Project
    and database table "projects"
    '''
    __tablename__ = PROJECT_PATH_NAME + '_projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)


class Hash(db.Model):
    '''
    Object-relational mapping between python class Hash
    and database table "hashes"
    '''
    __tablename__ = PROJECT_PATH_NAME + '_hashes'

    hg_changeset = Column(String(40), nullable=False)
    git_commit = Column(String(40), nullable=False)
    project_id = Column(Integer, ForeignKey(Project.id), nullable=False)
    project = orm.relationship(Project, primaryjoin=(project_id == Project.id))
    date_added = Column(Integer, nullable=False)

    project_name = property(lambda self: self.project.name)

    def as_json(self):
        return {
            n: getattr(self, n)
            for n in ('git_commit', 'hg_changeset', 'date_added', 'project_name',)
        }

    __table_args__ = (
        # TODO: (needs verification) all queries specifying a hash are for
        # (project, hash), so these aren't used
        Index('hg_changeset', 'hg_changeset'),
        Index('git_commit', 'git_commit'),
        # TODO: this index is a prefix of others and will never be used
        Index('project_id', 'project_id'),
        Index('project_id__date_added', 'project_id', 'date_added'),
        Index('project_id__hg_changeset', 'project_id', 'hg_changeset', unique=True),
        Index('project_id__git_commit', 'project_id', 'git_commit', unique=True),
    )

    __mapper_args__ = {
        # tell the SQLAlchemy ORM about one of the unique indexes; it doesn't
        # matter which
        'primary_key': [project_id, hg_changeset],
    }
