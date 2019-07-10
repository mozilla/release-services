# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import setuptools


setuptools.setup(
    name='code_coverage_tools',
    version='0.1.0',
    description='Support tools for Mozilla code coverage',
    author='Mozilla Release Management',
    author_email='release-mgmt-analysis@mozilla.com',
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
