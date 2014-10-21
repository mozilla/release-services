# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types


class ClobberRequest(wsme.types.Base):
    "Represents a clobber request for a branch and build directory."

    branch = unicode  #: The branch for this clobber request.
    builddir = unicode  #: The build directory to be clobbered.
    #: A specific slave to clobber (defaults to all slaves).slave = unicode
    slave = wsme.types.wsattr(unicode, mandatory=False, default=None)


class ClobberTime(wsme.types.Base):
    "Represents the most recent data pertaining to a particular clobber."

    branch = unicode  #: The branch associated with this clobber.
    builddir = unicode  #: The clobbered directory.
    slave = unicode  #: A particular slave (null means all slaves).
    lastclobber = int  #: Timestamp associated with the last clobber request.
    who = unicode  #: User who initiated the last clobber.
