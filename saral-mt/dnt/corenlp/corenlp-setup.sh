#!/usr/bin/env bash
# Author Thamme Gowda, created on May 12,  2018
# This script setups core NLP

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# CORENLP
URL="http://nlp.stanford.edu/software/stanford-corenlp-full-2018-02-27.zip"
LOC_DIR="$DIR/stanford-corenlp-full-2018-02-27"
ZIP_FILE="${LOC_DIR}.zip"

if [[ ! -d "$LOC_DIR" ]]; then
    mkdir -p "$LOC_DIR"
    [[ -f ${ZIP_FILE} ]] || wget $URL -O "${LOC_DIR}.zip"
    unzip ${ZIP_FILE} -d $DIR && rm ${ZIP_FILE}
fi


# scala
URL="https://downloads.lightbend.com/scala/2.12.4/scala-2.12.4.tgz"
LOC_DIR="$DIR/scala-2.12.4"
if [[ ! -d "$LOC_DIR" ]]; then
    wget $URL -O "${LOC_DIR}.tgz"
    tar xzf "${LOC_DIR}.tgz" -C $DIR
    rm "${LOC_DIR}.tgz"
fi