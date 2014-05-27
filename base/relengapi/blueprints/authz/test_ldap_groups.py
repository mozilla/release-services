# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy
import mockldap
import unittest
import logging
import logging.handlers
from nose.tools import eq_
from relengapi.testing import TestContext
from relengapi import actions
from relengapi.blueprints.authz import ldap_groups

actions.test_ldap_groups.foo.doc("Foo")
actions.test_ldap_groups.bar.doc("Bar")

URI = 'ldap://localhost/'
CONFIG = {
    'RELENGAPI_ACTIONS': {
        'uri': URI,
        'login_dn': 'cn=bind,o=users',
        'login_password': 'bindpw',
        'user_base': 'o=users',
        'group_base': 'o=groups',
        'debug': True,
        'group-actions': {
            'group1': ['test_ldap_groups.foo'],
            'group2': ['test_ldap_groups.foo', 'test_ldap_groups.bar'],
            'group3': ['test_ldap_groups.bar'],
        },
    },
}
BAD_CONFIG = copy.deepcopy(CONFIG)
BAD_CONFIG['RELENGAPI_ACTIONS']['login_password'] = 'invalid'
test_context = TestContext(reuse_app=True, config=CONFIG)


class Identity(object):

    def __init__(self, auth_type, identifier):
        self.auth_type = auth_type
        self.id = identifier
        self.provides = set()


# tests

class TestGetUserGroups(unittest.TestCase):

    directory = {
        'o=users': {'o': 'users'},
        'cn=bind,o=users': {
            'objectClass': ['inetOrgPerson'],
            'cn': ['bind'],
            'userPassword': ['bindpw'],
        },
        'ou=people,o=users': {'ou': 'people'},
        'cn=jimmy,ou=people,o=users': {
            'objectClass': ['inetOrgPerson'],
            'cn': ['jimmy'],
            'mail': ['jimmy@org.org'],
        },
        'cn=mary,ou=people,o=users': {
            'objectClass': ['inetOrgPerson'],
            'cn': ['mary'],
            'mail': ['mary@org.org'],
        },
        'o=groups': {'o': 'groups'},
        'cn=authors,o=groups': {
            'objectClass': ['groupOfNames'],
            'cn': ['authors'],
            'member': ['cn=jimmy,ou=people,o=users', 'cn=mary,ou=people,o=users'],
        },
        'cn=editors,o=groups': {
            'objectClass': ['groupOfNames'],
            'cn': ['editors'],
            'member': ['cn=mary,ou=people,o=users'],
        },
        'cn=c-suite,o=groups': {
            'objectClass': ['groupOfNames'],
            'cn': ['c-suite'],
            'member': [],
        },
    }

    @classmethod
    def setupClass(cls):
        cls.mockldap = mockldap.MockLdap(cls.directory)

    @classmethod
    def tearDownClass(cls):
        del cls.mockldap

    def setUp(self):
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']

    def tearDown(self):
        self.mockldap.stop()
        del self.ldapobj

    @test_context
    def call(self, app, mail, exp_groups):
        lg = ldap_groups.LdapGroups(app)
        eq_(sorted(lg.get_user_groups(mail)), sorted(exp_groups))

    def test_get_user_groups_single(self):
        self.call(mail='jimmy@org.org', exp_groups=['authors'])

    def test_get_user_groups_multiple(self):
        self.call(mail='mary@org.org', exp_groups=['authors', 'editors'])

    def test_get_user_groups_nosuch(self):
        self.call(mail='steve@org.org', exp_groups=[])

    @test_context.specialize(config=BAD_CONFIG)
    def test_login_fail(self, app):
        hdlr = logging.handlers.BufferingHandler(100)
        logging.getLogger(ldap_groups.__name__).addHandler(hdlr)
        try:
            lg = ldap_groups.LdapGroups(app)
            eq_(sorted(lg.get_user_groups('x@y')), [])
            # make sure the error was logged
            for rec in hdlr.buffer:
                if rec.msg.startswith('While connecting to the LDAP server'):
                    break
            else:
                self.fail("login exception not logged")
        finally:
            logging.getLogger(ldap_groups.__name__).removeHandler(hdlr)


@test_context
def test_on_identity_loaded_not_user(app):
    ident = Identity('token', 'abcde')
    lg = ldap_groups.LdapGroups(app)
    lg.on_identity_loaded('sender', ident)
    eq_(ident.provides, set())


@test_context
def test_on_identity_loaded_groups_unique(app):
    ident = Identity('user', 'jimmy')
    lg = ldap_groups.LdapGroups(app)
    lg.get_user_groups = lambda mail: ['group1', 'group2']
    lg.on_identity_loaded('sender', ident)
    eq_(ident.provides, set(
        [actions.test_ldap_groups.foo, actions.test_ldap_groups.bar]))


@test_context
def test_on_identity_loaded_groups_unknown_groups(app):
    ident = Identity('user', 'jimmy')
    lg = ldap_groups.LdapGroups(app)
    lg.get_user_groups = lambda mail: ['group3', 'nosuch']
    lg.on_identity_loaded('sender', ident)
    eq_(ident.provides, set([actions.test_ldap_groups.bar]))
