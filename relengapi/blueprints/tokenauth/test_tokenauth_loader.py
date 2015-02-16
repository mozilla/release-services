# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock

from flask import json
from nose.tools import eq_
from relengapi import p
from relengapi.blueprints.tokenauth import loader
from relengapi.blueprints.tokenauth import tables
from relengapi.blueprints.tokenauth import test_util
from relengapi.blueprints.tokenauth.test_tokenauth import test_context


def insert_token(app):
    session = app.db.session('relengapi')
    t = tables.Token(
        id=1, permissions=[p.test_tokenauth.zig], description="Zig only")
    session.add(t)
    session.commit()


@test_context
def test_loader_no_header(app, client):
    """With no Authentication header, no permissions are allowed"""
    auth = json.loads(client.get('/test_tokenauth').data)
    eq_(auth['permissions'], [])


@test_context
def test_loader_not_bearer(app, client):
    """With an Authentication header that does not start with 'Bearer', no
    permissions are allowed"""
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authentication', 'Penguiner TOK/1/v1')]).data)
    eq_(auth['permissions'], [])


@test_context.specialize(db_setup=insert_token)
def test_loader_good_header(app, client):
    """With a good Authentication header, the permissions in the DB are allowed"""
    tok = test_util.FakeSerializer.prm(1)
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authentication', 'Bearer ' + tok)]).data)
    eq_(auth['permissions'], ['test_tokenauth.zig'], auth)


@test_context
def test_loader_bad_header(app, client):
    """With a bad Authentication header, no permissions are allowed"""
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authentication', 'Bearer xxxxx')]).data)
    eq_(auth['permissions'], [])


@test_context.specialize(db_setup=insert_token)
def test_loader_good_header_not_in_db(app, client):
    """With a good Authentication header but no row in the DB, no permissions are allowed"""
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authentication', 'Bearer TOK/2/v1')]).data)
    eq_(auth['permissions'], [])


@test_context.specialize(db_setup=insert_token)
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
