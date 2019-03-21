#!/usr/bin/env python

from setuptools import setup

data_patterns = [
    'templates/**.html',
    'static/**.jpg',
    'static/**.html',
    'static/**.css',
    'static/**.js',
    'static/**.txt',
]

setup(name='tooltool',
      version='1.3.0',
      description='Secure, cache-friendly access to large binary blobs for builds and tests',
      author='John Ford',
      author_email='jhford@mozilla.com',
      url='https://git.mozilla.org/?p=build/tooltool.git',
      py_modules=['tooltool'],
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
