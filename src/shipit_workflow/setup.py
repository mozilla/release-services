# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from setuptools import find_packages
from setuptools import setup

with open('VERSION') as f:
    version = f.read().strip()
description = '''
Release kick-off (ship-it) is a Mozilla "internal" tool used to start the
release of Firefox Desktop, Android and Thunderbird. This tool is specific to
Mozilla workflows and tools.
'''


def read_requirements(file_):
    lines = []
    with open(file_) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('-e ') or line.startswith('http://') or line.startswith('https://'):
                lines.append(line.split('#')[1].split('egg=')[1])
            elif line.startswith('#') or line.startswith('-'):
                pass
            else:
                lines.append(line)
    return lines


setup(
    name='mozilla-shipit-workflow',
    version=version,
    description=description,
    author='Mozilla Release Engineering',
    author_email='release@mozilla.com',
    url='https://treestatus.mozilla-releng.net',
    tests_require=read_requirements('requirements-dev.txt'),
    install_requires=read_requirements('requirements.txt'),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
