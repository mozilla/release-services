# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from flask import session
from flask.ext.login import current_user
from nose.tools import assert_raises
from nose.tools import eq_
from nose.tools import with_setup
from relengapi import p
from relengapi.lib import auth
from relengapi.lib.testing.context import TestContext


test_context = TestContext()
p.test_lib_auth.a.doc("test perm a")
p.test_lib_auth.b.doc("test perm b")


def clear_loaders():
    auth._request_loaders = []


def test_AnonymousUser():
    u = auth.AnonymousUser()
    eq_(u.type, 'anonymous')
    eq_(str(u), 'anonymous:')
    eq_(u.is_authenticated(), False)
    eq_(u.is_active(), False)
    eq_(u.is_anonymous(), True)
    eq_(u.permissions, set())


@test_context
def test_HumanUser(app):
    u = auth.HumanUser("florence@nightingale.com")
    eq_(u.type, 'human')
    eq_(u.authenticated_email, 'florence@nightingale.com')
    eq_(str(u), 'human:florence@nightingale.com')
    eq_(u.is_authenticated(), True)
    eq_(u.is_active(), True)
    eq_(u.is_anonymous(), False)
    with app.test_request_context('/'):
        eq_(u.permissions, set())


@test_context
def test_HumanUser_perms_in_session(app):
    u = auth.HumanUser("florence@nightingale.com")
    with app.test_request_context('/'):
        session['perms'] = ['test_lib_auth.a']
        session['perms_exp'] = time.time() + 10000
        eq_(u.permissions, set([p.test_lib_auth.a]))
        del session['perms']
        # .. and still cached
        eq_(u.permissions, set([p.test_lib_auth.a]))


@test_context
def test_HumanUser_perms_session_expired(app):
    @auth.permissions_stale.connect_via(app)
    def set_perms(app, user, permissions):
        permissions.add(p.test_lib_auth.a)
        permissions.add(p.test_lib_auth.b)
    u = auth.HumanUser("florence@nightingale.com")
    with app.test_request_context('/'):
        session['perms'] = ['test_lib_auth.a']
        session['perms_exp'] = time.time() - 10000
        eq_(u.permissions, set([p.test_lib_auth.a, p.test_lib_auth.b]))
        eq_(sorted(session['perms']),
            ['test_lib_auth.a', 'test_lib_auth.b'])
        assert session['perms_exp'] > time.time()


@with_setup(clear_loaders, clear_loaders)
@test_context
def test_request_loader(app, client):
    @auth.request_loader
    def rl(req):
        if 'user' in req.headers:
            return auth.HumanUser(req.headers['user'])

    @app.route("/test")
    def test():
        return str(current_user)
    eq_(client.get('/test').data, 'anonymous:')
    eq_(client.get('/test', headers=[('user', 'f@n.com')]).data,
        'human:f@n.com')


@with_setup(clear_loaders, clear_loaders)
def test_request_loader_not_set():
    bad_user = auth.HumanUser('me@me.com')
    bad_user._permissions = 'not-a-set'
    auth._request_loaders = [lambda req: bad_user]
    assert_raises(TypeError, lambda:
                  auth._request_loader(None))


@test_context
def test_login_request(client):
    assert 'A valid login is required' in client.get('/login_request').data


@test_context.specialize(user=auth.HumanUser('jeanne'))
def test_login_request_logged_in(client):
    resp = client.get('/login_request')
    eq_((resp.status_code, resp.headers[
        'location']), (302, 'http://localhost/'))


@test_context.specialize(user=auth.HumanUser('jeanne'))
def test_login_request_logged_in_next(client):
    resp = client.get('/login_request?next=/foo')
    eq_((resp.status_code, resp.headers[
        'location']), (302, 'http://localhost/foo'))


@test_context
def test_clear_perms_cache(app):
    with app.test_request_context('/'):
        session['perms'] = ['test_lib_auth.a']
        session['perms_exp'] = time.time() + 10000
        auth._clear_perms_cache()
        assert 'perms' not in session
        assert 'perms_exp' not in session


@test_context
def test_config_invalid_auth_type(app):
    app.config['RELENGAPI_AUTHENTICATION'] = {'type': 'no-such'}
    assert_raises(RuntimeError, lambda:
                  auth.init_app(app))


@test_context
def test_config_invalid_perm_type(app):
    app.config['RELENGAPI_PERMISSIONS'] = {'type': 'no-such'}
    assert_raises(RuntimeError, lambda:
                  auth.init_app(app))
