# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from contextlib import nullcontext as does_not_raise

import pytest
from mozilla_version.gecko import DeveditionVersion
from mozilla_version.gecko import FennecVersion
from mozilla_version.gecko import FirefoxVersion
from mozilla_version.gecko import ThunderbirdVersion

from shipit_api.release import Product
from shipit_api.release import bump_version
from shipit_api.release import is_eme_free_enabled
from shipit_api.release import is_partner_enabled
from shipit_api.release import is_rc
from shipit_api.release import parse_version


@pytest.mark.parametrize('product, version, expectation, result', (
    ('devedition', '56.0b1', does_not_raise(), DeveditionVersion(56, 0, beta_number=1)),
    (Product.DEVEDITION, '56.0b1', does_not_raise(), DeveditionVersion(56, 0, beta_number=1)),
    ('fennec', '68.2b3', does_not_raise(), FennecVersion(68, 2, beta_number=3)),
    (Product.FENNEC, '68.2b3', does_not_raise(), FennecVersion(68, 2, beta_number=3)),
    ('firefox', '45.0', does_not_raise(), FirefoxVersion(45, 0)),
    (Product.FIREFOX, '45.0', does_not_raise(), FirefoxVersion(45, 0)),
    ('thunderbird', '60.8.0', does_not_raise(), ThunderbirdVersion(60, 8, 0)),
    (Product.THUNDERBIRD, '60.8.0', does_not_raise(), ThunderbirdVersion(60, 8, 0)),
    ('non-existing-product', '68.0', pytest.raises(ValueError), None),
))
def test_parse_version(product, version, expectation, result):
    with expectation:
        assert parse_version(product, version) == result


@pytest.mark.parametrize('product, version, partial_updates, result', (
    ('firefox', '64.0', None, True),
    ('thunderbird', '64.0', None, False),
    ('fennec', '64.0', None, True),
    ('firefox', '64.0.1', None, False),
    ('thunderbird', '64.0.1', None, False),
    ('fennec', '64.0.1', None, False),
    ('firefox', '56.0b3', None, False),
    ('fennec', '56.0b3', None, False),
    ('firefox', '45.0esr', None, False),

    ('firefox', '57.0', {'56.0b1': [], '55.0': []}, True),
    ('firefox', '57.0', {'56.0': [], '55.0': []}, True),
    ('firefox', '57.0.1', {'57.0': [], '56.0.1': [], '56.0': []}, False),
    ('thunderbird', '57.0', {'56.0': [], '55.0': []}, False),
    ('thunderbird', '57.0', {'56.0': [], '56.0b4': [], '55.0': []}, True),
    ('firefox', '70.0b4', {'69.0b15': [], '69.0b16': [], '70.0b3': []}, False),
    ('devedition', '70.0b4', {'70.0b3': [], '70.0b1': [], '70.0b2': []}, False),
))
def test_is_rc(product, version, partial_updates, result):
    assert is_rc(product, version, partial_updates) == result


@pytest.mark.parametrize('product, version, result', (
    ('firefox', '45.0', '45.0.1'),
    ('firefox', '45.0.1', '45.0.2'),
    ('firefox', '45.0b3', '45.0b4'),
    ('firefox', '45.0esr', '45.0.1esr'),
    ('firefox', '45.0.1esr', '45.0.2esr'),
    ('firefox', '45.2.1esr', '45.2.2esr'),
    ('fennec', '68.1b2', '68.1b3'),
))
def test_bump_version(product, version, result):
    assert bump_version(product, version) == result


@pytest.mark.parametrize('product, version, result', (
    ('firefox', '59.0', False),
    ('firefox', '65.0b3', False),
    ('firefox', '65.0b8', True),
    ('firefox', '65.0', True),
    ('firefox', '65.0.1', True),
    ('firefox', '60.5.0esr', True),
    ('fennec', '65.0b8', False),
    ('fennec', '65.0', False),
))
def test_is_partner_enabled(product, version, result):
    assert is_partner_enabled(product, version) == result


@pytest.mark.parametrize('product, version, result', (
    ('firefox', '65.0b3', False),
    ('firefox', '65.0b8', True),
    ('firefox', '65.0', True),
    ('firefox', '65.0.1', True),
    ('firefox', '60.5.0esr', False),
    ('fennec', '65.0b8', False),
    ('fennec', '65.0', False),
))
def test_is_eme_free_enabled(product, version, result):
    assert is_eme_free_enabled(product, version) == result
