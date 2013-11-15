#!/bin/sh

while read line; do
    hg_sha=`echo $line | sed -e 's/ .*//'`
    git_sha=`echo $line | sed -e 's/.* //'`
    echo "insert into hashes values (NULL, '$hg_sha', '$git_sha', 3, unix_timestamp());"
done < ~/Desktop/combined_gecko_mapfile
