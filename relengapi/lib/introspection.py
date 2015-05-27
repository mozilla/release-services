# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pkg_resources

_distributions = None


def _fetch():
    global _distributions

    if not _distributions:
        _distributions = {}
        for dist in pkg_resources.WorkingSet():
            _distributions[dist.key] = dist


def get_distributions():
    _fetch()
    return _distributions
