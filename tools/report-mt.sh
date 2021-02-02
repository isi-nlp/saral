#!/usr/bin/env bash

# Author Thamme Gowda
# Date February 2021

# requirements:
#  + sacrebleu   (with MacroF1)
#  + sacremoses
#  + awkg


root=mt-out  # root dir of gfi/mt-out
lang=3C
LC="-lc"
echo "Reporting BLEU, MacroF1 with $LC detok on $lang"


delim=${delim:-','}
#delim='\t'

function scan_mt_names {
    ls $root/{build,analysis}/$lang/$lang-*.out.tsv \
        | grep -v 'ssplit' \
        | xargs -I {} basename {} \
	| sed 's/\.out\.tsv$//' \
	| cut -d- -f3 \
	| sort \
	| uniq 
}

function detokenize_tsv {
    inp_tsv=$1
    out=$2
    [[ -f $inp_tsv ]] || return
    if [[ -f $out ]] ; then
	[[ -f $out.bak ]] && rm $out.bak;
	mv $out $out.bak;
    fi
    cut -f2 $inp_tsv | sacremoses detokenize | sed 's/<unk>//g' > $out
}


mt_names=$(scan_mt_names)
test_names="analysis buildtest builddev"
test_names_str=$(echo $test_names | sed "s/ /$delim$delim/g")

printf "System/BLEU MacroF1${delim}${test_names_str}\n"
for mt in $mt_names; do
    printf "$mt$delim"

    ( for t in $test_names; do
	td=$t  # test dir
	if [[ $t =~ build ]]; then
	    td="build"
	fi
	td=$root/$td
        hyp_tsv=${td}/$lang/$lang-$t-$mt.out.tsv
	hyp_detok=${hyp_tsv/.out.tsv/.detok}
	[[ -f $hyp_detok ]] || detokenize_tsv $hyp_tsv $hyp_detok
        ref=${td}/$lang/$lang-$t.ref
	if [[ ! -f $hyp_detok ]]; then
	    echo "NA-Hyp,NA-Hyp"
	elif [[ ! -f $ref ]]; then
	    echo "NA-Ref,NA-Ref"
	else
	    cat $hyp_detok | sacrebleu -m bleu macrof $LC -b $ref 
	fi
    done ) | tr '\n' ',' 
    printf "\n"
done




