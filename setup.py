#!/usr/bin/env python

import os
from setuptools import setup, find_packages

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
    ],
    package_data={
        'relengapi': ['docs/**.rst'],
    },
    install_requires=[
        'Flask',
        'relengapi',
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
