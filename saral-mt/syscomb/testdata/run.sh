#!/usr/bin/env bash

data=$PWD/testdata
python fallback.py -s $data/src.txt --hyp $data/hyp.txt -f $data/fallback.txt -t 0.4