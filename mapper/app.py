#!/usr/bin/env python
import logging

import bottle
from bottle import route, run, abort, default_app
import bottle_mysql

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
    query = 'SELECT %s FROM hashes, projects WHERE %s LIKE "%s%%" AND projects.id=hashes.project_id and %s;' % (target_column, source_column, rev, project, _get_project_name_sql(project))
    db.execute(query)
    row = db.fetchone()
    if row:
        bottle.response.content_type = "application/json"
        return row
    abort(404, "%s - %s not found" % (query, target_column))


@route('/<project>/mapfile/full')
def get_full_mapfile(project, db):
    """Get a full mapfile. <project> can be a comma-delimited set of projects"""
    query = 'SELECT DISTINCT hg_changeset, git_changeset FROM hashes, projects WHERE projects.id=hashes.project_id and %s ORDER BY git_changeset;' % _get_project_name_sql(project)
    db.execute(query)
    error_message = "%s - not found" % query
    bottle.response.content_type = "text/plain"
    return _build_mapfile(db, error_message)


@route('/<project>/mapfile/since/<date>')
def get_mapfile_since(project, date, db):
    """Get a mapfile since date.  <project> can be a comma-delimited set of projects"""
    query = 'SELECT DISTINCT hg_changeset, git_changeset FROM hashes, projects WHERE projects.id=hashes.project_id and %s AND date_added >= unix_timestamp("%s") ORDER BY git_changeset;' % (_get_project_name_sql(project), date)
    db.execute(query)
    error_message = "%s - not found" % query
    bottle.response.content_type = "text/plain"
    return _build_mapfile(db, error_message)


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
