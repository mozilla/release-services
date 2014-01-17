#!/usr/bin/env python

import bottle
from bottle import route, run, abort, default_app, request
import bottle_mysql
import logging
import pprint
import re
from mapper.decorators import login_required, check_client_ip, attach_required

log = logging.getLogger(__name__)

rev_regex = re.compile('''^[a-f0-9]{1,40}$''')


def _get_project_name_sql(project_name):
    """ Helper method that returns the select sql clause for the project
    name(s) specified for a project name field.  This can be comma-delimited,
    which is the way we combine queries across multiple projects.

    Args:
        project_name: a string from a bottle route, which may be comma-delimited.

    Returns:
        A string to append to a SELECT sql call.

    Raises:
        HTTPError: The project name has a quote mark in it. (via bottle.abort())
    """
    if '"' in project_name or "'" in project_name:
        abort(500, "Bad project name |%s|" % project_name)
    if ',' in project_name:
        return 'name in ("%s")' % '","'.join(project_name.split(','))
    else:
        return 'name="%s"' % project_name


def _build_mapfile(db, error_message):
    """ Helper method to build the full mapfile from a query
    Args:
        db: a db connection sent from bottle_mysql
        error_message: the message string to send back if there are no results found.

    Yields:
        Text output, which is 40 characters of hg changeset sha, a space,
        40 characters of git changeset sha, and a newline.

    Exceptions:
        HTTPError: No results found, via bottle.abort().
    """
    success = False
    while True:
        row = db.fetchone()
        if not row:
            break
        success = True
        yield("%s %s\n" % (row['hg_changeset'], row['git_changeset']))
    if not success:
        abort(404, error_message)


def _check_existing_sha(project, vcs_type, changeset, db):
    """ Helper method to check for an existing changeset.
    Args:
        project: the project name(s) string, comma-delimited
        vcs_type: the vcs name string (hg or git)
        changeset: the changeset string to look for
        db: the bottle_mysql db connection

    Returns:
        The first db row if it exists; otherwise None.
    """
    query = 'SELECT * FROM hashes, projects WHERE projects.id=hashes.project_id AND %s AND %s_changeset=%%s' % (_get_project_name_sql(project), vcs_type)
    db.execute(query, (changeset, ))
    row = db.fetchone()
    if row:
        return row


def _check_well_formed_sha(sha):
    """Helper method to check for a well-formed sha.
    Args:
        sha: string to check against the well-formed sha regex.

    Returns:
        None on success.

    Exceptions:
        HTTPError: on non-well-formed sha, via bottle.abort()
    """
    if not rev_regex.match(sha):
        abort(400, "Bad sha %s!" % str(sha))


def _insert_one(project, hg_changeset, git_changeset, db):
    """ Helper method to insert a single hg_changeset/git_changeset pair into the db.

    Args:
        project: single project name string (not comma-delimited list)
        hg_changeset: hg changeset string
        git_changeset: git changeset string
        db: the bottle_mysql db connection

    Returns:
        The response from the db.execute() call.
    """
    _check_well_formed_sha(hg_changeset)
    _check_well_formed_sha(git_changeset)
    for vcs_type, changeset in {'hg': hg_changeset, 'git': git_changeset}.items():
        row = _check_existing_sha(project, vcs_type, changeset, db)
        if row:
            return (409, row)
    query = "INSERT INTO hashes SELECT %s, %s, id, unix_timestamp() FROM projects WHERE name=%s;"
    return db.execute(query, (hg_changeset, git_changeset, project))


@route('/<project>/rev/<vcs>/<rev>')
def get_rev(project, vcs, rev, db):
    """Translate git/hg revisions.
    """
    if vcs not in ("git", "hg"):
        abort(500, "Unknown vcs %s" % vcs)
    if not rev_regex.match(rev):
        abort(500, "Bad revision format |%s|" % rev)
    if vcs == 'git':
        target_column = 'git_changeset'
        source_column = 'hg_changeset'
    elif vcs == 'hg':
        target_column = 'hg_changeset'
        source_column = 'git_changeset'
    query = 'SELECT %s FROM hashes, projects WHERE %s LIKE "%s%%" AND projects.id=hashes.project_id AND %s;' % (target_column, source_column, rev, _get_project_name_sql(project))
    db.execute(query)
    row = db.fetchone()
    if row:
        bottle.response.content_type = "application/json"
        return row
    abort(404, "%s - %s not found" % (query, target_column))


@route('/<project>/mapfile/full')
def get_full_mapfile(project, db):
    """Get a full mapfile. <project> can be a comma-delimited set of projects"""
    query = 'SELECT DISTINCT hg_changeset, git_changeset FROM hashes, projects WHERE projects.id=hashes.project_id AND %s ORDER BY git_changeset;' % _get_project_name_sql(project)
    db.execute(query)
    error_message = "%s - not found" % query
    bottle.response.content_type = "text/plain"
    return _build_mapfile(db, error_message)


@route('/<project>/mapfile/since/<date>')
def get_mapfile_since(project, date, db):
    """Get a mapfile since date.  <project> can be a comma-delimited set of projects"""
    query = 'SELECT DISTINCT hg_changeset, git_changeset FROM hashes, projects WHERE projects.id=hashes.project_id AND %s AND date_added >= unix_timestamp(%%s) ORDER BY git_changeset;' % _get_project_name_sql(project)
    db.execute(query, (date, ))
    error_message = "%s - not found" % query
    bottle.response.content_type = "text/plain"
    return _build_mapfile(db, error_message)


def _insert_many(project, db, dups=False):
    """Update the db with many lines."""
    unsuccessful = ""
    for line in request.body.readlines():
        line = line.rstrip()
        try:
            (hg_changeset, git_changeset) = line.split(' ')
        except ValueError:
            # header/footer won't match this format
            continue
        resp = _insert_one(project, hg_changeset, git_changeset, db)
        if isinstance(resp, tuple):
            status, row = resp
            if status == 409:
                unsuccessful = "%s%s\n" % (unsuccessful, str(line))
        if unsuccessful and not dups:
            abort(206, "These were unsuccessful:\n\n%s" % unsuccessful)
    if unsuccessful:
        return "Unsuccessful lines:\n\n%s" % unsuccessful


@check_client_ip
@login_required
@attach_required
@route('/<project>/insert', method='POST')
def insert_many_no_dups(project, db):
    return _insert_many(project, db, dups=False)


@check_client_ip
@login_required
@attach_required
@route('/<project>/insert/ignoredups', method='POST')
def insert_many_allow_dups(project, db):
    return _insert_many(project, db, dups=True)


@check_client_ip
@login_required
@attach_required
@route('/<project>/insert/:hg_changeset#[0-9a-f]+#/:git_changeset#[0-9a-f]+#')
def insert_one(project, hg_changeset, git_changeset, db):
    """Insert a single row into the db"""
    resp = _insert_one(project, hg_changeset, git_changeset, db)
    if isinstance(resp, tuple):
        status, row = resp
        if status == 409:
            abort(status, "Already exists: %s" % pprint.pformat(row))
    row = _check_existing_sha(project, 'hg', hg_changeset, db)
    if row:
        return str(row)
    else:
        abort(500, "row doesn't exist!")


def main():
    """main entry point"""
    logging.basicConfig(level=logging.INFO)
    log.info("Starting up...")
    run(host='localhost', port=8888, debug=True, reloader=True)


app = default_app()
# TODO get this in a file
plugin = bottle_mysql.Plugin(dbuser='user', dbpass='pass', dbname='mapper')
app.install(plugin)

if __name__ == '__main__':
    main()
