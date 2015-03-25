# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from itsdangerous import BadData
from relengapi import p
from relengapi.blueprints.tokenauth.tables import Token

# test utilities


class FakeSerializer(object):

    """A token serializer that produces a readable serialization, for use in
    tests."""

    @staticmethod
    def prm(id):
        return FakeSerializer.dumps(
            {"iss": "ra2", "jti": "t%d" % id, "typ": "prm"})

    @staticmethod
    def tmp(nbf, exp, prm, mta):
        return FakeSerializer.dumps(
            {"iss": "ra2", "typ": "tmp", 'nbf': nbf,
             "exp": exp, "prm": prm, "mta": mta})

    @staticmethod
    def usr(id):
        return FakeSerializer.dumps(
            {"iss": "ra2", "jti": "t%d" % id, "typ": "usr"})

    @staticmethod
    def dumps(data):
        return 'FK:' + json.dumps(data,
                                  separators=(',', ':'),
                                  sort_keys=True)

    @staticmethod
    def loads(data):
        if data[:3] != 'FK:':
            raise BadData('Not a fake token')
        else:
            return json.loads(data[3:])

# sample tokens, both a function to insert, and a JSON representation of the
# corresponding result.


def insert_prm(app):
    session = app.db.session('relengapi')
    t = Token(
        id=1,
        typ='prm',
        disabled=False,
        permissions=[p.test_tokenauth.zig],
        description="Zig only")
    session.add(t)
    session.commit()


prm_json = {
    'id': 1,
    'typ': 'prm',
    'description': 'Zig only',
    'permissions': ['test_tokenauth.zig'],
    'disabled': False,
}


def insert_usr(app, permissions=[p.test_tokenauth.zig], disabled=False):
    session = app.db.session('relengapi')
    t = Token(
        id=2,
        typ='usr',
        user='me@me.com',
        permissions=permissions,
        disabled=disabled,
        description="User Zig")
    session.add(t)
    session.commit()


usr_json = {
    'id': 2,
    'typ': 'usr',
    'user': 'me@me.com',
    'description': 'User Zig',
    'permissions': ['test_tokenauth.zig'],
    'disabled': False,
}


def insert_all(app):
    insert_prm(app)
    insert_usr(app)
