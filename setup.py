#!/usr/bin/env python

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
