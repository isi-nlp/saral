#!/usr/bin/env bash

while read f; do
    docid=$(echo $f| sed 's/.*_\([0-9]\+\)\..*/\1/g' )
    cat $f | sed 's/^<\([^>]\+\)>/\1/' | awk -F '\t' -v docid=$docid 'NF ==3 {printf "%s_%s\t%s\t%s\n", docid,$1,$2,$3}'
done
