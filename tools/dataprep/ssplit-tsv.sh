#!/usr/bin/env bash

corenlp-ssplit.scala -tsv | ssplit-tsv-len.py -l 80
