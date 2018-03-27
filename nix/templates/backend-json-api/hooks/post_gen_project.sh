#!/usr/bin/env bash

silent() {
  out=`$@ 2>&1` || echo $out
}

ln -s ../../nix/requirements_override.nix ./
ln -s ../../nix/setup.cfg ./

echo "=> Pinning exact dependencies of a project (this might take few minutes) ..."
silent nix-build ../../nix/default.nix -A tools.pypi2nix -o ../../tmp/result-pypi2nix
silent ../../tmp/result-pypi2nix/bin/pypi2nix -v -V 3.5 -E postgresql -r requirements.txt -r requirements-dev.txt
