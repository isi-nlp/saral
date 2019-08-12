#!/usr/bin/env bash
# sentence split, followed by tokenization followed by force split to 80 tokens

DIR=$(dirname "${BASH_SOURCE[0]}")  # get the directory name
DIR=$(realpath "${DIR}")

tmp_file=$(mktemp --suffix .tsv)
$DIR/corenlp-ssplit.scala -tsv > $tmp_file
$DIR/ulftok-tsv.sh $tmp_file  # this script takes .tsv file and makes .tok.tsv

tmp_tok_file=${tmp_file/.tsv/.tok.tsv}
$DIR/ssplit-tsv-len.py -l 80 -i $tmp_tok_file

rm $tmp_file $tmp_tok_file
