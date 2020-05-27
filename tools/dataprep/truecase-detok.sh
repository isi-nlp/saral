#!/usr/bin/env bash

detokr=$MOSES/scripts/tokenizer/detokenizer.perl
[[ -f $detokr ]] || { echo "Cant find MOSES; please export MOSES=/path"; exit 1; }
corenlp-truecase.scala 2> /dev/null | $detokr -l en -penn -q
