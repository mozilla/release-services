# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib

from nose.tools import eq_
from relengapi.blueprints.tooltool import util

ONE = '1\n'
ONE_DIGEST = hashlib.sha512(ONE).hexdigest()


def test_keyname():
    eq_(util.keyname(ONE_DIGEST), 'sha512/' + ONE_DIGEST)
