# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime

import structlog
from flask import current_app

from relengapi.blueprints.badpenny import tables
from relengapi.lib import badpenny
from relengapi.lib import time

logger = structlog.get_logger()


@badpenny.periodic_task(seconds=24 * 3600)
def cleanup_old_jobs(job_status):
    session = current_app.db.session('relengapi')
    Task = tables.BadpennyTask
    Job = tables.BadpennyJob

    old_job_days = current_app.config.get('BADPENNY_OLD_JOB_DAYS', 7)
    old = time.now() - datetime.timedelta(days=old_job_days)
    deleted = 0

    for task in Task.query.all():
        # Iterate until we find a job that's not too old.  Only
        # delete on the next iteration to avoid deleting the most
        # recent job.
        to_delete = None
        for job in Job.query.filter(Job.task_id == task.id).order_by(Job.created_at):
            if to_delete:
                for log in to_delete.logs:
                    session.delete(log)
                session.delete(to_delete)
                to_delete = None
                deleted += 1

            if job.created_at < old:
                to_delete = job
            else:
                break

    if deleted:
        logger.info("removed %d old jobs", deleted)
        session.commit()
