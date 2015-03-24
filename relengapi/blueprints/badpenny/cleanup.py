# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import logging

from flask import current_app
from relengapi.blueprints.badpenny import tables
from relengapi.lib import badpenny
from relengapi.lib import time

logger = logging.getLogger(__name__)


@badpenny.periodic_task(seconds=24 * 3600)
def cleanup_old_jobs(job_status):
    session = current_app.db.session('relengapi')
    Task = tables.BadpennyTask

    old_job_days = current_app.config.get('BADPENNY_OLD_JOB_DAYS', 7)
    old = time.now() - datetime.timedelta(days=old_job_days)
    deleted = 0

    for task in Task.query.all():
        # consider all but the most recent job
        jobs = reversed(task.jobs[1:])
        for job in jobs:
            if job.created_at < old:
                for log in job.logs:
                    session.delete(log)
                session.delete(job)
                deleted += 1

    if deleted:
        logger.info("removed %d old jobs", deleted)
        session.commit()
