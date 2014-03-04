# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages

setup(
    name='relengapi-docs',
    version='0.0',
    description='Documentation blueprint for relengapi',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='',
    install_requires=[
        "Flask",
        "relengapi",
        "Sphinx",
    ],
    tests_require=["nose", "mock"],
    packages=find_packages(),
    include_package_data=True,
    test_suite='nose.collector',
    namespace_packages=['relengapi', 'relengapi.blueprints'],
    entry_points={
        "relengapi_blueprints": [
            'docs = relengapi.blueprints.docs:bp',
        ],
    },
)
