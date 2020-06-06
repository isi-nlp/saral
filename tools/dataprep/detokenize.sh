#!/usr/bin/env bash

DIR="$(dirname "${BASH_SOURCE[0]}")"  # get the directory name
DIR="$(realpath "${DIR}")"    # resolve its full path if need be

$DIR/detokenize.perl 2> /dev/null |  sed 's/ @\([^@ ]\+\)@ /\1/g' 
