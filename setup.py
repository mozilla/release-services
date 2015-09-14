# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from setuptools import find_packages
from setuptools import setup

setup(
    name='relengapi',
    version='3.3.0',
    description='The code behind https://api.pub.build.mozilla.org',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='https://api.pub.build.mozilla.org',
    install_requires=[
        "Flask",
        "Flask-Login>=0.3.0",
        "Flask-Browserid",
        "Sphinx>=1.3",
        "SQLAlchemy>=0.9.4",
        "Celery>=3.1.16",  # see https://github.com/mozilla/build-relengapi/issues/145
        "alembic>=0.7.0",
        "argparse",
        "requests",
        "wrapt",
        "blinker",  # required to use flask signals
        "pytz",
        "wsme<0.8",  # see https://github.com/mozilla/build-relengapi/issues/325
        "croniter",
        "python-dateutil",
        "simplejson",
        "boto",
        "python-memcached",
        "elasticache-auto-discovery",
        "IPy",
        "furl",
        "redo",
        # Temporary freeze until https://github.com/bhearsum/bzrest/pull/3 is fixed
        "bzrest==0.9",
        "structlog",
        "mozdef_client",
        "requests_futures",
    ],
    extras_require={
        'test': [
            'nose',
            'mock',
            'coverage',
            'pep8',
            'mockldap',
            'pyflakes',
            'moto',
            'mockcache',
            'isort',
        ],
        # extras required only for LDAP authorization support
        'ldap': [
            'python-ldap',
        ],
    },
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    package_data={  # NOTE: these files must *also* be specified in MANIFEST.in
        'relengapi': [
            'docs/**.rst',
            'docs/**.py',
            'docs/**.css',
        ],
        'relengapi.blueprints': [
            '*/templates/**.html',
            '*/static/**.jpg',
            '*/static/**.css',
            '*/static/**.js',
            '*/static/**.map',
            '*/static/**.txt',
            '*/static/**.eot',
            '*/static/**.svg',
            '*/static/**.ttf',
            '*/static/**.woff',
        ],
        'relengapi.alembic': [
            '*.ini',
            '*.py',
            '*.mako',
        ],
    },
    entry_points={
        "console_scripts": [
            'relengapi = relengapi.cmd:main',
        ],
    },
    license='MPL2',
)
