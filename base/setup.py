# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages

data_patterns = [
    'templates/**.html',
    'static/**.jpg',
    'static/**.css',
    'static/**.js',
    'static/**.txt',
]

setup(
    name='relengapi',
    version='0.1.8',
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
        "wrapt",
    ],
    extras_require = {
        'test': [
            'nose',
            'mock',
            'pep8',
            # see https://bitbucket.org/logilab/pylint/issue/203/importing-namespace-packages-crashes
            'pylint<1.2',
        ]
    },
    packages=find_packages(),
    include_package_data=True,
    namespace_packages=['relengapi', 'relengapi.blueprints'],
    package_data={  # NOTE: these files must *also* be specified in MANIFEST.in
        'relengapi': data_patterns,
        'relengapi.blueprints.base': data_patterns,
        'relengapi.blueprints.auth': data_patterns,
        'relengapi.blueprints.authz': data_patterns,
        'relengapi.blueprints.userauth': data_patterns,
        'relengapi.blueprints.tokenauth': data_patterns,
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
