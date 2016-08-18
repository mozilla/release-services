# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

from setuptools import find_packages
from setuptools import setup

here = os.path.dirname(__file__)

with open(os.path.join(here, 'requirements.txt')) as f:
    install_requires = filter(
        lambda x: not x.startswith('-r'),
        map(
            lambda x: x.startswith('-e ../') and x[6:] or x,
            f.read().strip().split('\n')
        )
    )

# until clouseau gets properly packaged
# https://github.com/calixteman/clouseau/pull/68
install_requires = [i for i in install_requires] + ['clouseau']

setup(
    name='shipit_dashboard',
    version=open(os.path.join(here, 'VERSION')).read().strip(),
    description='The code behind https://dashboard.shipit.mozilla-releng.net',
    author='Mozilla Release Engineering',
    author_email='release@mozilla.com',
    url='https://dashboard.shipit.mozilla-releng.net',
    install_requires=install_requires,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
