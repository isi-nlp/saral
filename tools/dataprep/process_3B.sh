
PACK=/nas/material/users/tg/work/data/material/orig/IARPA_MATERIAL_OP2-3B
MTOUT=/nas/material/users/tg/work/data/material/gfi/mt-out

# activate environment
source ~/libs/saral/tools/dataprep/activate.sh

# make dirs
mkdir $MTOUT/{build,analysis,dev,eval}/3B
mkdir $MTOUT/{analysis,dev,eval}/3B-asr

# copy all build data
cd $MTOUT/build/3B
cp $PACK/BUILD/bitext/3B_bitext.txt 3B-build.src-ref.orig.tsv
wildebeest < 3B-build.src-ref.orig.tsv  > 3B-build.src-ref.tsv

# split train, dev, test
corpus_splitter.py -i 3B-build.src-ref.orig.tsv  -o 3B-build -dev 6000 -test 10000
# restore extension src-ref.orig.tsv
for i in 3B-build{dev,test,train}.tsv ; do mv $i ${i/.tsv/.src-ref.orig.tsv}; done
# normalize
for i in 3B-build{dev,test,train}.src-ref.orig.tsv ; do wildebeest < $i > ${i/.orig}; done

# seperate source and target
for i in 3B-build{dev,test,train}.src-ref.tsv; do
    cut -f1,2 < $i > ${i/-ref};
    cut -f1,3 < $i > ${i/src-};
done
# tokenize
for i in 3B-build{dev,test,train}.{src,ref}.tsv; do ulftok-tsv.sh $i;  done



    

# Analysis
cd $MTOUT/analysis/3B
ls $PACK/ANALYSIS/text/translation/*.txt | bitext2tsv.sh > 3B-analysis.src-ref.orig.tsv 
# normalize
wildebeest < 3B-analysis.src-ref.orig.tsv > 3B-analysis.src-ref.tsv
cut -f1 3B-analysis.src-ref.tsv  > 3B-analysis.ids
cut -f1,2 3B-analysis.src-ref.tsv  > 3B-analysis.src.tsv
cut -f1,3 3B-analysis.src-ref.tsv  > 3B-analysis.ref.tsv
ulftok-tsv.sh 3B-analysis.src.tsv
ulftok-tsv.sh 3B-analysis.ref.tsv

# ssplit
ssplit-tsv-tok.sh < 3B-analysis.src.tsv > 3B-analysis-ssplilt.src.tok.tsv
cut -f1 3B-analysis-ssplilt.src.tok.tsv > 3B-analysis-ssplilt.ids

#another norm
#paste <(cut -f1 $orig) <(cut -f2 $orig | sacremoses normalize -q -d -p -c) <(cut -f3 $orig | sacremoses normalize -q -d -p -c ) > ${norm/norm/norm2}


# Dev pack
cd $MTOUT/dev/3B 
ls $PACK/DEV/text/src/*.txt  | plain2tsv.sh > 3B-dev.src.orig.tsv
wildebeest < 3B-dev.src.orig.tsv > 3B-dev.src.tsv

 ulftok-tsv.sh 3B-dev.src.tsv
 ssplit-tsv-tok.sh < 3B-dev.src.tsv > 3B-dev-ssplit.src.tok.tsv
 cut -f1 3B-dev-ssplit.src.tok.tsv  > 3B-dev-ssplit.ids
 



