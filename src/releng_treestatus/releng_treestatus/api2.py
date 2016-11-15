# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import releng_treestatus.api1


def get_trees():
    return [i for i in releng_treestatus.api.get_trees().values()]
