#!/usr/bin/env bash

corenlp-ssplit.scala |  sed 's/^[^[:space:]]\+_\([0-9]\+\)[^[:space:]0-9]\+:\([0-9\.]\+\)\t/\1_\2\t/' 

