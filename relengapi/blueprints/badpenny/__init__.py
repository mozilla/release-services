# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from flask import Blueprint
from flask import current_app
from flask import url_for
from relengapi import apimethod
from relengapi import p
from relengapi.blueprints.badpenny import cleanup
from relengapi.blueprints.badpenny import cron
from relengapi.blueprints.badpenny import execution
from relengapi.blueprints.badpenny import rest
from relengapi.blueprints.badpenny import tables
from relengapi.lib import angular
from relengapi.lib import api
from relengapi.lib import permissions
from relengapi.lib import time
from werkzeug.exceptions import NotFound

logger = logging.getLogger(__name__)
bp = Blueprint('badpenny', __name__,
               static_folder='static',
               template_folder='templates')

p.base.badpenny.view.doc('See scheduled tasks and logs of previous jobs')
p.base.badpenny.run.doc('Force a run of a badpenny task')


def permitted():
    return permissions.can(p.base.badpenny.view)
bp.root_widget_template(
    'badpenny_root_widget.html', priority=100, condition=permitted)


@bp.route('/')
@p.base.badpenny.view.require()
def root():
    return angular.template('badpenny.html',
                            url_for('.static', filename='badpenny.js'),
                            url_for('.static', filename='badpenny.css'),
                            tasks=api.get_data(list_tasks))


@bp.route('/tasks')
@apimethod([rest.BadpennyTask], bool)
@p.base.badpenny.view.require()
def list_tasks(all=False):
    """List all badpenny tasks.  With "?all=1", include inactive tasks."""
    rv = [t.to_jsontask() for t in tables.BadpennyTask.query.all()]
    if not all:
        rv = [t for t in rv if t.active]
    return rv


@bp.route('/tasks/<task_name>')
@apimethod(rest.BadpennyTask, unicode)
@p.base.badpenny.view.require()
def get_task(task_name):
    """Get information on a badpenny task by name."""
    t = tables.BadpennyTask.query.filter(
        tables.BadpennyTask.name == task_name).first()
    if not t:
        raise NotFound
    return t.to_jsontask(with_jobs=True)


@bp.route('/tasks/<task_name>/run-now', methods=['POST'])
@apimethod(rest.BadpennyJob, unicode)
@p.base.badpenny.run.require()
def run_task_now(task_name):
    """Force the given badpenny task to run now."""
    t = tables.BadpennyTask.query.filter(
        tables.BadpennyTask.name == task_name).first()
    if not t:
        raise NotFound

    session = current_app.db.session('relengapi')
    job = tables.BadpennyJob(task=t, created_at=time.now())
    session.add(job)
    session.commit()

    execution.submit_job(task_name=t.name, job_id=job.id)
    return job.to_jsonjob()


@bp.route('/jobs')
@apimethod([rest.BadpennyJob])
@p.base.badpenny.view.require()
def list_jobs():
    """List all badpenny jobs."""
    return [t.to_jsonjob() for t in tables.BadpennyJob.query.all()]


@bp.route('/jobs/<job_id>')
@apimethod(rest.BadpennyJob, int)
@p.base.badpenny.view.require()
def get_job(job_id):
    """Get information on a badpenny job by its ID.  Use this to poll for job
    completion."""
    j = tables.BadpennyJob.query.filter(
        tables.BadpennyJob.id == job_id).first()
    if not j:
        raise NotFound
    return j.to_jsonjob()


@bp.route('/jobs/<job_id>/logs')
@apimethod(rest.BadpennyJobLog, int)
@p.base.badpenny.view.require()
def get_job_logs(job_id):
    """Get logs for a badpenny job by its ID."""
    j = tables.BadpennyJobLog.query.filter(
        tables.BadpennyJobLog.id == job_id).first()
    if not j:
        raise NotFound
    return rest.BadpennyJobLog(content=j.content)

# Flask is fond of module-level code, which means imports have side-effects,
# which upsets pyflakes.
_hush_pyflakes = [cron, cleanup]
