#!/usr/bin/env python

from setuptools import setup

setup(name='mapper',
      version='0.2',
      description='hg to git mapper',
      author='Chris AtLee',
      author_email='chris@atlee.ca',
      url='https://github.com/catlee/mapper',
      packages=['mapper'],
      install_requires=['bottle', 'bottle_mysql', 'MySQL-python'],
      license='MPL2',
      )
