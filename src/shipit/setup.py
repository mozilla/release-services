# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from setuptools import find_packages
from setuptools import setup

here = os.path.dirname(__file__)

setup(
    name='shipit',
    version=open(os.path.join(here, 'VERSION')).read().strip(),
    description='The code behind https://ship-it.mozilla-releng.net',
    author='Mozilla RelEng',
    author_email='release@mozilla.com',
    url='https://ship-it.mozilla-releng.net',
    install_requires=[
        "releng_common",
    ],
    extras_require={
    },
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            'releng = releng.cmd:main',
        ],
    },
    license='MPL2',
)
