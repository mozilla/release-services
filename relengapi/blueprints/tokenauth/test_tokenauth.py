# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import json
from flask.ext.login import current_user
from nose.tools import eq_
from relengapi import p
from relengapi.blueprints.tokenauth import test_util
from relengapi.blueprints.tokenauth.tables import Token
from relengapi.lib import auth
from relengapi.lib.testing.context import TestContext

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


def insert_token(app):
    session = app.db.session('relengapi')
    t = Token(
        id=1, permissions=[p.test_tokenauth.zig], description="Zig only")
    session.add(t)
    session.commit()


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


@test_context.specialize(user=userperms([p.base.tokens.issue,
                                         p.test_tokenauth.zig]))
def test_issue_token_success(client):
    """Successful token issuance returns a token"""
    request = {
        'permissions': ['test_tokenauth.zig'], 'description': 'More Zig'}
    res = client.post_json('/tokenauth/tokens', request)
    eq_(json.loads(res.data), {
        'result': {
            'token': test_util.FakeSerializer.prm(1),
            'id': 1,
            'typ': 'prm',
            'description': 'More Zig',
            'permissions': ['test_tokenauth.zig'],
        }})


@test_context.specialize(user=userperms([p.base.tokens.issue,
                                         p.test_tokenauth.zig]))
def test_issue_token_not_subset(client):
    """Tokens can only allow permissions the issuer can perform, failing with
    'bad request' otherwise."""
    request = {'permissions': ['test_tokenauth.zig', 'test_tokenauth.zag'],
               'description': 'More Zig'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([p.base.tokens.issue,
                                         p.test_tokenauth.zig]))
def test_issue_token_no_description(client):
    """Tokens reqiure a description to issue."""
    request = {'permissions': ['test_tokenauth.zig']}
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
