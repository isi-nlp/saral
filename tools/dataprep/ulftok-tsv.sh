#!/usr/bin/env bash
# Author: TG ; created: July 25, 2018

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
if [ $# -ne 1 ]; then
    echo "ERROR: invalid args, input_path needed"
    echo "Usage: ${BASH_SOURCE[0]} INPUT_PATH"
    exit 1
fi

INP=$1

OUTP=${INP/.tsv/.tok.tsv}

[[ -f $INP ]] || { echo "Input $INP doesnt exist;" ; exit 2; }
[[ $INP == *.tsv ]] || { echo "Input $INP is not a TSV";  exit 3; }
[[ -f $OUTP ]] && { echo "output $OUTP exists; not overwriting it;" ; exit 4; }


ULFTOK_PATH=$(realpath $DIR/../../saral-mt/ulf-tokenizer/ulf-eng-tok.sh)
paste <(cut -f1 $INP) <(cut -f2 $INP | $ULFTOK_PATH) > $OUTP
