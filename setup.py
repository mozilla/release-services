#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from setuptools import setup, find_packages

data_patterns = [
    'templates/**.html',
    'static/**.html',
    'static/**.jpg',
    'static/**.css',
    'static/**.js',
    'static/**.txt',
]

setup(
    name='relengapi-slaveloan',
    version='0.1.3',
    description='Slave Loan blueprint for RelengAPI',
    author='Justin Wood',
    author_email='callek@mozilla.com',
    url='https://github.com/mozilla/build-relengapi-slaveloan',
    entry_points={
        "relengapi.blueprints": [
            'slaveloan = relengapi.blueprints.slaveloan:bp',
        ],
        "relengapi.metadata": [
            'relengapi-slaveloan = relengapi.blueprints.slaveloan.metadata:data',
        ],
    },
    packages=find_packages(),
    namespace_packages=['relengapi', 'relengapi.blueprints'],
    data_files=[
        ('relengapi-' + dirpath, [os.path.join(dirpath, f) for f in files])
        for dirpath, _, files in os.walk('docs')
        # don't include directories not containing any files, as they will be
        # included in installed-files.txt, and deleted (rm -rf) on uninstall;
        # see https://bugzilla.mozilla.org/show_bug.cgi?id=1088676
        if files
    ],
    package_data={  # NOTE: these files must *also* be specified in MANIFEST.in
        'relengapi.blueprints.slaveloan': data_patterns + [
            'docs/**.rst'
        ],
    },
    include_package_data=True,
    license='MPL2',
    install_requires=[
        "Flask",
        "furl",
        "relengapi>=0.3",
        "redo",
        # Temporary freeze until https://github.com/bhearsum/bzrest/pull/3 is fixed
        "bzrest==0.9",
    ],
    extras_require={
        'test': [
            'nose',
            'mock',
            'pep8',
            'pyflakes',
            'coverage',
        ]
    },
)
