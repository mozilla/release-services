# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import calendar
import dateutil.parser
import logging
import re
import sqlalchemy as sa
import time

from flask import Blueprint
from flask import Response
from flask import abort
from flask import g
from flask import jsonify
from flask import request
from relengapi.lib import db
from sqlalchemy import orm
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from relengapi import p

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)
bp = Blueprint('mapper', __name__)

p.mapper.mapping.insert.doc("Allows new hg-git mappings to be inserted "
                            "into mapper db (hashes table)")
p.mapper.project.insert.doc("Allows new projects to be inserted into "
                            "mapper db (projects table)")

# TODO: replace abort with a custom exception
# - http://flask.pocoo.org/docs/patterns/apierrors/


class Project(db.declarative_base('mapper')):

    """Object-relational mapping between python class Project
    and database table "projects"
    """
    __tablename__ = 'projects'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False, unique=True)


class Hash(db.declarative_base('mapper')):

    """Object-relational mapping between python class Hash
    and database table "hashes"
    """
    __tablename__ = 'hashes'
    hg_changeset = sa.Column(sa.String(40), nullable=False)
    git_commit = sa.Column(sa.String(40), nullable=False)
    project_id = sa.Column(
        sa.Integer, sa.ForeignKey('projects.id'), nullable=False)
    project = orm.relationship(Project, primaryjoin=(project_id == Project.id))
    # project = orm.relationship(Project, backref=orm.backref('hashes', order_by=id))
    date_added = sa.Column(sa.Integer, nullable=False)

    project_name = property(lambda self: self.project.name)

    def as_json(self):
        return jsonify(**{n: getattr(self, n)
                          for n in ('git_commit', 'hg_changeset',
                                    'date_added', 'project_name')})

    __table_args__ = (
        # TODO: (needs verification) all queries specifying a hash are for
        # (project, hash), so these aren't used
        sa.Index('hg_changeset', 'hg_changeset'),
        sa.Index('git_commit', 'git_commit'),
        # TODO: this index is a prefix of others and will never be used
        sa.Index('project_id', 'project_id'),
        sa.Index('project_id__date_added', 'project_id', 'date_added'),
        sa.Index('project_id__hg_changeset', 'project_id',
                 'hg_changeset', unique=True),
        sa.Index(
            'project_id__git_commit', 'project_id', 'git_commit', unique=True),
    )

    __mapper_args__ = {
        # tell the SQLAlchemy ORM about one of the unique indexes; it doesn't
        # matter which
        'primary_key': [project_id, hg_changeset],
    }


def _project_filter(projects_arg):
    """Helper method that returns the SQLAlchemy filter expression for the
    project name(s) specified. This can be a comma-separated list, which is
    the way we combine queries across multiple projects.

    Args:
        projects_arg: Comma-separated list of project names

    Returns:
        A SQLAlchemy filter expression
    """
    if ',' in projects_arg:
        return Project.name.in_(projects_arg.split(','))
    else:
        return Project.name == projects_arg


def _build_mapfile(query):
    """Helper method to build a map file from a SQLAlchemy query.
    Args:
        query: SQLAlchemy query

    Returns:
        * Text output: 40 characters git commit SHA, a space,
          40 characters hg changeset SHA, a newline; or
        * None: if the query returns no results
    """
    contents = '\n'.join('%s %s' % (r.git_commit, r.hg_changeset)
                         for r in query)
    if contents:
        return Response(contents + '\n', mimetype='text/plain')


def _check_well_formed_sha(vcs, sha, exact_length=40):
    """Helper method to check for a well-formed SHA.
    Args:
        vcs: Name of the vcs system ('hg' or 'git')
        sha: String to check against the well-formed SHA regex
        exact_length: Number of characters SHA should be, or
                      None if exact length is not required

    Returns:
        None

    Exceptions:
        HTTP 400: Malformed SHA or unknown vcs
    """
    if vcs not in ("git", "hg"):
        abort(400, "Unknown vcs type %s" % vcs)
    rev_regex = re.compile('''^[a-f0-9]{1,40}$''')
    if sha is None:
        abort(400, "%s SHA is <None>" % vcs)
    elif sha == "":
        abort(400, "%s SHA is an empty string" % vcs)
    elif not rev_regex.match(sha):
        abort(400, "%s SHA contains bad characters: '%s'" % (vcs, str(sha)))
    if exact_length is not None and len(sha) != exact_length:
        abort(400, "%s SHA should be %s characters long, but is %s characters long: '%s'"
              % (vcs, exact_length, len(sha), str(sha)))


def _get_project(session, project):
    """Helper method to return Project class for a project with the given name.

    Args:
        session: SQLAlchemy ORM Session object
        project: Name of the project (e.g. 'build-tools')

    Returns:
        the corresponding python Project object

    Exceptions:
        HTTP 404: Project could not be found
        HTTP 500: Multiple projects with same name found
    """
    try:
        return Project.query.filter_by(name=project).one()
    except MultipleResultsFound:
        abort(500, "Multiple projects with name %s found in database" %
              project)
    except NoResultFound:
        abort(404, "Could not find project %s in database" % project)


def _add_hash(session, git_commit, hg_changeset, project):
    """Helper method to add a git-hg mapping into the current SQLAlchemy ORM session.

    Args:
        session: SQLAlchemy ORM Session object
        git_commit: String of the 40 character SHA of the git commit
        hg_changeset: String of the 40 character SHA of the hg changeset
        project: String of the name of the project (e.g. 'build-tools')

    Exceptions:
        HTTP 400: Malformed SHA
    """
    _check_well_formed_sha('git', git_commit)  # can raise http 400
    _check_well_formed_sha('hg', hg_changeset)  # can raise http 400
    h = Hash(git_commit=git_commit, hg_changeset=hg_changeset, project=project,
             date_added=time.time())
    session.add(h)


@bp.route('/<projects>/rev/<vcs_type>/<commit>')
def get_rev(projects, vcs_type, commit):
    # (documentation in relengapi/docs/usage/mapper.rst)
    _check_well_formed_sha(vcs_type, commit, exact_length=None)  # can raise http 400
    q = Hash.query.join(Project).filter(_project_filter(projects))
    if vcs_type == "git":
        q = q.filter(sa.text("git_commit like :cspatttern")).params(
            cspatttern=commit + "%")
    elif vcs_type == "hg":
        q = q.filter(sa.text("hg_changeset like :cspatttern")).params(
            cspatttern=commit + "%")
    try:
        row = q.one()
        return "%s %s" % (row.git_commit, row.hg_changeset)
    except NoResultFound:
        if vcs_type == "git":
            abort(404, "No hg changeset found for git commit id %s in project(s) %s"
                  % (commit, projects))
        elif vcs_type == "hg":
            abort(404, "No git commit found for hg changeset %s in project(s) %s"
                  % (commit, projects))
    except MultipleResultsFound:
        abort(500, "Internal error - multiple results returned for %s commit %s"
              "in project %s - this should not be possible in database"
              % (vcs_type, commit, projects))


@bp.route('/<projects>/mapfile/full')
def get_full_mapfile(projects):
    # (documentation in relengapi/docs/usage/mapper.rst)
    q = Hash.query.join(Project).filter(_project_filter(projects))
    q = q.order_by(Hash.hg_changeset)
    mapfile = _build_mapfile(q)
    if not mapfile:
        abort(404, 'No results found in database for requested map file')
    return mapfile


@bp.route('/<projects>/mapfile/since/<since>')
def get_mapfile_since(projects, since):
    # (documentation in relengapi/docs/usage/mapper.rst)
    try:
        since_dt = dateutil.parser.parse(since)
    except ValueError as e:
        abort(400, 'Invalid date %s specified; see https://labix.org/python-dateutil: %s'
              % (since, e.message))
    since_epoch = calendar.timegm(since_dt.utctimetuple())
    q = Hash.query.join(Project).filter(_project_filter(projects))
    q = q.order_by(Hash.hg_changeset)
    q = q.filter(Hash.date_added > since_epoch)
    print q
    mapfile = _build_mapfile(q)
    if not mapfile:
        abort(404, 'No mappings inserted into database for project(s) %s since %s'
              % (projects, since))
    return mapfile


def _insert_many(project, ignore_dups=False):
    """Update the database with many git-hg mappings.

    Args:
        project: Single project name string
        ignore_dups: Boolean; if False, abort on duplicate entries without inserting
        anything

    Returns:
        An empty json response body

    Exceptions:
        HTTP 400: Request content-type is not 'text/plain'
        HTTP 400: Malformed SHA
        HTTP 404: Project not found
        HTTP 409: ignore_dups=False and there are duplicate entries
        HTTP 500: Multiple projects found with matching project name
    """
    if request.content_type != 'text/plain':
        abort(
            400, "HTTP request header 'Content-Type' must be set to 'text/plain'")
    session = g.db.session('mapper')
    proj = _get_project(session, project)  # can raise HTTP 404 or HTTP 500
    for line in request.stream.readlines():
        line = line.rstrip()
        try:
            (git_commit, hg_changeset) = line.split(' ')
        except ValueError:
            logger.error(
                "Received input line: '%s' for project %s", line, project)
            logger.error("Was expecting an input line such as "
                         "'686a558fad7954d8481cfd6714cdd56b491d2988 "
                         "fef90029cb654ad9848337e262078e403baf0c7a'")
            logger.error("i.e. where the first hash is a git commit SHA "
                         "and the second hash is a mercurial changeset SHA")
            abort(400, "Input line '%s' received for project %s did not contain a space"
                  % (line, project))
            # header/footer won't match this format
            continue
        _add_hash(session, git_commit, hg_changeset, proj)  # can raise HTTP 400
        if ignore_dups:
            try:
                session.commit()
            except sa.exc.IntegrityError:
                session.rollback()
    if not ignore_dups:
        try:
            session.commit()
        except sa.exc.IntegrityError:
            session.rollback()
            abort(409, "Some of the given mappings for project %s already exist"
                  % project)
    return jsonify()


@bp.route('/<project>/insert', methods=('POST',))
@p.mapper.mapping.insert.require()
def insert_many_no_dups(project):
    # (documentation in relengapi/docs/usage/mapper.rst)
    return _insert_many(project, ignore_dups=False)  # can raise HTTP 400, 404, 409, 500


@bp.route('/<project>/insert/ignoredups', methods=('POST',))
@p.mapper.mapping.insert.require()
def insert_many_ignore_dups(project):
    # (documentation in relengapi/docs/usage/mapper.rst)
    return _insert_many(project, ignore_dups=True)  # can raise HTTP 400, 404, 500


@bp.route('/<project>/insert/<git_commit>/<hg_changeset>', methods=('POST',))
@p.mapper.mapping.insert.require()
def insert_one(project, git_commit, hg_changeset):
    # (documentation in relengapi/docs/usage/mapper.rst)
    session = g.db.session('mapper')
    proj = _get_project(session, project)  # can raise HTTP 404 or HTTP 500
    _add_hash(session, git_commit, hg_changeset, proj)  # can raise HTTP 400
    try:
        session.commit()
        q = Hash.query.join(Project).filter(_project_filter(project))
        q = q.filter(sa.text("git_commit == :commit")).params(commit=git_commit)
        return q.one().as_json()
    except sa.exc.IntegrityError:
        abort(409, "Provided mapping %s %s for project %s already exists and "
              "cannot be reinserted" % (git_commit, hg_changeset, project))
    except NoResultFound:
        abort(500, "Provided mapping %s %s for project %s could not be inserted "
              "into the database" % (git_commit, hg_changeset, project))
    except MultipleResultsFound:
        abort(500, "Provided mapping %s %s for project %s has been inserted into "
              "the database multiple times" % (git_commit, hg_changeset, project))


@bp.route('/<project>', methods=('POST',))
@p.mapper.project.insert.require()
def add_project(project):
    # (documentation in relengapi/docs/usage/mapper.rst)
    session = g.db.session('mapper')
    p = Project(name=project)
    session.add(p)
    try:
        session.commit()
    except (sa.exc.IntegrityError, sa.exc.ProgrammingError):
        abort(409, "Project %s could not be inserted into the database" %
              project)
    return jsonify()
