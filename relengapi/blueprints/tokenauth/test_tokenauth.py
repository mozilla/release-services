# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import calendar
import pytz

from datetime import datetime
from flask import json
from flask.ext.login import current_user
from nose.tools import eq_
from relengapi import p
from relengapi.blueprints.tokenauth import test_util
from relengapi.blueprints.tokenauth import types
from relengapi.blueprints.tokenauth.tables import Token
from relengapi.lib import auth
from relengapi.lib.testing.context import TestContext
from wsme.rest.json import fromjson
from wsme.rest.json import tojson

p.test_tokenauth.zig.doc("Zig")
p.test_tokenauth.zag.doc("Zag")


def app_setup(app):
    # utility endpoint
    @app.route('/test_tokenauth')
    def test_route():
        assert isinstance(current_user.permissions, set)
        return json.dumps({
            'id': current_user.get_id(),
            'permissions': sorted(str(a) for a in current_user.permissions),
        })
    # fake out the serializer to make it easier to debug
    app.tokenauth_serializer = test_util.FakeSerializer()


def userperms(perms):
    u = auth.HumanUser('permie')
    u._permissions = set(perms)
    return u

test_context = TestContext(databases=['relengapi'],
                           reuse_app=True,
                           app_setup=app_setup)
issuer_test_context = test_context.specialize(
    user=userperms([p.base.tokens.issue, p.test_tokenauth.zig]))


def insert_token(app):
    session = app.db.session('relengapi')
    t = Token(
        id=1, permissions=[p.test_tokenauth.zig], description="Zig only")
    session.add(t)
    session.commit()


def _get_token(data):
    resp = json.loads(data)
    if 'result' not in resp:
        raise AssertionError(str(resp))
    return fromjson(types.JsonToken, resp['result'])


def _eq_token(token, attrs):
    eq_(tojson(types.JsonToken, token),
        tojson(types.JsonToken, types.JsonToken(**attrs)))


def assert_prm_token(data, **attrs):
    token = _get_token(data)
    attrs['typ'] = 'prm'
    attrs['id'] = id = token.id
    attrs['token'] = test_util.FakeSerializer.prm(id)
    _eq_token(token, attrs)


def assert_tmp_token(data, **attrs):
    token = _get_token(data)
    attrs['typ'] = 'tmp'
    nbf = calendar.timegm(token.not_before.utctimetuple())
    exp = calendar.timegm(token.expires.utctimetuple())
    attrs['token'] = test_util.FakeSerializer.tmp(
        nbf=nbf, exp=exp, prm=token.permissions,
        mta=token.metadata)
    _eq_token(token, attrs)

# tests


@test_context.specialize(user=userperms([]))
def test_list_tokens_forbidden(client):
    """Listing tokens requires base.tokens.view"""
    eq_(client.get('/tokenauth/tokens').status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.view]))
def test_list_tokens_empty(client):
    """Listing tokens with an empty DB returns an empty list"""
    eq_(json.loads(client.get('/tokenauth/tokens').data),
        {'result': []})


@test_context.specialize(db_setup=insert_token,
                         user=userperms([p.base.tokens.view]))
def test_list_tokens_full(client):
    """Listing tokens returns the tokens in the DB"""
    eq_(json.loads(client.get('/tokenauth/tokens').data),
        {'result': [
            {'description': 'Zig only', 'id': 1, 'typ': 'prm',
                'permissions': ['test_tokenauth.zig']}
        ]})


@test_context.specialize(user=userperms([]))
def test_issue_token_forbidden(client):
    """Token issuance requires base.tokens.issue"""
    eq_(client.get('/tokenauth/tokens').status_code, 403)


@issuer_test_context
def test_issue_token_prm_success_no_typ(client):
    """Specifying no typ returns a prm token (for backward compatibility)"""
    request = {
        'permissions': ['test_tokenauth.zig'], 'description': 'More Zig'}
    res = client.post_json('/tokenauth/tokens', request)
    assert_prm_token(res.data,
                     description='More Zig',
                     permissions=['test_tokenauth.zig'])


@issuer_test_context
def test_issue_token_prm_success(client):
    """A legitimate request for a prm token returns one"""
    request = {'permissions': ['test_tokenauth.zig'],
               'description': 'More Zig', 'typ': 'prm'}
    res = client.post_json('/tokenauth/tokens', request)
    assert_prm_token(res.data,
                     description='More Zig',
                     permissions=['test_tokenauth.zig'])


@issuer_test_context
def test_issue_token_tmp_success(client):
    """A legitimate request for a tmp token returns one"""
    request = {'permissions': ['test_tokenauth.zig'],
               'not_before': datetime(2014, 1, 1, tzinfo=pytz.UTC),
               'expires': datetime(2015, 1, 1, tzinfo=pytz.UTC),
               'typ': 'tmp',
               'metadata': {}}
    res = client.post_json('/tokenauth/tokens', request)
    assert_tmp_token(res.data,
                     not_before=datetime(2014, 1, 1, tzinfo=pytz.UTC),
                     expires=datetime(2015, 1, 1, tzinfo=pytz.UTC),
                     permissions=['test_tokenauth.zig'],
                     metadata={})


@issuer_test_context
def test_issue_token_not_subset(client):
    """Tokens can only allow permissions the issuer can perform, failing with
    'bad request' otherwise."""
    request = {'permissions': ['test_tokenauth.zig', 'test_tokenauth.zag'],
               'description': 'More Zig', 'typ': 'prm'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@issuer_test_context
def test_issue_tmp_token_no_metadata(client):
    """Requesting a temporary token without metadata fails."""
    request = {'permissions': ['test_tokenauth.zig'],
               'not_before': datetime(2014, 1, 1, tzinfo=pytz.UTC),
               'expires': datetime(2015, 1, 1, tzinfo=pytz.UTC),
               'typ': 'tmp'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@issuer_test_context
def test_issue_token_no_description(client):
    """Permanent tokens reqiure a description to issue."""
    request = {'permissions': ['test_tokenauth.zig'], 'typ': 'prm'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([]), db_setup=insert_token)
def test_get_token_forbidden(client):
    """Getting a single token requires base.tokens.view"""
    eq_(client.get('/tokenauth/tokens/1').status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.view]),
                         db_setup=insert_token)
def test_get_token_exists(client):
    """Getting an existing token returns its id, permissions, and description."""
    eq_(json.loads(client.get('/tokenauth/tokens/1').data),
        {'result': {'id': 1, 'description': 'Zig only', 'typ': 'prm',
                    'permissions': ['test_tokenauth.zig']}})


@test_context.specialize(user=userperms([p.base.tokens.view]))
def test_get_token_missing(client):
    """Getting a token which doesn't exist returns 404"""
    eq_(client.get('/tokenauth/tokens/99').status_code, 404)


@test_context.specialize(user=userperms([]), db_setup=insert_token)
def test_get_token_by_token_forbidden(client):
    """Getting a single token by token requires base.tokens.view"""
    res = client.post_json('/tokenauth/tokens/query', 'TOK/1/v1')
    eq_(res.status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.view]), db_setup=insert_token)
def test_get_token_by_token_exists(client):
    """Getting a single token returns that token."""
    res = client.post_json('/tokenauth/tokens/query',
                           test_util.FakeSerializer.prm(1))
    eq_(res.status_code, 200)
    eq_(json.loads(res.data),
        {'result': {'id': 1, 'description': 'Zig only', 'typ': 'prm',
                    'permissions': ['test_tokenauth.zig']}})


@test_context.specialize(user=userperms([p.base.tokens.view]))
def test_get_token_by_token_missing(client):
    """Getting a single token that does not exist returns status 404"""
    res = client.post_json('/tokenauth/tokens/query', 'TOK/99/v1')
    eq_(res.status_code, 404)


@test_context.specialize(user=userperms([p.base.tokens.view]))
def test_get_token_by_token_invalid(client):
    """Passing an invalid string to get a token returns 404"""
    res = client.post_json('/tokenauth/tokens/query', 'XXX')
    eq_(res.status_code, 404)


@test_context.specialize(user=userperms([]), db_setup=insert_token)
def test_revoke_token_forbidden(client):
    """Token revocation requires base.tokens.revoke"""
    eq_(client.delete('/tokenauth/tokens/1').status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.revoke]),
                         db_setup=insert_token)
def test_revoke_token_exists(app, client):
    """Revoking a token returns a 204 status and deletes the row."""
    eq_(client.delete('/tokenauth/tokens/1').status_code, 204)
    with app.app_context():
        token_data = Token.query.filter_by(id=1).first()
        eq_(token_data, None)


@test_context.specialize(user=userperms([p.base.tokens.revoke]),
                         db_setup=insert_token)
def test_revoke_token_missing(app, client):
    """Revoking a token returns a 204 status even if no such token existed."""
    eq_(client.delete('/tokenauth/tokens/99').status_code, 204)
