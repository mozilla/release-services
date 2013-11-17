#!/bin/sh

while read line; do
    hg_sha=`echo $line | sed -e 's/ .*//'`
    git_sha=`echo $line | sed -e 's/.* //'`
    echo "insert into hashes values ('$hg_sha', '$git_sha', 3, unix_timestamp());"
done < ~/Desktop/project-branches-mapfile

while read line; do
    hg_sha=`echo $line | sed -e 's/ .*//'`
    git_sha=`echo $line | sed -e 's/.* //'`
    echo "insert into hashes values ('$hg_sha', '$git_sha', 2, unix_timestamp());"
done < ~/Desktop/gecko-mapfile
