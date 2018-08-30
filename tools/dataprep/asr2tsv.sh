#!/usr/bin/env bash
# Author TG
# This script is for post processing ASR output
# It does two tasks:
#  1. replaces first space with tab character (to make a TSV, first word is ID)
#  2. replaces tokens such as <noise> <silence> etc with elipsis

sed 's/^\([^[:space:]]\+\) /\1\t/' | sed 's/<[a-z]\+>/…/g'
