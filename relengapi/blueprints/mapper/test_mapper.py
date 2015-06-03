# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import mock

from nose.tools import eq_
from relengapi import p
from relengapi.blueprints.mapper import Hash
from relengapi.blueprints.mapper import Project
from relengapi.lib import auth
from relengapi.lib.testing.context import TestContext
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

SHA1 = '111111705d7c41c8f101b5b1e3438d95d0fcfa7a'
SHA1R = ''.join(reversed(SHA1))
SHA2 = '222222705d7c41c8f101b5b1e3438d95d0fcfa7a'
SHA2R = ''.join(reversed(SHA2))
SHA3 = '333333333d7c41c8f101b5b1e3438d95d0fcfa7a'
SHA3R = ''.join(reversed(SHA3))

SHAFILE = "%s %s\n%s %s\n%s %s\n" % (
    SHA1, SHA1R,
    SHA2, SHA2R,
    SHA3, SHA3R)

Session = sessionmaker()


def db_setup(app):
    engine = app.db.engine("mapper")
    Session.configure(bind=engine)
    session = Session()
    project = Project(name='proj')
    session.add(project)
    session.commit()


def db_teardown(app):
    engine = app.db.engine("mapper")
    engine.execute("delete from hashes")
    engine.execute("delete from projects")


class User(auth.BaseUser):

    def get_id(self):
        return 'test:'

    def get_permissions(self):
        return [
            p.mapper.mapping.insert,
            p.mapper.project.insert,
        ]

test_context = TestContext(databases=['mapper'],
                           user=User(),
                           db_setup=db_setup,
                           db_teardown=db_teardown,
                           reuse_app=True)


def insert_some_hashes(app):
    engine = app.db.engine("mapper")
    Session.configure(bind=engine)
    session = Session()
    project = session.query(Project).filter(Project.name == 'proj').one()
    session.add(
        Hash(git_commit=SHA1, hg_changeset=SHA1R, project=project, date_added=12345))
    session.add(
        Hash(git_commit=SHA2, hg_changeset=SHA2R, project=project, date_added=12346))
    session.add(
        Hash(git_commit=SHA3, hg_changeset=SHA3R, project=project, date_added=12347))
    session.commit()


def hash_pair_exists(app, git, hg):
    engine = app.db.engine("mapper")
    Session.configure(bind=engine)
    session = Session()
    try:
        session.query(Hash).filter(Hash.hg_changeset == hg).filter(
            Hash.git_commit == git).one()
        return True
    except (MultipleResultsFound, NoResultFound):
        return False


@test_context
def test_get_rev_git(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/proj/rev/git/%s' % SHA1)
    eq_(rv.status_code, 200)
    eq_(rv.data, '%s %s' % (SHA1, SHA1R))


@test_context
def test_get_rev_hg(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/proj/rev/hg/%s' % SHA2R)
    eq_(rv.status_code, 200)
    eq_(rv.data, '%s %s' % (SHA2, SHA2R))


@test_context
def test_get_rev_abbreviated(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/proj/rev/git/%s' % SHA1[:8])
    eq_(rv.status_code, 200)
    eq_(rv.data, '%s %s' % (SHA1, SHA1R))


@test_context
def test_get_rev_missing(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/proj/rev/git/abcdeabcde')
    eq_(rv.status_code, 404)
    # TODO: check that return is JSON, once it is


@test_context
def test_get_rev_malformed(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/proj/rev/git/xyz')
    eq_(rv.status_code, 400)
    # TODO: check that return is JSON, once it is


@test_context
def test_get_rev_weird_vcs(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/proj/rev/darcs/123')
    eq_(rv.status_code, 400)
    # TODO: check that return is JSON, once it is


@test_context
def test_get_mapfile(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/proj/mapfile/full')
    eq_(rv.status_code, 200)
    eq_(rv.data, '%s %s\n%s %s\n%s %s\n' % (
        # note that these are sorted by git sha1, not hg
        SHA3, SHA3R, SHA1, SHA1R, SHA2, SHA2R,
    ))


@test_context
def test_get_mapfile_no_rows(client):
    rv = client.get('/mapper/proj/mapfile/full')
    eq_(rv.status_code, 404)


@test_context
def test_get_mapfile_no_project(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/notaproj/mapfile/full')
    eq_(rv.status_code, 404)


@test_context
def test_get_mapfile_since(app, client):
    insert_some_hashes(app)
    rv = client.get('/mapper/proj/mapfile/since/1970-01-01T03:25:46+00:00')
    eq_(rv.status_code, 200)
    eq_(rv.data, '%s %s\n' % (SHA3, SHA3R))


@test_context
def test_insert_one(client):
    # TODO: this should really be POST
    with mock.patch('time.time') as time:
        time.return_value = 1234.0
        rv = client.post('/mapper/proj/insert/%s/%s' % (SHA1, SHA2))
    eq_(rv.status_code, 200)
    eq_(json.loads(rv.data), {
        'date_added': 1234.0,
        'project_name': 'proj',
        'git_commit': SHA1,
        'hg_changeset': SHA2,
    })


@test_context
def test_insert_one_duplicate(client):
    rv = client.post('/mapper/proj/insert/%s/%s' % (SHA1, SHA2))
    eq_(rv.status_code, 200)
    # duplicate hg changeset
    rv = client.post('/mapper/proj/insert/%s/%s' % (SHA1, SHA3))
    eq_(rv.status_code, 409)
    # duplicate git changeset
    rv = client.post('/mapper/proj/insert/%s/%s' % (SHA3, SHA2))
    eq_(rv.status_code, 409)
    # TODO: check response when it's JSON


@test_context
def test_insert_one_no_project(client):
    rv = client.post('/mapper/notaproj/insert/%s/%s' % (SHA1, SHA2))
    eq_(rv.status_code, 404)
    # TODO: check response when it's JSON


@test_context
def test_insert_multi_bad_content_type(app, client):
    rv = client.post('/mapper/proj/insert',
                     content_type='text/chocolate', data=SHAFILE)
    eq_(rv.status_code, 400)
    # TODO: check response when it's JSON


@test_context
def test_insert_multi_no_dups(app, client):
    rv = client.post('/mapper/proj/insert',
                     content_type='text/plain', data=SHAFILE)
    eq_(rv.status_code, 200)
    # TODO: check response when it's JSON
    assert hash_pair_exists(app, SHA1, SHA1R)
    assert hash_pair_exists(app, SHA2, SHA2R)
    assert hash_pair_exists(app, SHA3, SHA3R)


@test_context
def test_insert_multi_no_dups_but_dups(app, client):
    rv = client.post('/mapper/proj/insert/%s/%s' % (SHA2, SHA2R))
    eq_(rv.status_code, 200)
    rv = client.post('/mapper/proj/insert',
                     content_type='text/plain', data=SHAFILE)
    eq_(rv.status_code, 409)
    # TODO: check response when it's JSON
    assert not hash_pair_exists(app, SHA1, SHA1R)
    assert hash_pair_exists(app, SHA2, SHA2R)
    assert not hash_pair_exists(app, SHA3, SHA3R)


@test_context
def test_insert_multi_ignoredups(app, client):
    rv = client.post('/mapper/proj/insert/ignoredups',
                     content_type='text/plain', data=SHAFILE)
    eq_(rv.status_code, 200)
    # TODO: check response when it's JSON
    assert hash_pair_exists(app, SHA1, SHA1R)
    assert hash_pair_exists(app, SHA2, SHA2R)
    assert hash_pair_exists(app, SHA3, SHA3R)


@test_context
def test_insert_multi_ignoredups_with_dups(app, client):
    rv = client.post('/mapper/proj/insert/%s/%s' % (SHA2, SHA2R))
    eq_(rv.status_code, 200)
    rv = client.post('/mapper/proj/insert/ignoredups',
                     content_type='text/plain', data=SHAFILE)
    eq_(rv.status_code, 200)
    # TODO: check response when it's JSON
    assert hash_pair_exists(app, SHA1, SHA1R)
    assert hash_pair_exists(app, SHA2, SHA2R)
    assert hash_pair_exists(app, SHA3, SHA3R)


@test_context
def test_add_project(client):
    rv = client.post('/mapper/proj2')
    eq_(rv.status_code, 200)
    eq_(json.loads(rv.data), {})


@test_context
def test_add_project_existing(client):
    rv = client.post('/mapper/proj')
    eq_(rv.status_code, 409)
    # TODO: check that return is JSON, once it is


# TODO: also assert content types
