# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def is_key_present_in_list_of_dicts(key, list_of_dicts):
    return any(key in dict_ for dict_ in list_of_dicts)
