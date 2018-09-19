#!/usr/bin/env bash

# use this script to convert a bunch of plain text files to TSVs. 
#  1. run coreNLP sentence splitter. this outputs filename.txt:line_number \t sentences
#  2. convert ugly looking file name to a neat docID_seg_ID using sed
#  3. If there are any longer sequences than 80 words, split them

corenlp-ssplit.scala | \
   sed 's/^[^[:space:]]\+_\([0-9]\+\)[^[:space:]0-9]\+:\([0-9\.]\+\)\t/\1_\2\t/' | \
   ssplit-tsv-len.py -l 80 

