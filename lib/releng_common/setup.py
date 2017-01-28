# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from setuptools import find_packages, setup


here = os.path.dirname(__file__)

with open(os.path.join(here, 'VERSION')) as f:
    version = f.read().strip()

setup(
    name='releng_common',
    version=version,
    description='Services behind https://mozilla-releng.net',
    author='Mozilla Release Engineering',
    author_email='release@mozilla.com',
    url='https://github.com/garbas/mozilla-releng',
    tests_require=[
        'flake8',
        'pytest',
        'responses',
    ],
    install_requires=[
        'Flask',
        'Jinja2',
        'gunicorn',
        'newrelic',
    ],
    extras_require=dict(
        cache=['Flask-Cache'],
        db=['psycopg2', 'Flask-SQLAlchemy', 'Flask-Migrate'],
        auth=['Flask-Login', 'taskcluster'],
        api=['connexion<1.1.0'],
        log=['structlog', 'Logbook'],
        cors=['Flask-Cors'],
        security=['flask-talisman'],
    ),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
