#!/usr/bin/env bash
# Author: Thamme Gowda created: May 11, 2018

#$ -P material -cwd  -pe mt 2 -l h_vmem=8G,h_rt=24:00:00,gpu=1
# Note: requires more RAM for bigger datasets, CRF tagger uses whole dataset as one batch

if [[ $# -ne 1 ]]; then
    echo "Invalid Args. Usage: $0 SPLIT"
    exit 2
fi
SPLIT=$1

source $HOME/.bashrc
# conda environment must have: python3.6+, pytorch, python-crfsuite, emoji, torchtext, spacy etc...
source activate py3

## Settings begin ###
EPOCHS=40
DIR=/nas/material/users/tg/work/material/y1/experiments/dnt/es-en/nmt-crf-dnt-v2
OUT="$DIR/$SPLIT"
ONMT="/nas/home/tg/libs/OpenNMT-py"
DATA="/nas/material/users/tg/work/material/y1/experiments/dnt/es-en/data"
# Source code of this dnt repository
export PYTHONPATH=/nas/home/tg/work/libs2/saral/saral-mt/dnt/src

SRC="tok.es"
TGT="tok.en"
REF="en"

TRAIN_SRC=${DATA}/train_$SPLIT.$SRC
TRAIN_TGT=${DATA}/train_$SPLIT.$TGT
DEV_SRC=${DATA}/tune.$SRC
DEV_TGT=${DATA}/tune.$TGT
TEST_SRC=${DATA}/test.$SRC
TEST_TGT=${DATA}/test.$TGT
TEST_REF=${DATA}/test.$REF
SEED=4321


#### Settings End ####

[[ -d ${OUT}/models ]] || mkdir -p ${OUT}/models
[[ -d ${OUT}/data ]] || mkdir -p ${OUT}/data
[[ -d ${OUT}/dnt ]] || mkdir -p ${OUT}/dnt
[[ -d ${OUT}/test ]] || mkdir -p ${OUT}/test
DNT_MODEL=${OUT}/dnt/dntmodel.crf

# copy this script for reproducibility
cp "${BASH_SOURCE[0]}" $OUT/run.sh.bak

shopt -s expand_aliases
alias crfdnt="python -m crfdnt"
alias bleu="$ONMT/tools/multi-bleu-detok.perl"
alias detok="$ONMT/tools/detokenize.perl"

function log(){
    printf "`date`::$1\n" >> ${OUT}/log.log
}

log "Training:: $TRAIN_SRC --> $TRAIN_TGT"
log "Dev     :: $DEV_SRC --> $DEV_TGT"
log "Test    :: $TEST_SRC --> $TEST_TGT"


if [[ ! -f ${OUT}/_DNT_TRAIN_SUCCESS ]]; then
    echo "Training DNT tagger"
    log "Preparing DNT training data "
    log "Training a tagger"
    NER_MODEL="en_core_web_lg"
    paste ${TRAIN_SRC} ${TRAIN_TGT} | crfdnt train --bitext --ner-model $NER_MODEL ${DNT_MODEL}

    log "Evaluating DNT tagger"
    paste ${TRAIN_SRC} ${TRAIN_TGT} | crfdnt prepare --ner-model $NER_MODEL > ${OUT}/dnt/train.src.dnttag.tsv
    paste ${DEV_SRC} ${DEV_TGT} | crfdnt prepare --ner-model $NER_MODEL > ${OUT}/dnt/dev.src.dnttag.tsv
    crfdnt eval -i ${OUT}/dnt/train.src.dnttag.tsv ${DNT_MODEL} -e > ${OUT}/test/dnt.train.score.txt
    crfdnt eval -i ${OUT}/dnt/dev.src.dnttag.tsv ${DNT_MODEL} -e > ${OUT}/test/dnt.dev.score.txt

    [[ -f $DNT_MODEL ]] && touch $OUT/_DNT_TRAIN_SUCCESS
fi


if [[ ! -f $OUT/_DNT_CUT_SUCCESS ]]; then
    echo "preprocessing MT data using DNT tagger"
    # TODO: use gold tagger for NMT training
    paste ${TRAIN_SRC} ${TRAIN_TGT} | crfdnt dnt-cut ${DNT_MODEL} | awk -F '\t' -v out=${OUT}/data \
     '{print $1 > out"/train.src"; print $2 > out"/train.tgt"; print $3 > out"/train.dnt"; }'
    paste ${DEV_SRC} ${DEV_TGT} | crfdnt dnt-cut ${DNT_MODEL} | awk -F '\t'  -v out=${OUT}/data \
     '{print $1 > out"/dev.src"; print $2 > out"/dev.tgt"; print $3 > out"/dev.dnt"; }'

    paste ${TEST_SRC} | crfdnt dnt-cut ${DNT_MODEL} | awk -F '\t'  -v out=${OUT}/test \
     '{print $1 > out"/test.src"; print $2 > out"/test.dnt" }'

    # Test Ref goes un processed
    ln -s $TEST_REF $OUT/test/test.ref
   [[ `ls ${OUT}/data/* | wc -l` -ge 6 ]] && touch ${OUT}/_DNT_CUT_SUCCESS
fi


# update these variables
NAME="run1"

if [[ ! -f $OUT/_NMT_TRAIN_SUCCESS ]]; then
    log "ONMT Preprocessing"
    python $ONMT/preprocess.py -seed $SEED \
           -train_src $OUT/data/train.src \
           -train_tgt $OUT/data/train.tgt \
           -valid_src $OUT/data/dev.src \
           -valid_tgt $OUT/data/dev.tgt \
           -save_data $OUT/data/processed \
           -src_seq_length 200 -tgt_seq_length 200

    GPU_OPTS="-gpuid 0"
    CMD="python $ONMT/train.py -data $OUT/data/processed -save_model $OUT/models/$NAME $GPU_OPTS -dropout 0.5 -epochs $EPOCHS -seed $SEED -rnn_size 512 -enc_layers 1 -dec_layers 1 -encoder_type brnn "
    log  "ONMT Training command ::\n\n $CMD \n"
    #eval "$CMD"
    if eval "${CMD}"; then
        touch $OUT/_NMT_TRAIN_SUCCESS
    else
        echo "Training failed. exiting..."
        exit 4
    fi
fi

# select a model with high accuracy and low perplexity
# TODO: currently using linear scale, maybe not the best
model=`ls $OUT/models/*.pt| awk -F '_' 'BEGIN{maxv=-1000000} {score=$(NF-3)-$(NF-1); if (score > maxv) {maxv=score; max=$0}}  END{ print max}'`
log "ONMT Chosen Model = $model"
if [[ -z "$model" ]]; then
    echo "Model not found. Looked in $OUT/models/"
    exit
fi

if [[ ! -f $OUT/_NMT_DECODE_SUCCESS ]]; then
    GPU_OPTS="-gpu 0"
    log "Step 3a: Translate Test"
    python $ONMT/translate.py -model $model \
           -src $OUT/test/test.src \
           -output $OUT/test/test.out \
           -replace_unk  -verbose $GPU_OPTS > $OUT/test/test.log

    log "Step 3b: Translate Dev"
    python $ONMT/translate.py -model $model \
           -src $OUT/data/dev.src \
           -output $OUT/test/dev.out \
           -replace_unk -verbose $GPU_OPTS > $OUT/test/dev.log
    if [[ -s $OUT/test/test.out && -s $OUT/test/dev.out ]]; then
        touch $OUT/_NMT_DECODE_SUCCESS
    else
        echo "Decode failed"
        exit 5
    fi
fi
echo "Step 4a: Evaluate "


# DNT paste
paste $OUT/test/test.out $OUT/test/test.dnt | crfdnt dnt-paste | detok > $OUT/test/test.out.detok
paste $OUT/test/dev.out $OUT/data/dev.dnt | crfdnt dnt-paste | detok > $OUT/test/dev.out.detok

bleu $OUT/test/test.ref < $OUT/test/test.out.detok > $OUT/test/test.tc.bleu
bleu -lc $OUT/test/test.ref < $OUT/test/test.out.detok > $OUT/test/test.lc.bleu

bleu $OUT/data/dev.tgt < $OUT/test/dev.out.detok > $OUT/test/dev.tok.tc.bleu
bleu  -lc $OUT/data/dev.tgt < $OUT/test/dev.out.detok > $OUT/test/dev.tok.lc.bleu

log "Done"
