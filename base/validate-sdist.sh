# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -e

# some colors
# plain
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

[ -z "$VIRTUAL_ENV" ] && fail "Need an activated virtualenv with relengapi installed"
# find out where relengapi is installed and go there
base=`python -c 'import pkg_resources; print pkg_resources.require("'relengapi'")[0].location'`
cd $base

tmpbase=$(mktemp -d)
trap 'rm -f ${tmpbase}; exit 1' 1 2 3 15

# get the version
version=`python -c 'import pkg_resources; print pkg_resources.require("'relengapi'")[0].version'`

# get the list of files git thinks should be present
git ls-files . | sort > ${tmpbase}/git-files

# get the list of files in an sdist tarball
python setup.py -q sdist --dist-dir=${tmpbase}
tarball="${tmpbase}/relengapi-${version}.tar.gz"
[ -f ${tarball} ] || fail "No tarball at ${tarball}"
# exclude directories and a few auto-generated files from the tarball contents
tar -ztf $tarball | grep -v  '/$' | cut -d/ -f 2- | grep -vE '(egg-info|PKG-INFO|setup.cfg)' | sort > ${tmpbase}/sdist-files

# get the list of files *installed* from that tarball
(
    cd "${tmpbase}"
    tar -zxf ${tarball}
    cd `basename ${tarball%.tar.gz}`
    python setup.py -q install --root $tmpbase/root --record=installed.txt
    # get everything installed under site-packages, and trim up to and including site-packages/ on each line,
    # excluding .pyc files, and including the two namespaced packages
    grep 'site-packages/relengapi/' installed.txt | grep -v '\.pyc$' | sed -e 's!.*/site-packages/!!' | sort > ${tmpbase}/install-files
)

# and calculate the list of git files that we expect to see installed:
# anything not at the top level, but not the namespaced __init__.py's
grep / ${tmpbase}/git-files | grep -Ev '^relengapi/(blueprints/|)__init__\.py$' > ${tmpbase}/git-expected-installed

# start comparing!
cd ${tmpbase}
diff -u git-files sdist-files || fail "sdist files differ from files in git"
diff -u git-expected-installed install-files || fail "installed files differ from files in git"
