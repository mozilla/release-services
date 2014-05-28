#!/bin/bash -exv

git clone http://github.com/mozilla/build-relengapi
cd build-relengapi
pip install base[test]
cd ..
mv build-relengapi/base/pep8rc .
mv build-relengapi/base/pylintrc .
rm -rf build-relengapi
