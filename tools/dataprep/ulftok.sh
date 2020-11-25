#!/usr/bin/env bash
# Author: TG ; created: July 25, 2018

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

ULFTOK_PATH=$(realpath $DIR/../../saral-mt/ulf-tokenizer/ulf-eng-tok.sh)

$ULFTOK_PATH "$@"
