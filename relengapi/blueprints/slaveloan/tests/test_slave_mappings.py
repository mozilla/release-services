# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock
import re

from nose.tools import eq_
from nose.tools import ok_
from relengapi.blueprints.slaveloan import slave_mappings
from relengapi.lib.testing.context import TestContext

test_context = TestContext()

test_slavetype_map = {
    "foobar": [
        re.compile("^foobar-"),
        re.compile("^foo-")
    ],
    "banana": [
        re.compile("^banana-"),
        re.compile("^orange-"),
        re.compile("^apple-")
    ],
    "zodiac": [
        re.compile("^zodiac-"),
        re.compile("^libra-"),
        re.compile("^leo-"),
        re.compile("^virgo-")
    ]
}

test_gpo_needed_list = ["foobar", "zodiac"]


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

    with mock.patch.dict("relengapi.blueprints.slaveloan.slave_mappings._slave_type",
                         test_slavetype_map,
                         clear=True):
        eq_("foobar", s2st("foobar"))
        eq_("foobar", s2st("foobar-"))
        eq_("foobar", s2st("foobar-10"))
        eq_("foobar", s2st("foo-10"))
        eq_("banana", s2st("apple-10"))
        eq_("banana", s2st("orange-999"))
        eq_(None, s2st("america-100"), msg="None should be returned in a failed match")


@test_context
def test_gpo_needed_matches_keys():
    "Test that matches for gpo are based on above keys"
    map = slave_mappings._slave_type.keys()
    for gpo in slave_mappings._gpo_needed:
        ok_(gpo in map, msg="_gpo_needed should only contain loan types")


@test_context
def test_needs_gpo():
    "Test that a value in gpo keys returns true, and that a value missing returns false"
    ngpo = slave_mappings.needs_gpo

    with mock.patch.dict("relengapi.blueprints.slaveloan.slave_mappings._slave_type",
                         test_slavetype_map,
                         clear=True):
        with mock.patch("relengapi.blueprints.slaveloan.slave_mappings._gpo_needed",
                        new=test_gpo_needed_list):
            ok_(not ngpo("invalid"),
                msg="GPO not needed for an invalid slave")
            ok_(not ngpo("apple-10"),
                msg="GPO not needed for an slave that doesn't directly match a key")
            ok_(not ngpo("banana"),
                msg="GPO not needed for an slave that matches a slavetype key but not in gpo list")
            ok_(ngpo("foo-10"),
                msg="GPO needed for a slave that doesn't directly match a key")
            ok_(ngpo("foobar"),
                msg="GPO needed for a slave that directly matches a key")
            ok_(ngpo("libra-99"),
                msg="GPO needed for a slave that is not first match on gpo keys")
