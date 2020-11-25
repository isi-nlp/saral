#!/usr/bin/env bash
# Author: TG ; created: July 25, 2018

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "ERROR: invalid args, input_path needed"
    echo "Usage: ${BASH_SOURCE[0]} INPUT_PATH.tsv [OUT_PATH.tsv]"
    exit 1
fi

INP=$1
[[ -f $INP ]] || { echo "ERROR: Input $INP doesnt exist;" ; exit 2; }
if [[ $# -eq 2 ]]; then
    OUTP=$2
else
    [[ $INP == *.tsv ]] || { echo "Input $INP is not a TSV";  exit 3; }
    OUTP=${INP/.tsv/.tok.tsv}
fi

[[ -f $OUTP ]] && { echo "output $OUTP exists; not overwriting it;" ; exit 4; }


ULFTOK_PATH=$(realpath $DIR/../../saral-mt/ulf-tokenizer/ulf-eng-tok.sh)
paste <(cut -f1 $INP) <(cut -f2 $INP | $ULFTOK_PATH) > $OUTP
