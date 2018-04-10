# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
import json
import re

import setuptools


def join_requirements(list1, list2):
    packages = dict()

    for package in (list1 + list2):
        package_extra = []
        if '[' in package:
            package_extra += re.search('(?<=\[)[^]]+(?=\])', package).group().split(',')
            package = re.sub('(?<=\[)[^]]+(?=\])', '', package).replace('[]', '')
        packages.setdefault(package, [])
        packages[package] += package_extra

    joined = []
    for package, package_extra in packages.items():
        package_extra = ','.join(list(set(package_extra)))
        if package_extra:
            package_extra = '[{}]'.format(package_extra)
        joined.append(package + package_extra)

    return list(set(joined))


def read_requirements(file_):
    lines = []
    with open(file_) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('-e ') or line.startswith('http://') or line.startswith('https://'):
                extras = ''
                if '[' in line:
                    extras = '[' + line.split('[')[1].split(']')[0] + ']'
                line = line.split('#')[1].split('egg=')[1] + extras
            elif line == '' or line.startswith('#') or line.startswith('-'):
                continue
            line = line.split('#')[0].strip()
            lines.append(line)
    return sorted(list(set(lines)))


with open('VERSION') as f:
    VERSION = f.read().strip()

with open('requirements-extra.json') as f:
    EXTRAS = json.load(f)


setuptools.setup(
    name='mozilla-cli-common',
    version=VERSION,
    description='Services behind https://mozilla-releng.net',
    author='Mozilla Release Engineering',
    author_email='release@mozilla.com',
    url='https://github.com/mozilla-releng/services',
    tests_require=join_requirements(
        functools.reduce(lambda x, y: x + y, EXTRAS.values()),
        read_requirements('requirements-dev.txt'),
    ),
    extras_require=EXTRAS,
    install_requires=read_requirements('requirements.txt'),
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
