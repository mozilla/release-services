# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wrapt
from flask import abort
from flask.ext.login import current_user, login_required


class Permission(tuple):

    def doc(self, doc):
        self.__doc__ = doc
        self.all[self] = self

    def __getattr__(self, attr):
        new = Permission(self + (attr,))
        new.all = self.all
        setattr(self, attr, new)
        return new

    def exists(self):
        return self in self.all

    def require(self):
        return require(self)

    def can(self):
        return can(self)

    def __str__(self):
        return '.'.join(self)


class Permissions(Permission):

    def __init__(self):
        super(Permissions, self).__init__()
        self.all = {}

    def __getitem__(self, index):
        if not isinstance(index, tuple):
            index = tuple(index.split('.'))
        return self.all[index]

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
                    "Cannot require undocumented permission %s" % perm)

        @wrapt.decorator
        @login_required
        def req(wrapped, instance, args, kwargs):
            if not can(*permissions):
                abort(403)
            return wrapped(*args, **kwargs)
        return req

require = Permissions.require
can = Permissions.can

# this object is generally accessed at `relengapi.p`, but can be accessed here
# for imports in relengapi itself, which occur before `relengapi.p` exists.
p = Permissions()
