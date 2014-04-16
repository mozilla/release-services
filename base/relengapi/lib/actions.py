# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask.ext.principal import Permission


class Action(tuple):

    def doc(self, doc):
        self.__doc__ = doc
        self.all[self] = self

    def __getattr__(self, attr):
        new = Action(self + (attr,))
        new.all = self.all
        setattr(self, attr, new)
        return new

    def exists(self):
        return self in self.all

    def require(self):
        if not self.exists():
            raise RuntimeError(
                "Cannot require undocumented permission %r" % '.'.join(self))
        return Permission(self).require(http_exception=403)

    def __str__(self):
        return '.'.join(self)


class Actions(Action):

    def __init__(self):
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
