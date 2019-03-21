#! /usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

## tweakable parameters

# minimum acceptable coverage percentage
COVERAGE_MIN=100

# project name
PROJECT=tooltool

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

#[ -z "$VIRTUAL_ENV" ] && fail "Need an activated virtualenv with tooltool[test] installed"

tmpbase=$(mktemp -d -t tmpbase.XXXXXX)
trap 'rm -rf ${tmpbase}; exit 1' 1 2 3 15

status "running pep8"
pep8 --config=pep8rc tooltool.py || not_ok "pep8 failed"

status "running pyflakes"
pyflakes tooltool.py || not_ok "pyflakes failed"

if [ ! -z "$IN_NIX_SHELL" ]; then
  status "running shell tests"
  bash test.sh >/dev/null 2>&1 || not_ok "shell tests failed"
fi

status "running tests (under coverage)"
coverage erase || not_ok "coverage failed"
coverage run --rcfile=coveragerc --source=tooltool `dirname \`which nosetests\``/.nosetests-wrapped test_tooltool.py || not_ok "tests failed"

status "checking coverage"
coverage report --rcfile=coveragerc --fail-under=${COVERAGE_MIN} >${tmpbase}/covreport || not_ok "less than ${COVERAGE_MIN}% coverage"
coverage html --rcfile=coveragerc -d .coverage-html
head -n2 ${tmpbase}/covreport
tail -n1 ${tmpbase}/covreport

show_results
