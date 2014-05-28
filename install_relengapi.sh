#!/bin/bash -exv

git clone http://github.com/mozilla/build-relengapi
cd build-relengapi/base
python setup.py install
mv pep8rc ../..
mv pylintrc ../..
cd ../..
rm -rf build-relengapi
