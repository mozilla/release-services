# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types


class ClobberRequest(wsme.types.Base):
    "Represents a clobber request"

    id = int
    branch = unicode  #: The branch for this clobber request
    master = unicode  #: (deprecated) The buildbot master
    slave = unicode  #: The buildbot slave for this clobber request
    builddir = unicode  #: The build directory to be clobbered
