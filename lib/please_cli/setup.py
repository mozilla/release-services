# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from setuptools import find_packages
from setuptools import setup

here = os.path.dirname(__file__)

with open(os.path.join(here, 'please_cli', 'VERSION')) as f:
    version = f.read().strip()


def read_requirements(file_):
    lines = []
    with open(file_) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('-e ') or line.startswith('http'):
                lines.append(line.split('#')[1].split('egg=')[1])
            elif line.startswith('#') or line.startswith('-') or line == "":
                pass
            else:
                lines.append(line)
    return lines


setup(
    name='please-cli',
    version=version,
    description='Helper utilities for mozilla-releng/services',
    author='Mozilla Release Management',
    author_email='release-mgmt@mozilla.com',
    url='https://docs.mozilla-releng.net',
    tests_require=read_requirements('requirements-dev.txt'),
    install_requires=read_requirements('requirements.txt'),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
    entry_points={
        'console_scripts': [
            'please = please_cli:cmd',
        ]
    },
)
