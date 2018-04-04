# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import functools
import setuptools


with open('VERSION') as f:
    version = f.read().strip()


def read_requirements(file_):
    lines = []
    with open(file_) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('-e '):
                lines.append(line.split('#')[1].split('egg=')[1])
            elif line.startswith('#') or line.startswith('-'):
                pass
            else:
                lines.append(line)
    return lines


EXTRAS = dict(
    log=['logbook'],
    api=['connexion'],
    auth0=['flask-oidc', 'python-jose'],
    auth=['Flask-Login', 'taskcluster<2.0.0'],
    cache=['Flask-Cache'],
    cors=['Flask-Cors'],
    db=['Flask-SQLAlchemy', 'Flask-Migrate'],
    pulse=['kombu'],
    templates=['Jinja2'],
    security=['flask-talisman'],
    testing=['pytest', 'responses'],
    linting=[
        'flake8',
        'flake8-coding',
        'flake8-quotes',
    ],
    develop=[
        'pdbpp',
        'inotify',  # needed by gunicorn for faster/better reload
    ],
)
EXTRAS['all'] = functools.reduce(lambda x, y: x + y, EXTRAS.values())


setuptools.setup(
    name='mozilla-backend-common',
    version=version,
    description='Services behind https://mozilla-releng.net',
    author='Mozilla Release Engineering',
    author_email='release@mozilla.com',
    url='https://github.com/garbas/mozilla-releng',
    install_requires=read_requirements('requirements.txt'),
    tests_require=EXTRAS['all'],
    extras_require=EXTRAS,
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
    entry_points={
        'pytest11': [
            'backend_common = backend_common.testing',
        ]
    },
)
