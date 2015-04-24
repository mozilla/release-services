# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock

from flask import json
from nose.tools import eq_
from relengapi import p
from relengapi.blueprints.tokenauth import loader
from relengapi.blueprints.tokenauth import tables
from relengapi.blueprints.tokenauth.test_tokenauth import test_context
from relengapi.blueprints.tokenauth.util import FakeSerializer
from relengapi.blueprints.tokenauth.util import insert_prm
from relengapi.blueprints.tokenauth.util import insert_usr


def test_TokenUser_str_tmp():
    tu = loader.TokenUser({'typ': 'tmp', 'mta': '{}'})
    eq_(str(tu), 'token:tmp')


def test_TokenUser_str_usr():
    tu = loader.TokenUser({'typ': 'usr', 'jti': '13'},
                          authenticated_email='foo@bar.com')
    eq_(str(tu), 'token:usr:id=13:user=foo@bar.com')


def test_TokenUser_str_prm():
    tu = loader.TokenUser({'typ': 'prm', 'jti': '13'})
    eq_(str(tu), 'token:prm:id=13')


@test_context
def test_loader_no_header(app, client):
    """With no Authorization header, no permissions are allowed"""
    auth = json.loads(client.get('/test_tokenauth').data)
    eq_(auth['permissions'], [])


@test_context
def test_loader_not_bearer(app, client):
    """With an Authorization header that does not start with 'Bearer', no
    permissions are allowed"""
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authorization', 'Penguiner TOK/1/v1')]).data)
    eq_(auth['permissions'], [])


@test_context.specialize(db_setup=insert_prm)
def test_loader_good_header(app, client):
    """With a good Authorization header, the permissions in the DB are allowed"""
    tok = FakeSerializer.prm(1)
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authorization', 'Bearer ' + tok)]).data)
    eq_(auth['permissions'], ['test_tokenauth.zig'], auth)


@test_context.specialize(db_setup=insert_prm)
def test_loader_good_header_Authentication(app, client):
    """The old 'Authentication' header can be used instead of 'Authorization'"""
    # see https://github.com/mozilla/build-relengapi/pull/192/files
    tok = FakeSerializer.prm(1)
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authentication', 'Bearer ' + tok)]).data)
    eq_(auth['permissions'], ['test_tokenauth.zig'], auth)


@test_context.specialize(db_setup=insert_prm)
def test_from_str(app):
    """from_str returns a TokenUser object for a good token"""
    tok = FakeSerializer.prm(1)
    with app.app_context():
        eq_(loader.token_loader.from_str(tok).permissions,
            set([p.test_tokenauth.zig]))


@test_context
def test_from_str_no_type(app):
    """from_str does not return a user for a token with no 'typ'"""
    tok = FakeSerializer.dumps({})
    with app.app_context():
        eq_(loader.token_loader.from_str(tok), None)


@test_context
def test_from_str_bad_type(app):
    """from_str does not return a user for a token with a bogus typ"""
    tok = FakeSerializer.dumps({'iss': 'ra2', 'typ': 'booogus'})
    with app.app_context():
        eq_(loader.token_loader.from_str(tok), None)


@test_context
def test_loader_bad_header(app, client):
    """With a bad Authorization header, no permissions are allowed"""
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authorization', 'Bearer xxxxx')]).data)
    eq_(auth['permissions'], [])


@test_context
def test_loader_malformed_header(app, client):
    """With a malformed Authorization header, no permissions are allowed"""
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authorization', 'no-space-ma')]).data)
    eq_(auth['permissions'], [])


@test_context.specialize(db_setup=insert_prm)
def test_loader_good_header_not_in_db(app, client):
    """With a good Authorization header but no row in the DB, no permissions are allowed"""
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authorization', 'Bearer TOK/2/v1')]).data)
    eq_(auth['permissions'], [])


@test_context.specialize(db_setup=insert_prm)
def test_prm_loader(app):
    with app.app_context():
        eq_(loader.prm_loader({'typ': 'prm', 'jti': 't1'}).permissions,
            set([p.test_tokenauth.zig]))


@test_context
def test_tmp_loader(app):
    claims = {
        'typ': 'tmp',
        'exp': 1000020,
        'nbf': 1000000,
        'prm': ['test_tokenauth.zig'],
        'mta': {'quote': "that's so meta"},
    }
    with app.app_context():
        with mock.patch('relengapi.blueprints.tokenauth.loader.time') as time:
            time.time.return_value = 999990  # before `nbf`
            user = loader.tmp_loader(claims)
            eq_(user, None)

            time.time.return_value = 2222222  # after 'exp'
            user = loader.tmp_loader(claims)
            eq_(user, None)

            time.time.return_value = 1000010  # valid time
            user = loader.tmp_loader(claims)
            eq_(user.permissions, set([p.test_tokenauth.zig]))
            eq_(user.claims['mta'], {'quote': "that's so meta"})


@test_context.specialize(db_setup=insert_usr)
def test_usr_loader(app):
    with app.app_context():
        eq_(loader.usr_loader({'typ': 'usr', 'jti': 't2'}).permissions,
            set([p.test_tokenauth.zig]))


@test_context.specialize(db_setup=insert_usr)
def test_usr_loader_disabled(app):
    with app.app_context():
        # disable the token
        session = app.db.session('relengapi')
        tok = tables.Token.query.first()
        tok.disabled = True
        session.commit()
        # no TokenUser results
        eq_(loader.usr_loader({'typ': 'usr', 'jti': 't2'}), None)
