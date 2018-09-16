# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import datetime

import sqlalchemy as sa

import backend_common.db
import releng_mapper.config


class Project(backend_common.db.db.Model):
    '''
    Object-relational mapping between python class Project
    and database table "projects"
    '''
    __tablename__ = releng_mapper.config.APP_NAME + '_projects'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False, unique=True)


class Hash(backend_common.db.db.Model):
    '''
    Object-relational mapping between python class Hash
    and database table "hashes"
    '''
    __tablename__ = releng_mapper.config.APP_NAME + '_hashes'

    hg_changeset = sa.Column(sa.String(40), nullable=False)
    git_commit = sa.Column(sa.String(40), nullable=False)
    project_id = sa.Column(sa.Integer, sa.ForeignKey(Project.id), nullable=False)
    project = sa.orm.relationship(Project, primaryjoin=(project_id == Project.id))
    date_added = sa.Column(sa.Integer, nullable=False)

    project_name = property(lambda self: self.project.name)

    def as_json(self):
        result = {
            n: getattr(self, n)
            for n in ('git_commit', 'hg_changeset', 'project_name',)
        }
        result['date_added'] = datetime.utcfromtimestamp(self.date_added).isoformat()
        return result

    __table_args__ = (
        # TODO: (needs verification) all queries specifying a hash are for
        # (project, hash), so these aren't used
        sa.Index('hg_changeset', 'hg_changeset'),
        sa.Index('git_commit', 'git_commit'),
        # TODO: this index is a prefix of others and will never be used
        sa.Index('project_id', 'project_id'),
        sa.Index('project_id__date_added', 'project_id', 'date_added'),
        sa.Index('project_id__hg_changeset', 'project_id', 'hg_changeset', unique=True),
        sa.Index('project_id__git_commit', 'project_id', 'git_commit', unique=True),
    )

    __mapper_args__ = {
        # tell the SQLAlchemy ORM about one of the unique indexes; it doesn't
        # matter which
        'primary_key': [project_id, hg_changeset],
    }
