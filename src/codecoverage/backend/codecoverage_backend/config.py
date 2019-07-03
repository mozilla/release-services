# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

PROJECT_NAME = 'code-coverage-backend'
APP_NAME = 'codecoverage_backend'
COVERAGE_EXTENSIONS = [
    # C
    'c', 'h',
    # C++
    'cpp', 'cc', 'cxx', 'hh', 'hpp', 'hxx',
    # JavaScript
    'js', 'jsm', 'xul', 'xml', 'html', 'xhtml',
]
