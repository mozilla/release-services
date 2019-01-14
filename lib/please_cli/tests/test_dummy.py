# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pathlib


def test_import():
    please = pathlib.Path('../please')
    clean = False
    try:
        if not please.exists():
            clean = True
            with please.open('w+') as f:
                f.write('XXX')
        import please_cli  # noqa
    finally:
        if clean and please.exists():
            please.unlink()
