# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from datetime import datetime

import wsme.types


class JsonTree(wsme.types.Base):

    """A representation of a single tree.
    """

    _name = 'Tree'

    #: the name of the tree
    tree = wsme.types.wsattr(unicode, mandatory=True)

    #: the current status
    status = wsme.types.wsattr(unicode, mandatory=True)

    #: the reason for the status
    reason = wsme.types.wsattr(unicode, mandatory=True)

    #: even more information about the status
    message_of_the_day = wsme.types.wsattr(unicode, mandatory=True)


class JsonTreeLog(wsme.types.Base):

    """ A recorded change to a tree's status or reason, along with a set of
    tags assigned at the time.  This is useful for analysis of tree closures
    and their causes.  """

    _name = 'TreeLog'

    #: the name of the tree
    tree = wsme.types.wsattr(unicode, mandatory=True)

    #: the time the change occurred
    when = wsme.types.wsattr(datetime, mandatory=True)

    #: the user making the change
    who = wsme.types.wsattr(unicode, mandatory=True)

    #: the new status
    status = wsme.types.wsattr(unicode, mandatory=True)

    #: the reason for the status
    reason = wsme.types.wsattr(unicode, mandatory=True)

    #: tags for the change
    tags = wsme.types.wsattr([unicode], mandatory=True)


class JsonStateChange(wsme.types.Base):

    """A change to one or more trees' status, suitable for reverting the
    change.  Some of the information here is redundant to TreeLog, but is
    present to help users determine which change to revert.  The previous state
    of the tree is not exposed in this data type.  """

    _name = 'TreeStateChange'

    #: id of this change
    id = wsme.types.wsattr(int, mandatory=True)

    #: the names of the affected trees
    trees = wsme.types.wsattr([unicode], mandatory=True)

    #: the time the change occurred
    when = wsme.types.wsattr(datetime, mandatory=True)

    #: the user who made the change
    who = wsme.types.wsattr(unicode, mandatory=True)

    #: the updated (new) status
    status = wsme.types.wsattr(unicode, mandatory=True)

    #: the reason for the status change
    reason = wsme.types.wsattr(unicode, mandatory=True)


class JsonTreeUpdate(wsme.types.Base):

    """A requested update to one or more trees.  See the corresponding method
    for information on which fields must be supplied and when.  """

    _name = 'TreeUpdate'

    #: the trees to update
    trees = wsme.types.wsattr([unicode], mandatory=True)

    #: the new tree status (for all affected trees)
    status = wsme.types.wsattr(unicode)

    #: the reason for the status
    reason = wsme.types.wsattr(unicode)

    #: the message of the day for the tree
    message_of_the_day = wsme.types.wsattr(unicode)

    #: tags associated with the status update; this is required (including at
    #: least one tag) if status = 'closed',

    tags = wsme.types.wsattr([unicode])

    #: if true, add the change to the status and reason to the undo stack.
    #: Note that updates to the message of the day are not recorded.
    remember = wsme.types.wsattr(bool)
