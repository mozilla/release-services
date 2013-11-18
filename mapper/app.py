#!/usr/bin/env python

import bottle
from bottle import route, run, abort, default_app, request
import bottle_mysql
import logging
import pprint

log = logging.getLogger(__name__)


def _get_project_name_sql(project_name):
    if ',' in project_name:
        return 'name in ("%s")' % '","'.join(project_name.split(','))
    else:
        return 'name="%s"' % project_name


def _build_mapfile(db, error_message):
    """ Build the full mapfile from a query
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
    """ Helper method to check for an existing changeset
        """
    query = 'SELECT * FROM hashes, projects WHERE projects.id=hashes.project_id AND %s AND %s_changeset="%s"' % (_get_project_name_sql(project), vcs_type, changeset)
    db.execute(query)
    row = db.fetchone()
    if row:
        return row


def _insert_one(project, hg_changeset, git_changeset, db, autocommit=True, verbose=False):
    """ Helper method to insert into db
        """
    for vcs_type, changeset in {'hg': hg_changeset, 'git': git_changeset}.items():
        row = _check_existing_sha(project, vcs_type, changeset, db)
        if row:
            return (409, row)
    # TODO how to get project id?
    query = "INSERT INTO hashes SELECT '%s', '%s', id, unix_timestamp() FROM projects WHERE name='%s';" % (hg_changeset, git_changeset, project)
    return db.execute(query)


@route('/<project>/rev/<vcs>/<rev>')
def get_rev(project, vcs, rev, db):
    """Translate git/hg revisions"""
    assert vcs in ("git", "hg")
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
    query = 'SELECT DISTINCT hg_changeset, git_changeset FROM hashes, projects WHERE projects.id=hashes.project_id AND %s AND date_added >= unix_timestamp("%s") ORDER BY git_changeset;' % (_get_project_name_sql(project), date)
    db.execute(query)
    error_message = "%s - not found" % query
    bottle.response.content_type = "text/plain"
    return _build_mapfile(db, error_message)


# TODO auth
@route('/<project>/insert', method='PUT')
def insert_many(project, db):
    """Update the db, but allow for errors"""
    unsuccessful = ""
    for line in request.body.readlines():
        (hg_changeset, git_changeset) = line.split(' ')
        # TODO autocommit=False?
        resp = _insert_one(project, hg_changeset, git_changeset, db)
        if isinstance(resp, tuple):
            status, row = resp
            if status == 409:
                unsuccessful = "%s%s\n" % (unsuccessful, line)
        if unsuccessful:
            abort(206, "These were unsuccessful:\n\n%s" % unsuccessful)


# TODO auth
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
