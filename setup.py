#!/usr/bin/env python

import os

from setuptools import find_packages
from setuptools import setup

data_patterns = [
    'templates/**.html',
    'static/**.jpg',
    'static/**.html',
    'static/**.css',
    'static/**.js',
    'static/**.txt',
]

setup(name='relengapi-tooltool',
      version='1.0.0',
      description='Secure, cache-friendly access to large binary blobs for builds and tests',
      author='John Ford',
      author_email='jhford@mozilla.com',
      url='https://git.mozilla.org/?p=build/tooltool.git',
      entry_points={
          "relengapi_blueprints": [
              'mapper = relengapi.blueprints.tooltool:bp',
          ],
          "relengapi.metadata": [
              'relengapi-tooltool = relengapi.blueprints.tooltool:metadata',
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
          'relengapi.blueprints.tooltool': data_patterns,
      },
      install_requires=[
          'Flask',
          'relengapi>=0.3',
          'relengapi>=1.1.1',
      ],
      license='MPL2',
      extras_require={
          'test': [
              'nose',
              'mock',
              'moto',
              'pep8',
              'pyflakes',
              'coverage',
          ]
      })
