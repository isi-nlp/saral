#!/usr/bin/env bash

if [[ $# -ne 2 ]]; then
    echo "Error: Invalid Args! Usage: <DATA_DIR> <OUT_DIR>"
    exit 1
fi
data_d=$1
out_d=$2
[[ -d $out_d ]] || mkdir -p $out_d 

langs=( 1A 1B )
packs=( BUILD DEV ANALYSIS1 EVAL1 EVAL2 ) 
version="v1.0"
pref='IARPA_MATERIAL_BASE'
for lang in ${langs[@]}; do
    for pack in ${packs[@]}; do
	
	data_f=$data_d/$pref-$lang-${pack}_$version.tgz
	if [[ ! -f $data_f ]]; then echo "Error:File $data_f not found."; continue; fi
	text_d="$pref-$lang/$pack/text"
	# build pack is different
	[[ $pack == "BUILD" ]] && text_d="$pref-$lang-${pack}_$version/bitext"
	cmd="tar xvf $data_f $text_d -C $out_d"
	echo "$cmd"
	eval "$cmd"
    done
done
