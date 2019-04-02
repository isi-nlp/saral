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

[[ -f $INP ]] || { echo "Error: Input $INP doesnt exist;" ; exit 2; }
[[ $INP == *.tsv ]] || { echo "Errror: Input $INP is not a TSV";  exit 3; }
[[ -f $OUTP ]] && { echo "Error: output $OUTP exists; not overwriting it;" ; exit 4; }


ULFTOK_PATH=$(realpath $DIR/../../saral-mt/ulf-tokenizer/ulf-eng-tok.sh)
MOSESTOK_PATH=$(realpath $DIR/../../saral-mt/moses-tokenizer/tokenizer.perl)

[[ -f $MOSESTOK_PATH ]] || { echo "Error: moses tokenizer not found at $MOSESTOK_PATH" ; exit 5; }
[[ -f $ULFTOK_PATH ]] || { echo "Error: ULF tokenizer not found at $ULFTOK_PATH" ; exit 5; }

paste <(cut -f1 $INP) <(cut -f2 $INP | $MOSESTOK_PATH -no-escape | $ULFTOK_PATH) > $OUTP
