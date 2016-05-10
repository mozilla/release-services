# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from setuptools import find_packages
from setuptools import setup

here = os.path.dirname(__file__)

setup(
    name='relengapi_clobberer',
    version=open(os.path.join(here, 'VERSION')).read().strip(),
    description='The code behind https://clobberer.mozilla-releng.net',
    author='Rok Garbas',
    author_email='rgarbas@mozilla.com',
    url='https://clobberer.mozilla-releng.net',
    install_requires=[
        "relengapi_common",
        "taskcluster",
    ],
    extras_require={
    },
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            'relengapi = relengapi.cmd:main',
        ],
    },
    license='MPL2',
)
