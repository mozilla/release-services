# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask.ext.login import UserMixin


class User(UserMixin):

    def __init__(self, authenticated_email):
        self.authenticated_email = authenticated_email

    def get_id(self):
        return unicode(self.authenticated_email)
