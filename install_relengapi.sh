#!/bin/bash -exv

git clone http://github.com/mozilla/build-relengapi
cd build-relengapi
pip install -e base[test] -e docs[test]
