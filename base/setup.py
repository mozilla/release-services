# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages

setup(
    name='relengapi',
    version='0.1.5',
    description='The code behind https://api.pub.build.mozilla.org',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='https://api.pub.build.mozilla.org',
    install_requires=[
        "Flask",
        "Flask-Login>=0.2.10",
        "Flask-Browserid",
        "Flask-Principal",
        "SQLAlchemy",
        "Celery",
        "argparse",
        "requests",
    ],
    extras_require = {
        'test': [
            'nose',
            'mock'
        ]
    },
    packages=find_packages(),
    include_package_data=True,
    namespace_packages=['relengapi', 'relengapi.blueprints'],
    package_data={  # NOTE: these files must *also* be specified in MANIFEST.in
        'relengapi': [
            'templates/*.html',
            'static/*.jpg',
            'static/*.css',
            'static/js/ext/*.css',
            'static/js/ext/*.js',
        ],
        'relengapi.blueprints.base': [
            'templates/*.html',
        ],
        'relengapi.blueprints.auth': [
            'templates/*.html',
        ],
        'relengapi.blueprints.authz': [
            'templates/*.html',
        ],
        'relengapi.blueprints.userauth': [
            'templates/*.html',
        ],
        'relengapi.blueprints.tokenauth': [
            'static/*.js',
            'templates/*.html',
        ],
    },
    entry_points={
        "relengapi_blueprints": [
            'base = relengapi.blueprints.base:bp',
            'auth = relengapi.blueprints.auth:bp',
            'authz = relengapi.blueprints.authz:bp',
            'userauth = relengapi.blueprints.userauth:bp',
            'tokenauth = relengapi.blueprints.tokenauth:bp',
        ],
        "console_scripts": [
            'relengapi = relengapi.subcommands:main',
        ],
    },
    license='MPL2',
)
