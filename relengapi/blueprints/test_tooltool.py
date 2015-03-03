# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from relengapi.lib.testing.context import TestContext

test_context = TestContext()

TEST_HASH = '51781032335c09103e8509b1a558bf22a7119392cf1ea301c49c01bdf21ff0ce' \
            'b37d260bc1c322cd9b903252429fb01830fc27e4632be30cd345c95bf4b1a39b'


@test_context
def test_get_by_hash(client):
    """The /sha512/<hash> returns a 302 redirect to tooltool.pvt (temporarily)"""
    rv = client.get('/tooltool/sha512/{}'.format(TEST_HASH))
    eq_(rv.status_code, 302)
    eq_(rv.headers['Location'],
        'http://tooltool.pvt.build.mozilla.org/build/sha512/{}'.format(TEST_HASH))
