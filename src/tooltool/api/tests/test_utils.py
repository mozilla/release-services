# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib


def test_now():
    import tooltool_api.utils

    assert tooltool_api.utils.now().tzname() == 'UTC'


def test_keyname():
    import tooltool_api.utils

    ONE = '1\n'
    ONE_DIGEST = hashlib.sha512(ONE.encode('utf-8')).hexdigest()

    assert tooltool_api.utils.keyname(ONE_DIGEST) == 'sha512/' + ONE_DIGEST


def test_is_valid_sha512():
    import tooltool_api.utils

    VALID_SHA512 = '1' * 128

    assert tooltool_api.utils.is_valid_sha512('123') is None
    assert tooltool_api.utils.is_valid_sha512(VALID_SHA512).string == VALID_SHA512
