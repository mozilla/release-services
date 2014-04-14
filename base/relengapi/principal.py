# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask.ext.principal import Permission

class RoleElt(tuple):

    def doc(self, doc):
        self.__doc__ = doc
        self.all[self] = self

    def __getattr__(self, attr):
        new = RoleElt(self + (attr,))
        new.all = self.all
        setattr(self, attr, new)
        return new

    def require(self):
        if self not in self.all:
            raise RuntimeError("Cannot require undocumented permission %r" % '.'.join(self))
        return Permission(self).require()


class RootRoleElt(RoleElt):

    def __init__(self):
        self.all = {}

    def __getitem__(self, index):
        if not isinstance(index, tuple):
            index = tuple(index.split('.'))
        return self.all[index]


roles = RootRoleElt()
