import mock
import re

from nose.tools import eq_
from nose.tools import ok_
from relengapi.blueprints.slaveloan import slave_mappings
from relengapi.lib.testing.context import TestContext

test_context = TestContext()


@test_context
def test_slave_type_map_format_keys():
    "Test that the slave type mapping has string-based keys"
    map = slave_mappings._slave_type
    for k in map.keys():
        ok_(isinstance(k, basestring))


@test_context
def test_slave_type_map_format_values():
    "Test that the slave type mapping has lists as values, with regex items in the expected format"
    re_type = type(re.compile("hello, world"))
    map = slave_mappings._slave_type
    for k in map.keys():
        ok_(isinstance(map[k], list))
        for v in map[k]:
            ok_(isinstance(v, re_type))
            # Codifies assumption of hyphen at end of pattern
            eq_(v.pattern[-1:], '-')
            # Codifies assumption of matching only start of string
            eq_(v.pattern[:1], '^')


@test_context
def test_slavetype_to_slave_returns_exact_match():
    "Test that the slave to slavetype mappings func can return an exact match"
    keys = slave_mappings._slave_type.keys()
    eq_(keys[0], slave_mappings.slave_to_slavetype(keys[0]))
    # Test two choices, but using -1 prevents failure if the list has one item only
    eq_(keys[-1], slave_mappings.slave_to_slavetype(keys[-1]))


@test_context
def test_slavetype_to_slave_returns_match():
    "Test that the slave to slavetype func can scan a list of values properly"
    s2st = slave_mappings.slave_to_slavetype
    test_map = {
        "foobar": [
            re.compile("^foobar-"),
            re.compile("^foo-")
        ],
        "banana": [
            re.compile("^banana-"),
            re.compile("^orange-"),
            re.compile("^apple-")
        ]
    }

    with mock.patch.dict("relengapi.blueprints.slaveloan.slave_mappings._slave_type",
                         test_map,
                         clear=True):
        eq_("foobar", s2st("foobar"))
        eq_("foobar", s2st("foobar-"))
        eq_("foobar", s2st("foobar-10"))
        eq_("foobar", s2st("foo-10"))
        eq_("banana", s2st("apple-10"))
        eq_("banana", s2st("orange-999"))
        eq_(None, s2st("america-100"), msg="None should be returned in a failed match")
