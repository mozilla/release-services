#!/bin/bash
TEST_BASE_URL='http://localhost:8080/'
PASSCOUNT=0
FAILCOUNT=0
echo testing tooltool\'s command line interface

function fail() {
    echo TEST-FAIL: "$@"
    FAILCOUNT=$((FAILCOUNT + 1))
}

function pass() {
    echo TEST-PASS: "$@"
    PASSCOUNT=$((PASSCOUNT + 1))
}

function error() {
    echo TEST-ERROR: "$@"
}

function info() {
    echo TEST-INFO: "$@"
}

function setup() {
    #cleanup
    rm -rf manifest.tt a b c d test_file.ogg
    echo 1 > a
    echo 2 > b
    echo 3 > c
    echo 4 > d
}

function assert_zero() {
    if [ $1 -ne 0 ] ; then
        fail "$2"
    else
        pass "$2"
    fi
}

function assert_nonzero() {
    if [ $1 -eq 0 ] ; then
        fail "$2"
    else
        pass "$2"
    fi
}

mkdir -p testdir && cd testdir
tt="../tooltool.py --url $TEST_BASE_URL -v"
info "$tt"
###############
setup
$tt list
assert_nonzero $? "listing empty manifest"
###############
setup
$tt add a
assert_zero $? "adding file to manifest"
test -f manifest.tt
assert_zero $? "manifest file created"
###############
$tt add a
# TODO assert_nonzero $? "adding the same file a second time"
###############
$tt add notafile
#TODO this will always pass until the program is fixed
assert_nonzero $? "adding non-existant file"
###############
$tt list
assert_zero $? "listing valid manifest"
###############
rm a
$tt list
assert_zero $? "listing should work when there are absent files"
###############
$tt add b
assert_zero $? "adding a second file"
###############
$tt add b
assert_nonzero $? "adding a duplicate file shouldn't work"
###############
curl -LI $TEST_BASE_URL &> /dev/null
assert_zero $? "need a webserver, trying $TEST_BASE_URL"
###############
rm -f a b
$tt fetch a
assert_zero $? "fetching a single file"
echo 1 > ta
diff a ta &> /dev/null
assert_zero $? "a fetched correctly"
rm -f ta
test ! -e b
assert_zero $? "un-fetched file should be absent"
##############
$tt fetch
assert_zero $? "fetching all files in manifest"
test -f a
assert_zero $? "a fetched"
test -f b
assert_zero $? "b fetched"
##############
echo OMGWTFBBQ > a
$tt fetch a
assert_nonzero $? "without overwriting, shouldn't overwrite"
test `cat a` = "OMGWTFBBQ\n" # hmm, feels flakey
assert_nonzero $? "contents should be per local changes"
$tt fetch a --overwrite
assert_zero $? "with overwriting, should overwrite"
test `cat a` -eq 1
assert_zero $? "contents should be per manifest"
#############
$tt validate
assert_zero $? "validate works"








echo ==============================================
echo TEST-PASSES: $PASSCOUNT, TEST-FAILS: $FAILCOUNT
if [[ $FAILCOUNT -ne 0 || $PASSCOUNT -lt 1 ]] ; then
    echo TESTS FAILED
    exit 1
else
    (cd .. && rm -rf testdir)
    exit 0
fi
