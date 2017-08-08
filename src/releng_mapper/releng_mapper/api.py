# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import calendar
import dateutil
from flask import current_app
from .models import Project, Hash, _get_project, _add_hash, _project_filter, \
    _insert_many, _check_well_formed_sha, _stream_mapfile
from werkzeug.exceptions import BadRequest, Conflict, InternalServerError, NotFound, UnsupportedMediaType
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


def post_project(project: str) -> dict:
    session = current_app.db.session
    p = Project(name=project)
    session.add(p)

    try:
        session.commit()

    except (IntegrityError, ProgrammingError,):
        raise Conflict('Project {} could not be inserted into the database'.format(project))

    return {}


def post_hg_git_mapping(project: str, git_commit: str, hg_changeset: str) -> dict:
    session = current_app.db.session
    proj = _get_project(session, project)  # can raise HTTP 404 or HTTP 500
    _add_hash(session, git_commit, hg_changeset, proj)  # can raise HTTP 400
    try:
        session.commit()
        q = Hash.query.join(Project).filter(_project_filter(project))
        q = q.filter(text("git_commit == :commit")).params(commit=git_commit)
        return q.one().as_json()

    except IntegrityError:
        raise Conflict("Provided mapping {} {} for project {} already exists and "
                       "cannot be reinserted".format(git_commit, hg_changeset, project))

    except NoResultFound:
        raise InternalServerError("Provided mapping {} {} for project {} could not be inserted "
                                  "into the database".format(git_commit, hg_changeset, project))

    except MultipleResultsFound:
        raise InternalServerError("Provided mapping {git_commit} {hg_changeset} for project {project} has been inserted"
                                  " into the database multiple times".format(git_commit=git_commit,
                                                                             hg_changeset=hg_changeset,
                                                                             project=project))


def post_insert_many_ignoredups(project: str, body: str) -> dict:
    session = current_app.db.session
    return _insert_many(project, body, session, ignore_dups=True)


def post_insert_many(project: str, body: str) -> dict:
    session = current_app.db.session
    return _insert_many(project, body, session, ignore_dups=False)


def get_projects() -> dict:
    session = current_app.db.session
    all_projects = session.query(Project).all()
    if not all_projects:
        raise NotFound('Could not find any projects in the database.')

    return {
        'projects': [
            project.name
            for project in all_projects
        ],
    }


def get_mapfile_since(projects: str, since: str) -> str:
    try:
        since_dt = dateutil.parser.parse(since)

    except ValueError as e:
        raise BadRequest('Invalid date %s specified; see https://labix.org/python-dateutil: %s' % (since, e.message))

    since_epoch = calendar.timegm(since_dt.utctimetuple())

    q = Hash.query.join(Project).filter(_project_filter(projects))
    q = q.order_by(Hash.hg_changeset)
    q = q.filter(Hash.date_added > since_epoch)

    return _stream_mapfile(q)


def get_full_mapfile(projects: str) -> str:
    q = Hash.query.join(Project).filter(_project_filter(projects))
    q = q.order_by(Hash.hg_changeset)

    return _stream_mapfile(q)


def get_revision(projects: str, vcs_type: str, commit: str) -> str:
    # (documentation in relengapi/docs/usage/mapper.rst)
    _check_well_formed_sha(vcs_type, commit, exact_length=None)  # can raise http 400
    q = Hash.query.join(Project).filter(_project_filter(projects))
    if vcs_type == "git":
        q = q.filter(text("git_commit like :cspatttern")).params(cspatttern=commit + "%")

    elif vcs_type == "hg":
        q = q.filter(text("hg_changeset like :cspatttern")).params(cspatttern=commit + "%")

    try:
        row = q.one()
        return "%s %s" % (row.git_commit, row.hg_changeset)

    except NoResultFound:
        if vcs_type == "git":
            raise NotFound("No hg changeset found for git commit id %s in project(s) %s" % (commit, projects))

        elif vcs_type == "hg":
            raise NotFound("No git commit found for hg changeset %s in project(s) %s" % (commit, projects))

    except MultipleResultsFound:
        raise InternalServerError("Internal error - multiple results returned for %s commit %s in project %s - "
                                  "this should not be possible in database" % (vcs_type, commit, projects))

