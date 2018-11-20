# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import setuptools


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

DESCRIPTION = '''
Release kick-off (ship-it) is a Mozilla "internal" tool used to start the
release of Firefox Desktop, Android and Thunderbird. This tool is specific to
Mozilla workflows and tools.
'''

setuptools.setup(
    name='mozilla-shipit-api',
    version=VERSION,
    description=DESCRIPTION,
    author='Mozilla Release Services Team',
    author_email='release-services@mozilla.com',
    url='https://api.shipit.mozilla-releng.net',
    tests_require=read_requirements('requirements-dev.txt'),
    install_requires=read_requirements('requirements.txt'),
    packages=setuptools.find_packages(),
    entry_points=dict(
        console_scripts=[
            'shipit-v1-sync = shipit_api.cli:v1_sync',
            'shipit-download-product-details = shipit_api.cli:download_product_details',
            'shipit-rebuild-product-details = shipit_api.cli:rebuild_product_details',
        ],
    ),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
