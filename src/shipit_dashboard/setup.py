# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from setuptools import find_packages
from setuptools import setup

here = os.path.dirname(__file__)

with open(os.path.join(here, 'VERSION')) as f:
    version = f.read().strip()

setup(
    name='shipit_dashboard',
    version=version,
    description='The code behind https://dashboard.shipit.mozilla-releng.net',
    author='Mozilla Release Engineering',
    author_email='release@mozilla.com',
    url='https://dashboard.shipit.mozilla-releng.net',
    tests_require=[
        'flake8',
        'pytest',
    ],
    install_requires=[
        'releng_common[log,api,cors,auth,db]',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
