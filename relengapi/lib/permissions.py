# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wrapt
import wsme.types

from flask import abort
from flask import current_app
from flask.ext.login import current_user
from relengapi import util


class Permission(tuple):

    def doc(self, doc):
        self.__doc__ = doc
        self._all[self] = self

    def __getattr__(self, attr):
        new = Permission(self + (attr,))
        new._all = self._all
        setattr(self, attr, new)
        return new

    def exists(self):
        return self in self._all

    def require(self):
        return require(self)

    def can(self):
        return can(self)

    def __str__(self):
        return '.'.join(self)


class Permissions(Permission):

    def __init__(self):
        super(Permissions, self).__init__()
        self._all = {}

    def __getitem__(self, index):
        if not isinstance(index, tuple):
            index = tuple(index.split('.'))
        return self._all[index]

    def __iter__(self):
        return ((prm, prm.__doc__) for prm in self._all.itervalues())

    def get(self, index, default=None):
        try:
            return self[index]
        except KeyError:
            return default

    @staticmethod
    def can(*permissions):
        """
        Verify that the current user has all of the specified permissions.
        """
        assert permissions, "Must specify at least one permission"
        return all(perm in current_user.permissions for perm in permissions)

    @staticmethod
    def require(*permissions):
        """
        Wrap a view function, verifying that the user hsa all of the specified
        permissions.
        """
        assert permissions, "Must specify at least one permission"
        for perm in permissions:
            if not perm.exists():
                raise RuntimeError(
                    "Cannot require undocumented permission %s" % (perm,))

        @wrapt.decorator
        def req(wrapped, instance, args, kwargs):
            if not can(*permissions):
                # redirect browsers when the user is not logged in, but
                # just return 403 to REST clients
                if util.is_browser() and current_user.is_anonymous():
                    return current_app.login_manager.unauthorized()
                else:
                    abort(403)
            return wrapped(*args, **kwargs)
        return req

require = Permissions.require
can = Permissions.can

# this object is generally accessed at `relengapi.p`, but can be accessed here
# for imports in relengapi itself, which occur before `relengapi.p` exists.
p = Permissions()


class JsonPermission(wsme.types.Base):

    _name = "Permission"

    #: Dotted name of the permission
    name = unicode

    #: Documentation for the permission
    doc = unicode
