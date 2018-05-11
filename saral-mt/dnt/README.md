# CRF DNT Tagger


Goal: Build and evaluate a DO NOT TRANSLATE (DNT) Tagger model from MT
 parallel data using CRF.

## Steps:
1. Prepare parallel data for sequence tagging
2. Train a tagger model
3. Evaluate a tagger model
4. Predict tags for new data


## SETUP

```
pip install python-crfsuite

# add src directory to the path variable
export PYTHONPATH=...saral/saral-mt/dnt/src
alias crfdnt="python -m crfdnt"
```


## 1. Prepare

```
$ crfdnt prepare -h
usage: crfdnt prepare [-h] [-i INP] [-o OUT] [-s]
                           [-f {src-tags,tags,conll}]

optional arguments:
  -h, --help            show this help message and exit
  -i INP, --inp INP     Input stream. Default is STDIN. When specified, it
                        should be a file path. Data
                        Format=SRC_SEQUENCE\tTGT_SEQUENCE per line (default:
                        <_io.TextIOWrapper name='<stdin>' mode='r'
                        encoding='UTF-8'>)
  -o OUT, --out OUT     Output stream. Default is STDOUT. When specified, it
                        should be a file path. Data Format depends on the (-f,
                        --format) argument (default: <_io.TextIOWrapper
                        name='<stdout>' mode='w' encoding='UTF-8'>)
  -s, --swap            Swap the columns in input (default: False)
  -f {src-tags,tags,conll,TN}, --format {src-tags,tags,conll,TN}
                        Format of output: `src-tag`: output SOURCE\tTAG per
                        line. `tag`: output just TAG sequence per line.
                        `conll`: output in CoNLL 2013 NER format. `TN`:
                        outputs binary flags: T for Translate, N for Not-
                        translate (default: src-tags)
 -ner NER_MODEL, --ner-model NER_MODEL
                        NER model for categorising the DNT tags. NER is
                        powered by Spacy, hence the value should be a valid
                        spacy model. Example: {en_core_web_sm, en_core_web_md,
                        en_core_web_lg}. When not specified, no NER
                        categorization will be done. (default: None)
```

**Example**

```
cat lang1-lang2.tsv | crfdnt prepare > all-seq.tsv

# split all-seq into train and test
cat all-seq.tsv | shuf > all-seq-shuf.tsv
l=`wc -l all-seq-shuf.tsv | awk '{print int($1*0.8)}'`
split -l $l all-seq-shuf.tsv part
mv partaa train-seq.tsv
mv partab test-seq.tsv
```

## 2. Train

```
crfdnt train -h
usage: crfdnt train [-h] [-i INP] [-c CONTEXT] model

positional arguments:
  model                 Path to store model file

optional arguments:
  -h, --help            show this help message and exit
  -i INP, --inp INP     Input stream of Training data. Default is STDIN. When
                        specified, it should be a file path. Data
                        Format=SRC_SEQUENCE\tTAG_SEQUENCE per line by default
                        Data Format=SRC_SEQUENCE\tTGT_SEQUENCE i.e. parallel
                        bitext when --bitext is used (default:
                        <_io.TextIOWrapper name='<stdin>' mode='r'
                        encoding='UTF-8'>)
  -c CONTEXT, --context CONTEXT
                        Context in sequence. (default: 2)
  -bt, --bitext         input is a parallel bitext (default: False)
  -ner NER_MODEL, --ner-model NER_MODEL
                        Applicable for --bitext mode. NER model for
                        categorising the tags. NER is powered by Spacy, hence
                        the value should be a valid spacy model. Example:
                        {en_core_web_sm, en_core_web_md, en_core_web_lg}. When
                        not specified, no NER categorization will be done.
                        (default: None)
  -nm, --no-memorize    Do not memorize words (default: False)
  -v, --verbose         Verbose (default: False)
```

**Example**
```
 crfdnt train -i train-seq.tsv dnt-model1.pycrf
 # From training data directly
 paste train.src train.tgt | crfdnt train -bt dnt-model1.pycrf
```


## Evaluate

```
crfdnt eval -h
usage: crfdnt eval [-h] [-i INP] [-c CONTEXT] [-e] model

positional arguments:
  model                 Path to the stored model file

optional arguments:
  -h, --help            show this help message and exit
  -i INP, --inp INP     Input stream of Test data. Default is STDIN. When
                        specified, it should be a file path. Data
                        Format=SRC_SEQUENCE\tTAG_SEQUENCE per line (default:
                        <_io.TextIOWrapper name='<stdin>' mode='r'
                        encoding='UTF-8'>)
  -e, --explain         Explain top state transitions and weights (default:
                        False)
```

**Example**

```
crfdnt eval -i test-seq.tsv dnt-model1.pycrf -e
```


# Predict tags for new sequence
```
crfdnt tag -h
usage: __main__.py tag [-h] [-i INP] [-o OUT] [-c CONTEXT] model

positional arguments:
  model                 Path to the stored model file

optional arguments:
  -h, --help            show this help message and exit
  -i INP, --inp INP     Input stream of data. Default is STDIN. When
                        specified, it should be a file path. Data Format=one
                        SRC_SEQUENCE per line (default: <_io.TextIOWrapper
                        name='<stdin>' mode='r' encoding='UTF-8'>)
  -o OUT, --out OUT     Output stream. Default is STDOUT. When specified, it
                        should be a file path. Data
                        Format=SRC_SEQUENCE\tTAG_SEQUENCE per line. (default:
                        <_io.TextIOWrapper name='<stdout>' mode='w'
                        encoding='UTF-8'>)
```
**Example**

```
cat test-seq.tsv | cut -f1 | crfdnt tag  dnt-model1.pycrf
```


## Questions?

Send them to *Thamme Gowda TG(at)ISI(dot)EDU*
