#! /bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

## tweakable parameters

# minimum acceptable coverage percentage
COVERAGE_MIN=96

# project name
PROJECT=relengapi-tooltool

# unset RELENGAPI_SETTINGS, if it's set
RELENGAPI_SETTINGS=

set -e

# some colors

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

ok=true
problem_summary=""

not_ok() {
    ok=false
    echo "${RED}** ${*} **${NORM}"
    problem_summary="$problem_summary"$'\n'"${RED}**${NORM} ${*}"
}

warning() {
    echo "${YELLOW}** ${*} **${NORM}"
    problem_summary="$problem_summary"$'\n'"${YELLOW}**${NORM} ${*} (warning)"
}

show_results() {
    echo ""
    if $ok; then
        if [ -z "${problem_summary}" ]; then
            echo "${GREEN}GOOD!${NORM}"
        else
            echo "${YELLOW}WARNINGS${NORM}${problem_summary}"
        fi
    else
        echo "${RED}NO GOOD!${NORM}${problem_summary}"
        return 1
    fi
}

cd "$( dirname "${BASH_SOURCE[0]}" )"

[ -z "$VIRTUAL_ENV" ] && fail "Need an activated virtualenv with relengapi installed"

tmpbase=$(mktemp -d -t tmpbase.XXXXXX)
trap 'rm -rf ${tmpbase}; exit 1' 1 2 3 15

status "running pep8"
pep8 --config=pep8rc relengapi tooltool.py || not_ok "pep8 failed"

status "running pyflakes"
pyflakes relengapi tooltool.py || not_ok "pyflakes failed"

status "checking import module convention in modified files"
modified=false
for filename in `find relengapi -type f -name "*.py" -print` ; do
    rv=0
    python misc/fiximports.py "$filename" || rv=$?
    case $rv in
        0) ;;
        1) not_ok "cannot fix imports of $filename" ;;
        2) modified=true ;;
    esac
done
$modified && not_ok "some imports were re-ordered and changes will need to be committed"

status "running shell tests"
bash test.sh >/dev/null 2>&1 || not_ok "shell tests failed"

status "running client tests"
python test_tooltool.py >/dev/null 2>&1 || not_ok "client tests failed"

status "building docs"
relengapi build-docs --development || not_ok "build-docs failed"

status "running tests (under coverage)"
coverage erase || not_ok "coverage failed"
# NOTE: to add coverage of the client (currently terrible!), use --source=relengapi,tooltool
coverage run --rcfile=coveragerc --source=relengapi $(which relengapi) run-tests || not_ok "tests failed"

status "checking coverage"
coverage report --rcfile=coveragerc --fail-under=${COVERAGE_MIN} >${tmpbase}/covreport || not_ok "less than ${COVERAGE_MIN}% coverage"
coverage html --rcfile=coveragerc -d .coverage-html
head -n2 ${tmpbase}/covreport
tail -n1 ${tmpbase}/covreport

# get the version
version=`python -c 'import pkg_resources; print pkg_resources.require("'${PROJECT}'")[0].version'`

# remove SOURCES.txt, as it caches the expected contents of the package,
# over and above those specified in setup.py, MANIFEST, and MANIFEST.in
rm -f "*.egg-info/SOURCES.txt"

# get the list of files git thinks should be present
status "getting file list from git"
git_only='
    .gitignore
    .travis.yml
    pep8rc
    coveragerc
    validate.sh
    misc/fiximports.py
'
git ls-files . | while read f; do
                    ignore=false
                    for go in $git_only; do
                        [ "$go" = "$f" ] && ignore=true
                    done
                    $ignore || echo $f
                 done | sort > ${tmpbase}/git-files

# get the list of files in an sdist tarball
status "getting file list from sdist"
python setup.py -q sdist --dist-dir=${tmpbase}
tarball="${tmpbase}/${PROJECT}-${version}.tar.gz"
[ -f ${tarball} ] || fail "No tarball at ${tarball}"
# exclude directories and a few auto-generated files from the tarball contents
tar -ztf $tarball | grep -v  '/$' | cut -d/ -f 2- | grep -vE '(egg-info|PKG-INFO|setup.cfg)' | sort > ${tmpbase}/sdist-files

# get the list of files *installed* from that tarball
status "getting file list from install"
(
    cd "${tmpbase}"
    tar -zxf ${tarball}
    cd `basename ${tarball%.tar.gz}`
    python setup.py -q install --root $tmpbase/root --record=installed.txt

    # sometimes setuptools includes directories here, so filter those out
    cat installed.txt | while read f; do
        [ -f "$tmpbase/root/$f" ] && echo $f
    done > installed.txt~
    mv installed.txt~ installed.txt

    (
        # get everything installed under site-packages, and trim up to and including site-packages/ on each line,
        # excluding .pyc files
        grep "site-packages/relengapi/" installed.txt | grep -v '\.pyc$' | sed -e 's!.*/site-packages/!!'
        # get all installed $prefix/relengapi-docs
        grep '/relengapi-docs/' installed.txt | sed -e 's!.*/relengapi-docs/!docs/!'
    ) | sort > ${tmpbase}/install-files
)

# and calculate the list of git files that we expect to see installed:
# anything not at the top level, but not the namespaced __init__.py's
grep / ${tmpbase}/git-files | grep -Ev '^relengapi/(blueprints/|)__init__\.py$' > ${tmpbase}/git-expected-installed

# start comparing!
pushd ${tmpbase}
status "comparing git and sdist"
diff -u git-files sdist-files || not_ok "sdist files differ from files in git"
status "comparing git and install"
diff -u git-expected-installed install-files || not_ok "installed files differ from files in git"
popd >/dev/null

# This part only applies for the skel.eton project itself -- it
# attempts to follow the instructions for creating a new blueprint.  Other
# blueprints should just leave it here, unused, to reduce merge conflicts.  The
# use of [s] here prevents the global sed operation from modifying the word in
# this conditional.
if [[ "${PROJECT}" =~ relengapi-[s]keleton ]]; then
    srcdir=$PWD
    status "testing creation of a new blueprint"
    cp -r . ${tmpbase}/bubbler
    cd ${tmpbase}/bubbler
    find * -name '*tooltool*' | while read s; do d=$(echo $s | sed s/tooltool/bubbler/g); mv $s $d; done
    git grep tooltool | cut -d: -f 1 | sort -u | while read s; do sed s/tooltool/bubbler/ < $s > $s~; mv $s~ $s; done
    {
        virtualenv skeltest --no-site-packages &&
        skeltest/bin/pip install -e .[test] &&
        skeltest/bin/relengapi run-tests &&
        skeltest/bin/relengapi build-docs --development
    } || not_ok "creation of a new blueprint from tooltool failed"
    cd ${srcdir}
    rm -rf ${tmpbase}/bubbler

    status "testing installs and uninstalls"
    # this is a regression test for https://github.com/mozilla/build-relengapi-tooltool/pull/3
    mkdir ${tmpbase}/skeltest
    cd ${tmpbase}/skeltest
    {
        virtualenv ${tmpbase}/skeltest --no-site-packages &&
        ${tmpbase}/skeltest/bin/pip install relengapi[test] &&
        ${tmpbase}/skeltest/bin/pip install ${srcdir} &&
        ${tmpbase}/skeltest/bin/pip uninstall -y relengapi-tooltool &&
        ${tmpbase}/skeltest/bin/relengapi run-tests &&
        ${tmpbase}/skeltest/bin/relengapi build-docs
    } || not_ok "install/uninstall test failed"
    cd ${srcdir}
    rm -rf ${tmpbase}/skeltest
fi

show_results
