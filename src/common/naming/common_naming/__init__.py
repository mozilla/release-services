# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re


LETTERS = re.compile('[^a-zA-Z]')


class Project:

    def __init__(self, name):
        self.name = name

    @property
    def python_module_name(self):
        return LETTERS.sub('_', self.name)

    @property
    def python_distribution_name(self):
        return f'mozilla-release-{LETTERS.sub("-", self.name)}'

    @property
    def flask_app_name(self):
        return LETTERS.sub('_', self.name)
