#!/usr/bin/env python

import os
from setuptools import setup, find_packages

data_patterns = [
    'templates/**.html',
    'static/**.jpg',
    'static/**.css',
    'static/**.js',
    'static/**.txt',
]

setup(name='relengapi-skeleton',
    version='0.1.0',
    description='Skeleton of a RelengAPI project',
    author='Skeleton Crew',
    author_email='skeleton@mozilla.com',
    url='https://github.com/buildbot/build-relengapi-skeleton',
    entry_points={
        "relengapi_blueprints": [
            'mapper = relengapi.blueprints.skeleton:bp',
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
        'relengapi.blueprints.skeleton': data_patterns,
    },
    install_requires=[
        'Flask',
        'relengapi>=0.3',
    ],
    license='MPL2',
    extras_require={
        'test': [
            'nose',
            'mock',
            'pep8',
            'pyflakes',
            'coverage',
        ]
    })
