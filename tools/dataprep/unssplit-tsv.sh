#!/usr/bin/env bash

awk -F '\t' '{if (last != $1) {printf "%s%s\t%s", last==""?"":"\n",$1, $2 } else { printf " %s", $2 } last=$1 } END {print}'
