# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import assert_raises
from nose.tools import eq_
from relengapi.blueprints.tokenauth import tokenstr
from relengapi.lib.testing.context import TestContext

test_context = TestContext(reuse_app=True)


@TestContext()
def test_str_to_claims_valid_v1(app):
    with app.app_context():
        input_claims = {'id': 25, 'v': 1}
        token_str = app.tokenauth_serializer.dumps(input_claims)
        got_claims = tokenstr.str_to_claims(token_str)
        # v1 token is rewritten to ra2 format
        exp_claims = {'iss': 'ra2', 'typ': 'prm', 'jti': 't25'}
        eq_(got_claims, exp_claims)


@TestContext()
def test_str_to_claims_valid_v2(app):
    with app.app_context():
        input_claims = {'iss': 'ra2', 'typ': 'prm', 'jti': 't20'}
        token_str = app.tokenauth_serializer.dumps(input_claims)
        got_claims = tokenstr.str_to_claims(token_str)
        eq_(got_claims, input_claims)


@TestContext()
def test_str_to_claims_invalid_claims(app):
    with app.app_context():
        input_claims = {'in': 'valid'}
        token_str = app.tokenauth_serializer.dumps(input_claims)
        got_claims = tokenstr.str_to_claims(token_str)
        eq_(got_claims, None)


@TestContext()
def test_str_to_claims_invalid_str(app):
    with app.app_context():
        got_claims = tokenstr.str_to_claims('abcd')
        eq_(got_claims, None)


@TestContext()
def test_claims_to_str_to_claims(app):
    with app.app_context():
        input_claims = {'iss': 'ra2', 'typ': 'prm', 'jti': 't10'}
        token_str = tokenstr.claims_to_str(input_claims)
        got_claims = tokenstr.str_to_claims(token_str)
        eq_(got_claims, input_claims)


def test_jti2id():
    eq_(tokenstr.jti2id('t12'), 12)
    assert_raises(TypeError, lambda:
                  tokenstr.jti2id('xx'))
    assert_raises(TypeError, lambda:
                  tokenstr.jti2id(None))
