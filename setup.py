#!/usr/bin/env python

import os
from setuptools import setup, find_packages

setup(name='relengapi-skel',
    version='0.2.0.1',
    description='Skeleton of a RelengAPI project',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='https://github.com/djmitche/relengapi-skel',
    packages=find_packages(),
    namespace_packages=['relengapi', 'relengapi.blueprints'],
    entry_points={
        "relengapi_blueprints": [
            'mapper = relengapi.blueprints.skel:bp',
        ],
    },
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
            'mock'
        ]
    })
