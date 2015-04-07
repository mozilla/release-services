# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import traceback

from flask import current_app
from relengapi.blueprints.badpenny import tables
from relengapi.lib import badpenny
from relengapi.lib import celery
from relengapi.lib import time

logger = logging.getLogger(__name__)


def submit_job(task_name, job_id):
    # make a request via celery, but ignore the result
    _run_job.delay(task_name, job_id)


class JobStatus(object):

    def __init__(self, task_name, job):
        self.task_name = task_name
        self.job = job
        self._log_output = []

    def log_message(self, message):
        """Add MESSAGE to the log output of the job"""
        logger.debug("%r: %s" % (self.task_name, message))
        self._log_output.append(message)

    def _start(self):
        self.job.started_at = time.now()
        current_app.db.session('relengapi').commit()

    def _finish(self, successful):
        session = current_app.db.session('relengapi')

        self.job.completed_at = time.now()
        self.job.successful = successful
        if self._log_output:
            content = u'\n'.join(self._log_output)
            l = tables.BadpennyJobLog(id=self.job.id, content=content)
            session.add(l)
        session.commit()


@celery.task(ignore_result=True)
def _run_job(task_name, job_id):
    task = badpenny.Task.get(task_name)
    if not task:
        logger.warning("No such task %r; request dropped", task_name)
        return

    job = tables.BadpennyJob.query.filter(
        tables.BadpennyJob.id == job_id).first()
    if not job:
        logger.warning("No job with id %r; request dropped", job_id)
        return

    job_status = JobStatus(task_name, job)

    job_status._start()

    logger.info("Running task %r id %r" % (task_name, job_id))
    try:
        task.task_func(job_status)
    except Exception:
        logger.exception("Job %r failed", job_id)
        job_status.log_message(traceback.format_exc())
        job_status._finish(successful=False)
        return

    job_status._finish(successful=True)
