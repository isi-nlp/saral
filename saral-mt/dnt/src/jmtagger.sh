#!/usr/bin/env bash

# Wrapper script for Jon May's heuristic based DNT tagger

if [[ $# -ne 1 ]]; then
    echo "Illegal number of parameters"
    echo "Usage: <Source File>"
    exit 1
fi

SOURCE=$1

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=$DIR

tag_cmd="$DIR/copyme.py -ep -i $SOURCE -D $DIR/../data/vocab.gz -N $DIR/../data/il6.common.vocab -v 6"
paste $SOURCE <(${tag_cmd} | python -c 'import sys;
for line in sys.stdin:
    print(" ".join(map(lambda x: "N" if x.startswith("@@") else "T", line.strip().split())))')
