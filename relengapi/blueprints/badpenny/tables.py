# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa

from relengapi.blueprints.badpenny import rest
from relengapi.lib import badpenny
from relengapi.lib import db


class BadpennyJobLog(db.declarative_base('relengapi')):
    __tablename__ = 'badpenny_job_logs'

    id = sa.Column(sa.Integer, sa.ForeignKey('badpenny_jobs.id'),
                   primary_key=True)

    # 'logs' is free-form, hopefully brief, log text
    content = sa.Column(sa.Text())


class BadpennyJob(db.declarative_base('relengapi')):
    __tablename__ = 'badpenny_jobs'

    id = sa.Column(sa.Integer, primary_key=True)
    task_id = sa.Column(sa.Integer, sa.ForeignKey('badpenny_tasks.id'),
                        nullable=False)
    task = sa.orm.relationship('BadpennyTask')

    created_at = sa.Column(db.UTCDateTime(timezone=True), nullable=False)
    started_at = sa.Column(db.UTCDateTime(timezone=True), nullable=True)
    completed_at = sa.Column(db.UTCDateTime(timezone=True), nullable=True)
    successful = sa.Column(sa.Boolean())

    # note that there's never more than one log due to the unique id, but
    # SQLAlchemy still models it as a list
    logs = sa.orm.relationship('BadpennyJobLog')

    def to_jsonjob(self):
        return rest.BadpennyJob(id=self.id,
                                task_name=self.task.name,
                                created_at=self.created_at,
                                started_at=self.started_at,
                                completed_at=self.completed_at,
                                successful=self.successful)


class BadpennyTask(db.declarative_base('relengapi'), db.UniqueMixin):
    __tablename__ = 'badpenny_tasks'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)

    # all other data about a task is determined from runtime information (that
    # is, from the decorated function itself)

    jobs = sa.orm.relationship('BadpennyJob')

    @property
    def last_success(self):
        # TODO: get this value as part of the DB query for the task
        job = BadpennyJob.query. \
            filter(BadpennyJob.task_id == self.id). \
            order_by(sa.desc(BadpennyJob.created_at)). \
            limit(1). \
            first()
        if not job:
            return -1
        elif job.successful:
            return 1
        else:
            return 0

    @classmethod
    def unique_filter(cls, query, name):
        return query.filter(BadpennyTask.name == name)

    @classmethod
    def unique_hash(cls, name):
        return name

    def to_jsontask(self, with_jobs=False):
        runtime_task = badpenny.Task.get(self.name)
        task = rest.BadpennyTask(name=self.name, last_success=self.last_success,
                                 active=bool(runtime_task))
        if runtime_task:
            task.schedule = runtime_task.schedule
        if with_jobs:
            task.jobs = [j.to_jsonjob() for j in self.jobs]
        return task
