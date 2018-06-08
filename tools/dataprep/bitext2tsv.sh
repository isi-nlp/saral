#!/usr/bin/env bash

while read f; do
    docid=$(echo $f| sed 's/.*_\([0-9]\+\)\..*/\1/g' )
    cat $f | sed 's/^<\([^>]\+\)>/\1/' | awk -F '\t' -v OFS='\t' -v docid=$docid 'NF > 1 {$1=docid"_"$1; print}'
done
