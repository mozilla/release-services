# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from setuptools import setup, find_packages

data_patterns = [
    'templates/**.html',
    'static/**.jpg',
    'static/**.css',
    'static/**.js',
    'static/**.txt',
]

DOCS_DIRS = ['usage', 'developent', 'deployment']

setup(
    name='relengapi',
    version='0.2.1',
    description='The code behind https://api.pub.build.mozilla.org',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='https://api.pub.build.mozilla.org',
    install_requires=[
        "Flask",
        "Flask-Login>=0.2.10",
        "Flask-Browserid",
        "Sphinx",
        "SQLAlchemy>=0.9.4",
        "Celery",
        "argparse",
        "requests",
        "wrapt",
        "blinker",  # required to use flask signals
        #  Tests break with newer pytz,
        #  see https://bugs.launchpad.net/pytz/+bug/1324158
        "pytz==2014.1",
        "wsme",
    ],
    extras_require={
        'test': [
            'nose',
            'mock',
            'coverage',
            'pep8',
            # see
            # https://bitbucket.org/logilab/pylint/issue/203/importing-namespace-packages-crashes
            'pylint<1.2',
            'mockldap',
        ],
        # extras required only for LDAP authorization support
        'ldap': [
            'python-ldap',
        ],
    },
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    namespace_packages=['relengapi', 'relengapi.blueprints'],
    # copy ./docs to %(sys.prefix)s/relengapi-docs, recursively
    data_files=[
        ('relengapi-' + dirpath, [os.path.join(dirpath, f) for f in files])
        for dirpath, _, files in os.walk('docs')
    ],
    package_data={  # NOTE: these files must *also* be specified in MANIFEST.in
        'relengapi.blueprints.base': data_patterns,
        'relengapi.blueprints.auth': data_patterns,
        'relengapi.blueprints.tokenauth': data_patterns,
        'relengapi.blueprints.docs': data_patterns + [
            'base/**.rst',
            'base/_static/**',
            'base/conf.py',
        ],
    },
    entry_points={
        "relengapi_blueprints": [
            'base = relengapi.blueprints.base:bp',
            'auth = relengapi.blueprints.auth:bp',
            'tokenauth = relengapi.blueprints.tokenauth:bp',
            'docs = relengapi.blueprints.docs:bp',
        ],
        "relengapi.auth.mechanisms": [
            'browserid = relengapi.lib.auth.browserid:init_app',
            'external = relengapi.lib.auth.external:init_app',
        ],
        "relengapi.perms.mechanisms": [
            'static = relengapi.lib.auth.static_authz:init_app',
            'ldap-groups = relengapi.lib.auth.ldap_group_authz:init_app',
        ],
        "console_scripts": [
            'relengapi = relengapi.subcommands:main',
        ],
    },
    license='MPL2',
)
