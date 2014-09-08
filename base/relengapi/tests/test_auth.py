# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from relengapi.lib import auth


def test_user_loader():
    eq_(auth._user_loader('human:jimmy@foo.com'),
        auth.HumanUser('jimmy@foo.com'))


def test_user_loader_nonhuman():
    eq_(auth._user_loader('alien:jimmy@foo.com'),
        None)


def test_user_loader_invalid():
    eq_(auth._user_loader('somedata'),
        None)
