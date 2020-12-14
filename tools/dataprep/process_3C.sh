#! /bin/bash
#
# Note: there are sed and awk portability issues using these scripts
# on MacOS.  Also problems with errors not being caught.  Look at the
# output of every step to make sure things worked.

#wget http://nlp.stanford.edu/software/stanford-corenlp-latest.zip
#unzip stanford-corenlp-latest.zip
#wget https://downloads.lightbend.com/scala/2.13.4/scala-2.13.4.tgz
#tar xf scala-2.13.4.tgz

set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
export CORENLP=$DIR/stanford-corenlp-4.2.0
PATH=$PATH:$DIR/scala-2.13.4/bin
NORM="python $DIR/../../saral-mt/wildebeest/wildebeest_normalize.py"
PATH=$PATH:$(pwd)

# analysis
(cd $SARAL_ROOT/data/gfi/orig && \
     ls IARPA_MATERIAL_OP2-3C/ANALYSIS/text/translation/*.txt | bitext2tsv.sh) >3C-analysis.src-ref.tsv
cut -f1,2 3C-analysis.src-ref.tsv >3C-analysis.src.tsv.orig
cut -f1,2 3C-analysis.src-ref.tsv | $NORM >3C-analysis.src.tsv
cut -f1,3 3C-analysis.src-ref.tsv >3C-analysis.ref.tsv
cat 3C-analysis.src.tsv | ssplit-tsv-tok.sh >3C-analysis-ssplit.src.tok.tsv
cut -f1 3C-analysis-ssplit.src.tok.tsv >3C-analysis-ssplit.ids
ulftok-tsv.sh 3C-analysis.src.tsv 3C-analysis.src.tok.tsv
ulftok-tsv.sh 3C-analysis.ref.tsv 3C-analysis.ref.tok.tsv
cut -f1 3C-analysis.src.tok.tsv >3C-analysis.ids

# dev
(cd $SARAL_ROOT/data/gfi/orig && \
     ls IARPA_MATERIAL_OP2-3C/DEV/text/src/*.txt | plain2tsv.sh) >3C-dev.src.tsv.orig
cut -f1,2 3C-dev.src.tsv.orig | $NORM >3C-dev.src.tsv
cat 3C-dev.src.tsv | ssplit-tsv-tok.sh >3C-dev-ssplit.src.tok.tsv
cut -f1 3C-dev-ssplit.src.tok.tsv >3C-dev-ssplit.ids
ulftok-tsv.sh 3C-dev.src.tsv 3C-dev.src.tok.tsv
cut -f1 3C-dev.src.tok.tsv >3C-dev.ids

# build
# buildtrain has some very long lines; discard them now
cp $SARAL_ROOT/data/gfi/mt-out/build1/3C/buildtrain.kk.en.raw.txt $SARAL_ROOT/data/gfi/mt-out/build1/3C/buildtrain.kk.en.raw.txt.orig
cut -f1 $SARAL_ROOT/data/gfi/mt-out/build1/3C/buildtrain.kk.en.raw.txt >buildtrain.kk
cut -f2 $SARAL_ROOT/data/gfi/mt-out/build1/3C/buildtrain.kk.en.raw.txt >buildtrain.en
/nas/material02/users/joelb/views/mosesdecoder/scripts/training/clean-corpus-n.perl buildtrain kk en buildtrain.clean 1 150
paste buildtrain.clean.kk buildtrain.clean.en >$SARAL_ROOT/data/gfi/mt-out/build1/3C/buildtrain.kk.en.raw.txt

for ds in buildtrain builddev buildtest; do    
    cut -f1 $SARAL_ROOT/data/gfi/mt-out/build1/3C/${ds}.kk.en.raw.txt >3C-${ds}.src.orig
    cut -f2 $SARAL_ROOT/data/gfi/mt-out/build1/3C/${ds}.kk.en.raw.txt >3C-${ds}.ref
    count=$(cat 3C-${ds}.src.orig | wc -l)
    ids=3C-${ds}.ids
    paste -d _ <(seq $count) <(seq $count) >$ids
    cat 3C-${ds}.src.orig | $NORM | paste $ids /dev/stdin >3C-${ds}.src.tsv
    cat 3C-${ds}.ref | paste $ids /dev/stdin >3C-${ds}.ref.tsv
    ulftok-tsv.sh 3C-${ds}.src.tsv 3C-${ds}.src.tok.tsv
    ulftok-tsv.sh 3C-${ds}.ref.tsv 3C-${ds}.ref.tok.tsv
done
