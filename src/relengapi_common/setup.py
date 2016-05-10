# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from setuptools import find_packages
from setuptools import setup

here = os.path.dirname(__file__)

setup(
    name='relengapi_common',
    version=open(os.path.join(here, 'VERSION')).read().strip(),
    description='Common code for all services behind '
                'https://mozilla-releng.net',
    author='Rok Garbas',
    author_email='rgarbas@mozilla.com',
    url='https://github.com/mozilla/build-relengapi',
    install_requires=[
        "Flask",
        "Flask-Browserid",
        "Flask-Login>=0.3.0",
        "blinker",  # required to use flask signals
        "structlog",
        "werkzeug",
        "wrapt",
        "wsme<0.8.0",  # https://github.com/mozilla/build-relengapi/issues/325
        "SQLAlchemy>=0.9.4",
    ],
    extras_require={
        'test': [
            'pytest',
         ],
        'ldap': [
            'python-ldap',
        ],
    },
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
