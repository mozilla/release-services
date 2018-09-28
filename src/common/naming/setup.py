# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import setuptools


with open('VERSION') as f:
    VERSION = f.read().strip()


setuptools.setup(
    name='mozilla-release-common-naming',
    version=VERSION,
    description='A utility on how to name projects',
    author='Mozilla Release Services Team',
    author_email='release-services@mozilla.com',
    url='https://docs.mozilla-releng.net/projects/common.html',
    tests_require=read_requirements('requirements-dev.txt'),
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
