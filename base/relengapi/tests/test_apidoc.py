# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types

from nose.tools import eq_
from relengapi.lib import apidoc


def test_typename():
    """typename should return an object's _name attribute or its __name__ attribute"""
    def foo():
        pass
    eq_(apidoc.typename(foo), 'foo')
    foo._name = 'bar'
    eq_(apidoc.typename(foo), 'bar')


def test_typereference_UserType():
    """typereference should return the name of a UserType"""
    eq_(apidoc.typereference(wsme.types.binary), 'binary')


def test_typereference_str_dict():
    """typereference should describe a dictionary with string keys as {"...":
        <some type>}"""
    eq_(apidoc.typereference(
        wsme.types.DictType(unicode, int)), '{"...": int}')


def test_typereference_int_dict():
    """typereference should describe a dictionary with other keys as
    {<type>:<type>}"""
    eq_(apidoc.typereference(
        wsme.types.DictType(int, unicode)), '{int: unicode}')


def test_typereference_array():
    """typereference should describe a list as [<type>]"""
    eq_(apidoc.typereference(wsme.types.ArrayType(int)), '[int]')


def test_typereference_complex():
    """typereference should describe a complex type with an ':api:type:' reference"""
    class SomeType(wsme.types.Base):
        id = int

    eq_(apidoc.typereference(SomeType), ':api:type:`SomeType`')


def test_typereference_unknown():
    """typereference should describe an unkonwn object with its name"""
    eq_(apidoc.typereference(complex), 'complex')
