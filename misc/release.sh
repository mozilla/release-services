#! /bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -e

_ESC=$'\e'
GREEN="$_ESC[0;32m"
MAGENTA="$_ESC[0;35m"
RED="$_ESC[0;31m"
LTCYAN="$_ESC[1;36m"
YELLOW="$_ESC[1;33m"
NORM="$_ESC[0;0m"

fail() {
    echo "${RED}${@}${NORM}"
    exit 1
}

status() {
    echo "${LTCYAN}-- ${*} --${NORM}"
}

message() {
    echo "${MAGENTA} ${*}${NORM}"
}

usage() {
    fail "USAGE: misc/release.sh newversion"
}

[ $# = 1 ] || usage
[ -f misc/release.sh ] || usage
newversion="${1}"
[ -z "$VIRTUAL_ENV" ] && fail "Need an activated virtualenv with relengapi installed"

status "getting information from setup.py"

# monkey-patch setuptools.setup to just print a few args in shell format
setup_info=`python <<'EOF'
import setuptools
from pipes import quote  # replace with shlex.quote in python3
def setup(name, version, **kwargs):
    print "name={}".format(quote(name))
    print "oldversion='{}'".format(quote(version))
setuptools.setup = setup
import setup
EOF`
eval $setup_info

message "$name-$oldversion -> $name-$newversion"

status "creating release notes"

relnote_file="docs/relnotes/${newversion}.rst"
if [ -f "${relnote_file}" ]; then
    message "(${relnote_file} already exists)"
else
    sed -i $'/\.\. toctree::/a \\\n    '"${newversion}" docs/relnotes/index.rst
    git add docs/relnotes/index.rst

    (
        echo "$name-$newversion"
        echo "$name-$newversion" | tr -c $'\n' '='
        echo ""
        echo "* thing that changed"
        echo ""
        echo "* thing that changed"
        echo ""
        echo ".. todo::"
        echo ""
        echo "    Summarize the changes since $oldversion; below is the shortlog of merges,"
        echo "    or see https://github.com/mozilla/build-${name}/compare/${name}-${oldversion}...master"
        echo ""
        git shortlog --merges ${name}-${oldversion}..
    ) > ${relnote_file}
fi

${EDITOR:-vim} ${relnote_file}
git add ${relnote_file}

status "building docs to verify"

if ! relengapi build-docs --development; then
    message "If the error was in the new release notes, re-run this script to try again"
    fail "building docs failed"
fi

status "updating version in setup.py"

sed -i "s/version=['\"][^']*['\"],/version='$newversion',/" setup.py
git diff --quiet setup.py && fail "no change to setup.py?"
git add setup.py

status "committing and tagging"

git commit -m "Bump to version $name-$newversion"
git tag $name-$newversion
git log -1 --decorate $name-$newversion

status "building sdist"

python setup.py sdist

message "if everything looks OK,"
message " - git push --tags upstream"
message " - twine upload dist/$name-$newversion.tar.gz"
message " - deploy dist/$name-$newversion.tar.gz to production"
