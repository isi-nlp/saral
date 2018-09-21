#/usr/bin/env bash
#this script converts a bunch of .txt files into .tsv file
# usage: ls *.txt | plain2tsv.sh > out.tsv
#
while read f;
do
    id=$(echo $f | sed 's/.*_\([0-9]\+\).txt$/\1/');
    cat $f | sed 's/^\s\+//;s/\s\+$//' | grep -v '^$' | awk -F '\n' -v id="$id" '{printf "%s_%s\t%s\n",id,NR,$0}' ;
done
