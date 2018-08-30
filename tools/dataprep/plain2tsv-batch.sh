#!/usr/bin/env bash

if [[ $# -lt 2 ]]; then
    echo "Invalid args. Usage: plain2tsv-batch.sh <DATA_DIR> <OUT_DIR>"
    exit 1
fi
DATA=$1
OUT=$2
SPLIT=true
[[ $3 == "-nosplit" || $3 == "--no-split" ]] && SPLIT=false
[[ -d $OUR ]] || mkdir -p $OUT

langs=( 1A 1B )
splits=( EVAL1 EVAL2 ANALYSIS1 DEV )
for lang in ${langs[@]}; do
    for split in ${splits[@]}; do
	      text_d=$DATA/IARPA_MATERIAL_BASE-$lang/$split/text
	      bitext_d=$text_d/translation
	      out_pref="$OUT/$lang-${split,,}"
	      if [[ -d $bitext_d ]]; then
	          bitext_f="${out_pref}.bitext.tsv"
	          cmd="ls -1 $bitext_d/*.txt | bitext2tsv.sh > ${bitext_f}"
	          echo "$cmd"
	          if eval "${cmd}"; then
		            cat $bitext_f | cut -f1,2 >  ${out_pref}.src.tsv
		            cat $bitext_f | cut -f1,3 >  ${out_pref}.tgt.tsv
	          fi
	      else
	          mono_d=$text_d/src
	          if [[ ! -d $mono_d ]]; then
		            echo "Cant find bitext or mono text in $lang $split"
		            continue
	          fi
	          out_f=${out_pref}.src.tsv
            if [[ $SPLIT == true ]]; then
                cmd="ls -1 $mono_d/*.txt | plain2tsv-ssplit.sh > $out_f "
            else
                cmd="ls -1 $mono_d/*.txt | plain2tsv.sh > $out_f"
            fi
	          echo "$cmd"
	          eval "${cmd}"
	      fi
    done
done
