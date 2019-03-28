# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pathlib

import pytest


def create_html(folder, items):
    import shipit_api.product_details
    return shipit_api.product_details.create_index_listing_html(
        pathlib.Path(folder),
        [pathlib.Path(item) for item in items],
    )


@pytest.mark.parametrize('product_details, product_details_final', (
    (
        {
            '1.0/all.json': {},
            '1.0/l10n/en.json': {},
        },
        {
            '1.0/all.json': {},
            '1.0/l10n/en.json': {},
            'index.html': create_html('', ['1.0']),
            '1.0/index.html': create_html('1.0', ['1.0/all.json', '1.0/l10n']),
            '1.0/l10n/index.html': create_html('1.0/l10n', ['1.0/l10n/en.json']),
        },
    ),
))
def test_create_index_listing(product_details, product_details_final):
    import shipit_api.product_details
    assert shipit_api.product_details.create_index_listing(product_details) == product_details_final
