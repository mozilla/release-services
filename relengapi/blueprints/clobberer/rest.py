# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types


class ClobberRequest(wsme.types.Base):

    "Represents a clobber request for some list of builders"

    id = int
    branch = unicode
    master = unicode
    slave = unicode
    builddir = unicode
