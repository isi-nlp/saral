#!/usr/bin/env bash

corenlp-ssplit.scala | sed 's/^[^:]\+_\([0-9]\+\)\.[^_]*:\([0-9]\+\)/\1_\2/'
