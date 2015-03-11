# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import calendar
import contextlib
import mock
import pytz

from datetime import datetime
from flask import json
from flask.ext.login import current_user
from nose.tools import eq_
from relengapi import p
from relengapi.blueprints.tokenauth import types
from relengapi.blueprints.tokenauth.tables import Token
from relengapi.blueprints.tokenauth.util import FakeSerializer
from relengapi.blueprints.tokenauth.util import insert_all
from relengapi.blueprints.tokenauth.util import insert_prm
from relengapi.blueprints.tokenauth.util import insert_usr
from relengapi.blueprints.tokenauth.util import prm_json
from relengapi.blueprints.tokenauth.util import usr_json
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
    app.tokenauth_serializer = FakeSerializer()


def userperms(perms, email='perm@ie'):
    u = auth.HumanUser(email)
    u._permissions = set(perms)
    return u


class NoEmailUser(auth.BaseUser):

    type = 'noemail'

    def __init__(self, permissions):
        self._permissions = set(permissions)

    def get_id(self):
        return 'noemail'

    def get_permissions(self):
        return self._permissions

full_view_perms = userperms([
    p.base.tokens.prm.view,
    p.base.tokens.usr.view.all,
])

test_context = TestContext(databases=['relengapi'],
                           reuse_app=True,
                           app_setup=app_setup)

JAN_2014 = calendar.timegm(
    datetime(2014, 1, 1, tzinfo=pytz.UTC).utctimetuple())


@contextlib.contextmanager
def time_set_to(when):
    with mock.patch('relengapi.blueprints.tokenauth.time.time') as time:
        time.return_value = when
        yield time

# assertions


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
    attrs['token'] = FakeSerializer.prm(id)
    attrs['disabled'] = False
    _eq_token(token, attrs)


def assert_tmp_token(data, **attrs):
    token = _get_token(data)
    attrs['typ'] = 'tmp'
    attrs['disabled'] = False
    nbf = JAN_2014
    exp = calendar.timegm(token.expires.utctimetuple())
    attrs['token'] = FakeSerializer.tmp(
        nbf=nbf, exp=exp, prm=token.permissions,
        mta=token.metadata)
    _eq_token(token, attrs)


def assert_usr_token(data, **attrs):
    token = _get_token(data)
    attrs['typ'] = 'usr'
    attrs['id'] = id = token.id
    attrs['token'] = FakeSerializer.usr(id)
    attrs['disabled'] = False
    _eq_token(token, attrs)


# tests


@test_context.specialize(user=userperms([]))
def test_root(client):
    """The Angular UI is served at the root path, regardless of permissions"""
    eq_(client.get('/tokenauth/').status_code, 200)


@test_context.specialize(db_setup=insert_prm,
                         user=userperms([]))
def test_list_tokens_forbidden(client):
    """Anyone can list tokens, but the list is empty without
    base.tokens.*.view"""
    eq_(json.loads(client.get('/tokenauth/tokens').data),
        {'result': []})


@test_context.specialize(user=full_view_perms)
def test_list_tokens_empty(client):
    """Listing tokens with an empty DB returns an empty list"""
    eq_(json.loads(client.get('/tokenauth/tokens').data)['result'],
        [])


@test_context.specialize(db_setup=insert_all,
                         user=userperms([p.base.tokens.prm.view]))
def test_list_tokens_only_prm_permitted(client):
    """The list of tokens is limited by base.tokens.prm.view."""
    eq_(json.loads(client.get('/tokenauth/tokens').data)['result'],
        [prm_json])


@test_context.specialize(db_setup=insert_all,
                         user=userperms([p.base.tokens.usr.view.all]))
def test_list_tokens_only_usr_permitted(client):
    """The list of tokens is limited by base.tokens.usr.view.all."""
    eq_(json.loads(client.get('/tokenauth/tokens').data)['result'],
        [usr_json])


@test_context.specialize(db_setup=insert_all,
                         user=userperms([p.base.tokens.usr.view.my]))
def test_list_tokens_only_my_usr_permitted(client):
    """The list of tokens is limited by base.tokens.usr.view.my."""
    eq_(json.loads(client.get('/tokenauth/tokens').data)['result'],
        [])


@test_context.specialize(db_setup=insert_all,
                         user=userperms([p.base.tokens.usr.view.my],
                                        email='me@me.com'))
def test_list_tokens_only_my_usr_permitted_match(client):
    """The list of tokens is limited by base.tokens.usr.view.my,
    but does include my tokens."""
    eq_(json.loads(client.get('/tokenauth/tokens').data)['result'],
        [usr_json])


@test_context.specialize(db_setup=insert_all,
                         user=full_view_perms)
def test_list_tokens_filter_by_query_usr(client):
    """The list of tokens can be filtered by `?typ=..`"""
    eq_(json.loads(client.get('/tokenauth/tokens?typ=prm').data)['result'],
        [prm_json])


@test_context.specialize(db_setup=insert_all,
                         user=userperms([p.base.tokens.usr.view.all]))
def test_list_tokens_filter_and_perms(client):
    """Permissions and query arg filtering are conjunctive: with permission
    to view only usr tokens, but requesting only prm tokens, nothing is
    returned."""
    eq_(json.loads(client.get('/tokenauth/tokens?typ=prm').data)['result'],
        [])


@test_context.specialize(user=userperms([]))
def test_issue_prm_token_forbidden(client):
    """Issuing a permanent token requires base.tokens.prm.issue"""
    request = {
        'permissions': ['test_tokenauth.zig'], 'description': 'More Zig'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.prm.issue, p.test_tokenauth.zig]))
def test_issue_prm_success_no_typ(client):
    """Specifying no typ returns a prm token (for backward compatibility)"""
    request = {
        'permissions': ['test_tokenauth.zig'], 'description': 'More Zig'}
    res = client.post_json('/tokenauth/tokens', request)
    assert_prm_token(res.data,
                     description='More Zig',
                     permissions=['test_tokenauth.zig'])


@test_context.specialize(user=userperms([p.base.tokens.prm.issue, p.test_tokenauth.zig]))
def test_issue_prm_success(client):
    """A legitimate request for a prm token returns one"""
    request = {'permissions': ['test_tokenauth.zig'],
               'description': 'More Zig', 'typ': 'prm'}
    res = client.post_json('/tokenauth/tokens', request)
    assert_prm_token(res.data,
                     description='More Zig',
                     permissions=['test_tokenauth.zig'])


@test_context.specialize(user=userperms([p.base.tokens.prm.issue, p.test_tokenauth.zig]))
def test_issue_no_description(client):
    """Permanent tokens reqiure a description to issue."""
    request = {'permissions': ['test_tokenauth.zig'], 'typ': 'prm'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([p.base.tokens.prm.issue, p.test_tokenauth.zig]))
def test_issue_not_subset(client):
    """Tokens can only allow permissions the issuer can perform, failing with
    'bad request' otherwise."""
    request = {'permissions': ['test_tokenauth.zig', 'test_tokenauth.zag'],
               'description': 'More Zig', 'typ': 'prm'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([p.base.tokens.prm.issue, p.test_tokenauth.zig]))
def test_issue_not_valid_perms(client):
    """Requesting a token with nonexistent permissions fails"""
    request = {'permissions': ['bogus.permission'],
               'description': 'bogus', 'typ': 'prm'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([]))
def test_issue_tmp_token_forbidden(client):
    """Issuing a temporary token fails without base.tokens.tmp.issue"""
    request = {'permissions': ['test_tokenauth.zig'],
               'expires': datetime(2014, 1, 1, 1, 15, 0, tzinfo=pytz.UTC),
               'typ': 'tmp',
               'metadata': {}}
    with time_set_to(JAN_2014):
        eq_(client.post_json('/tokenauth/tokens', request).status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.prm.issue, p.test_tokenauth.zig]))
def test_issue_tmp_token_forbidden_wrong_typ(client):
    """Issuing a temporary token requires base.tokens.tmp.issue; base.tokens.prm.issue won't do"""
    request = {'permissions': ['test_tokenauth.zig'],
               'expires': datetime(2014, 1, 1, 1, 15, 0, tzinfo=pytz.UTC),
               'typ': 'tmp',
               'metadata': {}}
    with time_set_to(JAN_2014):
        eq_(client.post_json('/tokenauth/tokens', request).status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.tmp.issue, p.test_tokenauth.zig]))
def test_issue_tmp_success(client):
    """A legitimate request for a tmp token returns one, with not_before set to the current time"""
    request = {'permissions': ['test_tokenauth.zig'],
               'expires': datetime(2014, 1, 1, 1, 15, 0, tzinfo=pytz.UTC),
               'typ': 'tmp',
               'metadata': {}}
    with time_set_to(JAN_2014):
        res = client.post_json('/tokenauth/tokens', request)
    assert_tmp_token(res.data,
                     not_before=datetime(2014, 1, 1, tzinfo=pytz.UTC),
                     expires=datetime(2014, 1, 1, 1, 15, 0, tzinfo=pytz.UTC),
                     permissions=['test_tokenauth.zig'],
                     metadata={})


@test_context.specialize(user=userperms([p.base.tokens.tmp.issue, p.test_tokenauth.zig]))
def test_issue_tmp_token_includes_nbf(client):
    """Requesting a temporary token with not_before specified fails."""
    request = {'permissions': ['test_tokenauth.zig'],
               'not_before': datetime(2014, 1, 1, tzinfo=pytz.UTC),
               'expires': datetime(2014, 1, 1, 1, 15, 0, tzinfo=pytz.UTC),
               'metadata': {},
               'typ': 'tmp'}
    with time_set_to(JAN_2014):
        eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([p.base.tokens.tmp.issue, p.test_tokenauth.zig]))
def test_issue_tmp_token_exp_in_past(client):
    """Requesting a temporary token with an expiration time in the past fails."""
    request = {'permissions': ['test_tokenauth.zig'],
               'expires': datetime(2013, 12, 31, 23, 15, 0, tzinfo=pytz.UTC),
               'metadata': {},
               'typ': 'tmp'}
    with time_set_to(JAN_2014):
        eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([p.base.tokens.tmp.issue, p.test_tokenauth.zig]))
def test_issue_tmp_token_exp_in_future(client):
    """Requesting a temporary token with an expiration time too far in the future fails."""
    request = {'permissions': ['test_tokenauth.zig'],
               # more than 1 day (RELENGAPI_TMP_TOKEN_MAX_LIFETIME) after JAN_2014
               'expires': datetime(2014, 1, 2, 1, 15, 0, tzinfo=pytz.UTC),
               'metadata': {},
               'typ': 'tmp'}
    with time_set_to(JAN_2014):
        eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([p.base.tokens.tmp.issue, p.test_tokenauth.zig]))
def test_issue_tmp_token_no_metadata(client):
    """Requesting a temporary token without metadata fails."""
    request = {'permissions': ['test_tokenauth.zig'],
               'not_before': datetime(2014, 1, 1, tzinfo=pytz.UTC),
               'expires': datetime(2014, 1, 1, 1, 15, 0, tzinfo=pytz.UTC),
               'typ': 'tmp'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([p.base.tokens.usr.issue, p.test_tokenauth.zig]))
def test_issue_usr_disabled(client):
    """An issue request for a disabled token is rejected."""
    request = {'permissions': ['test_tokenauth.zig'],
               'disabled': True,
               'description': 'More Zig', 'typ': 'usr'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([]))
def test_issue_usr_token_forbidden(client):
    """Issuing a temporary token requires base.tokens.prm.issue"""
    request = {'permissions': ['test_tokenauth.zig'],
               'typ': 'usr',
               'description': 'my token'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.usr.issue, p.test_tokenauth.zig],
                                        email='right@right.net'))
def test_issue_usr_success(client):
    """A legitimate request to issue a user token returns one, ignoring a supplied
    user field"""
    request = {'permissions': ['test_tokenauth.zig'],
               'typ': 'usr',
               'user': 'wrong@wrong.com',
               'description': 'my token'}
    res = client.post_json('/tokenauth/tokens', request)
    assert_usr_token(res.data,
                     permissions=['test_tokenauth.zig'],
                     user='right@right.net',
                     description='my token')


@test_context.specialize(
    user=NoEmailUser([p.base.tokens.usr.issue, p.test_tokenauth.zig]))
def test_issue_usr_no_email(client):
    """User tokens are not issued to users without an email address"""
    request = {'permissions': ['test_tokenauth.zig'],
               'typ': 'usr',
               'description': 'my token'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.prm.issue, p.test_tokenauth.zig]))
def test_issue_bad_typ(client):
    """Trying to issue a token with a bogus type fails."""
    request = {'typ': 'BOGUS'}
    eq_(client.post_json('/tokenauth/tokens', request).status_code, 400)


@test_context.specialize(user=userperms([]), db_setup=insert_prm)
def test_get_prm_token_forbidden(client):
    """Getting a single permanent token requires base.tokens.prm.view; forbidden
    tokens return 404"""
    eq_(client.get('/tokenauth/tokens/1').status_code, 404)


@test_context.specialize(user=userperms([p.base.tokens.usr.view]),
                         db_setup=insert_prm)
def test_get_prm_token_exists_forbidden(client):
    """Getting an existing permanent token with usr permission returns 404."""
    eq_(client.get('/tokenauth/tokens/1').status_code, 404)


@test_context.specialize(user=userperms([p.base.tokens.prm.view]),
                         db_setup=insert_prm)
def test_get_prm_token_success(client):
    """Getting an existing permanent token returns its id, permissions, and description."""
    eq_(json.loads(client.get('/tokenauth/tokens/1').data),
        {'result': {'id': 1, 'description': 'Zig only', 'typ': 'prm',
                    'permissions': ['test_tokenauth.zig'],
                    'disabled': False}})


@test_context.specialize(user=userperms([]), db_setup=insert_usr)
def test_get_usr_token_forbidden(client):
    """Getting a single user token without usr permission returns 404."""
    eq_(client.get('/tokenauth/tokens/2').status_code, 404)


@test_context.specialize(user=userperms([p.base.tokens.usr.view.all]),
                         db_setup=insert_usr)
def test_get_usr_token_view_all(client):
    """Getting a user token with base.tokens.usr.view.all returns the token"""
    eq_(json.loads(client.get('/tokenauth/tokens/2').data),
        {'result': usr_json})


@test_context.specialize(user=userperms([p.base.tokens.usr.view.my], email='me@me.com'),
                         db_setup=insert_usr)
def test_get_usr_token_view_my_matching(client):
    """Getting a user token with base.tokens.usr.view.my returns the token
    if the emails match"""
    eq_(json.loads(client.get('/tokenauth/tokens/2').data),
        {'result': usr_json})


@test_context.specialize(user=userperms([], email='me@me.com'),
                         db_setup=insert_usr)
def test_get_usr_token_view_my_nonmatching(client):
    """Getting my own user token without base.tokens.usr.view.my fails"""
    eq_(client.get('/tokenauth/tokens/2').status_code, 404)


@test_context.specialize(user=userperms([p.base.tokens.usr.view.my], email='OTHER'),
                         db_setup=insert_usr)
def test_get_usr_token_view_my_not_matching(client):
    """Getting a user token with base.tokens.usr.view.my returns 404 if the
    emails do not match"""
    eq_(client.get('/tokenauth/tokens/2').status_code, 404)


@test_context.specialize(user=userperms([p.base.tokens.prm.view]))
def test_get_token_missing(client):
    """Getting a token which doesn't exist returns 404"""
    eq_(client.get('/tokenauth/tokens/99').status_code, 404)


@test_context.specialize(user=userperms([]), db_setup=insert_prm)
def test_query_prm_token_forbidden(client):
    """Querying a permanent token requires base.tokens.prm.view"""
    res = client.post_json('/tokenauth/tokens/query',
                           FakeSerializer.prm(1))
    eq_(res.status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.usr.view.all]),
                         db_setup=insert_prm)
def test_query_prm_token_forbidden_wrong_perm(client):
    """Querying a permanent token requires base.tokens.prm.view"""
    res = client.post_json('/tokenauth/tokens/query',
                           FakeSerializer.prm(1))
    eq_(res.status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.prm.view]), db_setup=insert_prm)
def test_query_prm_token_exists(client):
    """Querying a permanent token, with base.tokens.prm.view, returns that token."""
    res = client.post_json('/tokenauth/tokens/query',
                           FakeSerializer.prm(1))
    eq_(res.status_code, 200)
    eq_(json.loads(res.data),
        {'result': {'id': 1, 'description': 'Zig only', 'typ': 'prm',
                    'permissions': ['test_tokenauth.zig'],
                    'disabled': False}})


@test_context.specialize(user=userperms([]), db_setup=insert_usr)
def test_query_usr_token_forbidden(client):
    """Querying a user token without permission results in a 403"""
    res = client.post_json('/tokenauth/tokens/query',
                           FakeSerializer.usr(2))
    eq_(res.status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.usr.view.my], email='OTHER'),
                         db_setup=insert_usr)
def test_query_usr_token_forbidden_not_mine(client):
    """Querying a user token with base.tokens.usr.view.my gives 403
    if the token email doesn't match the request email"""
    res = client.post_json('/tokenauth/tokens/query',
                           FakeSerializer.usr(2))
    eq_(res.status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.usr.view.my], email='me@me.com'),
                         db_setup=insert_usr)
def test_query_usr_token_success_mine(client):
    """Querying a user token with base.tokens.usr.view.my returns the
    token if the emails match"""
    res = client.post_json('/tokenauth/tokens/query',
                           FakeSerializer.usr(2))
    eq_(json.loads(res.data), {'result': usr_json})


@test_context.specialize(user=userperms([p.base.tokens.usr.view.all]),
                         db_setup=insert_usr)
def test_query_usr_token_success_all(client):
    """Querying a user token with base.tokens.usr.view.all returns the token."""
    res = client.post_json('/tokenauth/tokens/query',
                           FakeSerializer.usr(2))
    eq_(json.loads(res.data), {'result': usr_json})


@test_context.specialize(user=userperms([p.base.tokens.prm.view]))
def test_query_token_missing(client):
    """Querying a permanent token that does not exist returns status 404"""
    res = client.post_json('/tokenauth/tokens/query',
                           FakeSerializer.prm(99))
    eq_(res.status_code, 404)


@test_context.specialize(user=userperms([]), db_setup=insert_prm)
def test_query_tmp_token(client):
    """Querying a temporary token returns that token's info,
    without requiring any special permissions"""
    tok = FakeSerializer.tmp(
        nbf=946684800,  # Jan 1, 2000
        exp=32503680000,  # Jan 1, 3000
        prm=['test_tokenauth.zag'],
        mta={})
    res = client.post_json('/tokenauth/tokens/query', tok)
    eq_(res.status_code, 200)
    eq_(json.loads(res.data),
        {'result': {
            'typ': 'tmp',
            'not_before': '2000-01-01T00:00:00+00:00',
            'expires': '3000-01-01T00:00:00+00:00',
            'metadata': {},
            'permissions': ['test_tokenauth.zag'],
            'disabled': False,
        }})


@test_context.specialize(user=userperms([p.base.tokens.prm.view]))
def test_query_token_invalid(client):
    """Passing an invalid string to query a token returns 404"""
    res = client.post_json('/tokenauth/tokens/query', 'XXX')
    eq_(res.status_code, 404)


@test_context.specialize(user=userperms([]), db_setup=insert_prm)
def test_revoke_prm_token_forbidden(client):
    """Permanent token revocation requires base.tokens.prm.revoke"""
    eq_(client.delete('/tokenauth/tokens/1').status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.prm.revoke]),
                         db_setup=insert_prm)
def test_revoke_prm_token_exists(app, client):
    """Revoking a permanent token returns a 204 status and deletes the row."""
    eq_(client.delete('/tokenauth/tokens/1').status_code, 204)
    with app.app_context():
        token_data = Token.query.filter_by(id=1).first()
        eq_(token_data, None)


@test_context.specialize(user=userperms([]), db_setup=insert_usr)
def test_revoke_usr_token_forbidden(client):
    """User token revocation requires base.tokens.usr.revoke.*"""
    eq_(client.delete('/tokenauth/tokens/2').status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.usr.revoke.my], email='OTHER'),
                         db_setup=insert_usr)
def test_revoke_usr_token_forbidden_not_mine(client):
    """User token revocation with base.tokens.usr.revoke.my requires
    emails to match"""
    eq_(client.delete('/tokenauth/tokens/2').status_code, 403)


@test_context.specialize(user=userperms([p.base.tokens.usr.revoke.my], email='me@me.com'),
                         db_setup=insert_usr)
def test_revoke_usr_token_success_mine(client):
    """User token revocation with base.tokens.usr.revoke.my succeeds
    when emails match."""
    eq_(client.delete('/tokenauth/tokens/2').status_code, 204)


@test_context.specialize(user=userperms([p.base.tokens.usr.revoke.all]),
                         db_setup=insert_usr)
def test_revoke_usr_token_success_all(client):
    """User token revocation with base.tokens.usr.revoke.all succeeds
    regardless of whether emails match."""
    eq_(client.delete('/tokenauth/tokens/2').status_code, 204)


@test_context.specialize(user=userperms([p.base.tokens.prm.revoke]),
                         db_setup=insert_prm)
def test_revoke_token_missing(app, client):
    """Revoking a token returns a 204 status even if no such token existed."""
    eq_(client.delete('/tokenauth/tokens/99').status_code, 403)


@test_context
def test_token_row_undefined_permissions(app):
    """If a token row contains an undefined permission, that permission
    is ignored when the token is loaded."""
    t = Token(
        id=20,
        typ='prm',
        _permissions='test_tokenauth.zig,not.a.real.permission',
        description="permtest")
    eq_(t.permissions, [p.test_tokenauth.zig])


@test_context
def test_token_row_empty_permissions(app):
    """If a token row contains no permissions, that remains the case
    after the permissions are serialized and deserialized."""
    t = Token(
        id=20,
        typ='prm',
        permissions=[],
        description="permtest")
    eq_(t.permissions, [])
