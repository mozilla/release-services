# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import time
import re
import logging
from typing import Tuple
from backend_common.db import db
from flask import request
from .config import PROJECT_PATH_NAME
from sqlalchemy import orm, Column, ForeignKey, Index, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from werkzeug.exceptions import Conflict, NotFound, InternalServerError, BadRequest
from cli_common import log


logger = log.get_logger(__name__)


class Project(db.Model):
    """Object-relational mapping between python class Project
    and database table "projects"
    """
    __tablename__ = PROJECT_PATH_NAME + '_projects'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)


class Hash(db.Model):

    """Object-relational mapping between python class Hash
    and database table "hashes"
    """
    __tablename__ = PROJECT_PATH_NAME + '_hashes'
    hg_changeset = Column(String(40), nullable=False)
    git_commit = Column(String(40), nullable=False)
    project_id = Column(Integer, ForeignKey(Project.id), nullable=False)
    project = orm.relationship(Project, primaryjoin=(project_id == Project.id))
    date_added = Column(Integer, nullable=False)

    project_name = property(lambda self: self.project.name)

    def as_json(self):
        return {
            n: getattr(self, n)
            for n in ('git_commit', 'hg_changeset','date_added', 'project_name')
        }

    __table_args__ = (
        # TODO: (needs verification) all queries specifying a hash are for
        # (project, hash), so these aren't used
        Index('hg_changeset', 'hg_changeset'),
        Index('git_commit', 'git_commit'),
        # TODO: this index is a prefix of others and will never be used
        Index('project_id', 'project_id'),
        Index('project_id__date_added', 'project_id', 'date_added'),
        Index('project_id__hg_changeset', 'project_id',
                 'hg_changeset', unique=True),
        Index(
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


def _stream_mapfile(query) -> Tuple[str, int, dict]:
    """Helper method to build a map file from a SQLAlchemy query.
    Args:
        query: SQLAlchemy query
    Returns:
        * Text output: 40 characters git commit SHA, a space,
          40 characters hg changeset SHA, a newline (streamed); or
        * HTTP 404: if the query returns no results
    """
    # this helps keep memory use down a little, but the DBAPI still loads
    # the entire result set into memory..
    # http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per
    query = query.yield_per(100)

    if query.count() == 0:
        NotFound('No mappings found.')

    def contents():
        for r in query:
            yield '%s %s' % (r.git_commit, r.hg_changeset) + "\n"

    if contents:
        return contents(), 200, {
            'mimetype': 'text/plain',
        }


def _check_well_formed_sha(vcs: str, sha: str, exact_length: int=40) -> None:
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
        raise BadRequest("Unknown vcs type {}".format(vcs))

    rev_regex = re.compile('''^[a-f0-9]{1,40}$''')
    if sha is None:
        raise BadRequest("{} SHA is <None>".format(vcs))

    elif sha == "":
        raise BadRequest("{} SHA is an empty string".format(vcs))

    elif not rev_regex.match(sha):
        raise BadRequest("{} SHA contains bad characters: '{}'".format(vcs, str(sha)))

    if exact_length is not None and len(sha) != exact_length:
        raise BadRequest("{vcs} SHA should be {correct} characters long, but is {actual} characters long: '{sha}'".format(
            vcs=vcs,
            correct=exact_length,
            actual=len(sha),
            sha=str(sha)
        ))


def _get_project(session, project: str) -> Project:
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
        return session.query(Project).filter_by(Project.name == project).one()

    except MultipleResultsFound:
        raise InternalServerError("Multiple projects with name {} found in database".format(project))

    except NoResultFound:
        raise NotFound("Could not find project {} in database".format(project))


def _add_hash(session, git_commit: str, hg_changeset: str, project: str) -> None:
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
    h = Hash(git_commit=git_commit, hg_changeset=hg_changeset, project=project, date_added=time.time())
    session.add(h)


def _insert_many(project: str, body: str, session, ignore_dups: bool=False) -> dict:
    """Update the database with many git-hg mappings.
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
    """
    if request.content_type != 'text/plain':
        raise BadRequest("HTTP request header 'Content-Type' must be set to 'text/plain'")

    proj = _get_project(session, project)  # can raise HTTP 404 or HTTP 500
    for line in request.stream.readlines():
        line = line.rstrip()

        try:
            (git_commit, hg_changeset) = line.split(' ')

        except ValueError:
            logger.error("Received input line: '%s' for project %s", line, project)
            logger.error("Was expecting an input line such as "
                         "'686a558fad7954d8481cfd6714cdd56b491d2988 "
                         "fef90029cb654ad9848337e262078e403baf0c7a'")
            logger.error("i.e. where the first hash is a git commit SHA and the second hash is a mercurial changeset SHA")
            raise BadRequest("Input line '%s' received for project %s did not contain a space" % (line, project))

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
            raise Conflict("Some of the given mappings for project %s already exist" % project)

    return {}
