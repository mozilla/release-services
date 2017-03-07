# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib


def gravatar(email):
    """
    Build a gravatar url from an email address
    """
    email = email.lower()
    h = hashlib.md5(email.encode('utf-8'))
    return 'https://www.gravatar.com/avatar/{}'.format(h.hexdigest())
