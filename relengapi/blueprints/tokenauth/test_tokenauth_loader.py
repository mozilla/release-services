
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import json
from nose.tools import eq_
from relengapi import p
from relengapi.blueprints.tokenauth import tables
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
    auth = json.loads(
        client.get('/test_tokenauth',
                   headers=[('Authentication', 'Bearer TOK/1/v1')]).data)
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
