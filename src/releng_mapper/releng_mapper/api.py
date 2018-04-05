# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import calendar
import re
import time
from typing import Optional
from typing import Tuple

import dateutil.parser
from flask import Response
from flask import current_app
from flask import request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import Conflict
from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import UnsupportedMediaType

from backend_common.auth import auth
from cli_common import log

from .models import Hash
from .models import Project

logger = log.get_logger(__name__)

AUTHENTICATION_SCOPE_PREFIX = 'project:releng:services/releng_mapper/permission/'


@auth.require_scopes([AUTHENTICATION_SCOPE_PREFIX + 'project/insert'])
def post_project(project: str) -> dict:
    session = current_app.db.session
    p = Project(name=project)
    session.add(p)

    try:
        session.commit()

    except (IntegrityError, ProgrammingError,):
        raise Conflict('Project {} could not be inserted into the database'.format(project))

    return {}


@auth.require_scopes([AUTHENTICATION_SCOPE_PREFIX + 'mapping/insert'])
def post_hg_git_mapping(project: str, git_commit: str, hg_changeset: str) -> dict:
    session = current_app.db.session
    proj = _get_project(session, project)  # can raise HTTP 404 or HTTP 500
    _add_hash(session, git_commit, hg_changeset, proj)  # can raise HTTP 400
    try:
        session.commit()
        q = Hash.query.join(Project).filter(_project_filter(project))
        q = q.filter(text('git_commit == :commit')).params(commit=git_commit)
        return q.one().as_json()

    except IntegrityError:
        raise Conflict('Provided mapping {} {} for project {} already exists and '
                       'cannot be reinserted'.format(git_commit, hg_changeset, project))

    except NoResultFound:
        raise InternalServerError('Provided mapping {} {} for project {} could not be inserted '
                                  'into the database'.format(git_commit, hg_changeset, project))

    except MultipleResultsFound:
        raise InternalServerError('Provided mapping {git_commit} {hg_changeset} for project {project} has been inserted'
                                  ' into the database multiple times'.format(git_commit=git_commit,
                                                                             hg_changeset=hg_changeset,
                                                                             project=project))


@auth.require_scopes([AUTHENTICATION_SCOPE_PREFIX + 'mapping/insert'])
def post_insert_many_ignoredups(project: str, body: str) -> dict:
    session = current_app.db.session
    return _insert_many(project, body.encode(), session, ignore_dups=True)


@auth.require_scopes([AUTHENTICATION_SCOPE_PREFIX + 'mapping/insert'])
def post_insert_many(project: str, body: str) -> dict:
    session = current_app.db.session
    return _insert_many(project, body.encode(), session, ignore_dups=False)


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


def get_mapfile_since(projects: str, since: str) -> Tuple[str, int, dict]:
    try:
        since_dt = dateutil.parser.parse(since)

    except ValueError as e:
        raise BadRequest('Invalid date %s specified; see https://labix.org/python-dateutil: %s' % (since, str(e)))

    since_epoch = calendar.timegm(since_dt.utctimetuple())

    q = Hash.query.join(Project).filter(_project_filter(projects))
    q = q.order_by(Hash.hg_changeset)
    q = q.filter(Hash.date_added > since_epoch)

    return _stream_mapfile(q)


def get_full_mapfile(projects: str) -> Tuple[str, int, dict]:
    q = Hash.query.join(Project).filter(_project_filter(projects))
    q = q.order_by(Hash.hg_changeset)

    return _stream_mapfile(q)


def get_revision(projects: str, vcs_type: str, commit: str) -> str:
    _check_well_formed_sha(vcs_type, commit, exact_length=None)  # can raise http 400
    q = Hash.query.join(Project).filter(_project_filter(projects))
    if vcs_type == 'git':
        q = q.filter(text('git_commit like :cspatttern')).params(cspatttern=commit + '%')

    elif vcs_type == 'hg':
        q = q.filter(text('hg_changeset like :cspatttern')).params(cspatttern=commit + '%')

    try:
        row = q.one()
    except NoResultFound:
        if vcs_type == 'git':
            raise NotFound('No hg changeset found for git commit id {} in project(s) {}'.format(commit, projects))

        elif vcs_type == 'hg':
            raise NotFound('No git commit found for hg changeset {} in project(s) {}'.format(commit, projects))

    except MultipleResultsFound:
        raise InternalServerError('Internal error - multiple results returned for {} commit {} in project {} - '
                                  'this should not be possible in database'.format(vcs_type, commit, projects))

    return '%s %s' % (row.git_commit, row.hg_changeset)


def _project_filter(projects_arg):
    '''Helper method that returns the SQLAlchemy filter expression for the
    project name(s) specified. This can be a comma-separated list, which is
    the way we combine queries across multiple projects.
    Args:
        projects_arg: Comma-separated list of project names
    Returns:
        A SQLAlchemy filter expression
    '''
    if ',' in projects_arg:
        return Project.name.in_(projects_arg.split(','))
    else:
        return Project.name == projects_arg


def _stream_mapfile(query) -> Tuple[str, int, dict]:
    '''Helper method to build a map file from a SQLAlchemy query.
    Args:
        query: SQLAlchemy query
    Returns:
        * Text output: 40 characters git commit SHA, a space,
          40 characters hg changeset SHA, a newline (streamed); or
        * HTTP 404: if the query returns no results
    '''
    # this helps keep memory use down a little, but the DBAPI still loads
    # the entire result set into memory..
    # http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per
    query = query.yield_per(100)

    if query.count() == 0:
        raise NotFound('No mappings found.')

    def contents():
        for r in query:
            yield '{} {}'.format(r.git_commit, r.hg_changeset) + '\n'

    if contents:
        return Response(contents(), mimetype='text/plain')


def _check_well_formed_sha(vcs: str, sha: str, exact_length: Optional[int]=40) -> None:
    '''Helper method to check for a well-formed SHA.
    Args:
        vcs: Name of the vcs system ('hg' or 'git')
        sha: String to check against the well-formed SHA regex
        exact_length: Number of characters SHA should be, or
                      None if exact length is not required
    Returns:
        None
    Exceptions:
        HTTP 400: Malformed SHA or unknown vcs
    '''
    if vcs not in ('git', 'hg'):
        raise BadRequest('Unknown vcs type {}'.format(vcs))

    rev_regex = re.compile('''^[a-f0-9]{1,40}$''')
    if sha is None:
        raise BadRequest('{} SHA is <None>'.format(vcs))

    elif sha == '':
        raise BadRequest('{} SHA is an empty string'.format(vcs))

    elif not rev_regex.match(sha):
        raise BadRequest('{} SHA contains bad characters: "{}"'.format(vcs, str(sha)))

    if exact_length is not None and len(sha) != exact_length:
        raise BadRequest('{vcs} SHA should be {correct} characters long, but is {actual} characters long: "{sha}"'.format(
            vcs=vcs,
            correct=exact_length,
            actual=len(sha),
            sha=str(sha)
        ))


def _get_project(session, project: str) -> Project:
    '''Helper method to return Project class for a project with the given name.
    Args:
        session: SQLAlchemy ORM Session object
        project: Name of the project (e.g. 'build-tools')
    Returns:
        the corresponding python Project object
    Exceptions:
        HTTP 404: Project could not be found
        HTTP 500: Multiple projects with same name found
    '''
    try:
        return session.query(Project).filter(Project.name == project).one()

    except MultipleResultsFound:
        raise InternalServerError('Multiple projects with name {} found in database'.format(project))

    except NoResultFound:
        raise NotFound('Could not find project {} in database'.format(project))


def _add_hash(session, git_commit: str, hg_changeset: str, project: str) -> None:
    '''Helper method to add a git-hg mapping into the current SQLAlchemy ORM session.
    Args:
        session: SQLAlchemy ORM Session object
        git_commit: String of the 40 character SHA of the git commit
        hg_changeset: String of the 40 character SHA of the hg changeset
        project: String of the name of the project (e.g. 'build-tools')
    Exceptions:
        HTTP 400: Malformed SHA
    '''
    _check_well_formed_sha('git', git_commit)  # can raise http 400
    _check_well_formed_sha('hg', hg_changeset)  # can raise http 400
    h = Hash(git_commit=git_commit, hg_changeset=hg_changeset, project=project, date_added=time.time())
    session.add(h)


def _insert_many(project: str, body: bytes, session, ignore_dups: bool=False) -> dict:
    '''Update the database with many git-hg mappings.
    Args:
        project: Single project name string
        ignore_dups: Boolean; if False, abort on duplicate entries without inserting
        anything
    Returns:
        An empty json response body
    Exceptions:
        HTTP 400: Malformed SHA
        HTTP 404: Project not found
        HTTP 409: ignore_dups=False and there are duplicate entries
        HTTP 415: Request content-type is not 'text/plain'
        HTTP 500: Multiple projects found with matching project name
    '''
    if request.content_type != 'text/plain':
        raise UnsupportedMediaType('HTTP request header "Content-Type" must be set to "text/plain"')

    proj = _get_project(session, project)  # can raise HTTP 404 or HTTP 500
    for line in body.decode('utf-8').split('\n'):
        line = line.rstrip()

        try:
            git_commit, hg_changeset = line.split(' ')

        except ValueError:
            logger.error('Received input line: "%s" for project %s', line, project)
            logger.error('Was expecting an input line such as '
                         '"686a558fad7954d8481cfd6714cdd56b491d2988 fef90029cb654ad9848337e262078e403baf0c7a"')
            logger.error('i.e. where the first hash is a git commit SHA and the second hash is a mercurial changeset SHA')
            raise BadRequest('Input line "{}" received for project {} did not contain a space'.format(line, project))

        _add_hash(session, git_commit, hg_changeset, proj)  # can raise HTTP 400

        if ignore_dups:
            try:
                session.commit()

            except IntegrityError:
                session.rollback()

    if not ignore_dups:
        try:
            session.commit()

        except IntegrityError:
            session.rollback()
            raise Conflict('Some of the given mappings for project {} already exist'.format(project))

    return {}
