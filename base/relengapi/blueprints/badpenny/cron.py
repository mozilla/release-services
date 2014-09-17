# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from flask import Blueprint
from flask import current_app
from relengapi.blueprints.badpenny import execution
from relengapi.blueprints.badpenny import tables
from relengapi.lib import badpenny
from relengapi.lib import subcommands
from relengapi.lib import time

bp = Blueprint('base', __name__)
logger = logging.getLogger(__name__)


class BadpennyCron(subcommands.Subcommand):

    def make_parser(self, subparsers):
        parser = subparsers.add_parser(
            'badpenny-cron', help='Trigger periodic tasks')
        return parser

    def sync_tasks(self):
        """Synchronize tasks defined in code into the DB"""
        for task in badpenny.Task.list():
            bpt = tables.BadpennyTask.as_unique(
                current_app.db.session('relengapi'), name=task.name)
            task.task_id = bpt.id
        current_app.db.session('relengapi').commit()

    def runnable_tasks(self, now):
        """Determine the set of runnable tasks at time NOW, yielding badpenny.Task instances"""
        for task in badpenny.Task.list():
            bpt = tables.BadpennyTask.query.filter(
                tables.BadpennyTask.name == task.name).first()
            if not bpt:
                continue  # weird..
            if task.runnable_now(bpt, now):
                yield task

    def run_task(self, task):
        """Actually run a task, inserting a DB row and generating the celery task."""
        job = tables.BadpennyJob(
            task_id=task.task_id,
            created_at=time.now())
        current_app.db.session('relengapi').add(job)
        current_app.db.session('relengapi').commit()

        execution.submit_job(task_name=task.name, job_id=job.id)

    def run(self, parser, args):
        logger.info("Synchronizing tasks into the DB")
        self.sync_tasks()

        logger.info("Creating jobs for overdue tasks")
        now = time.now()
        for task in self.runnable_tasks(now):
            logger.info("Running %r", task.name)
            self.run_task(task)
