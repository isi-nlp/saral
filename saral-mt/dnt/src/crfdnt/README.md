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
```


## 1. Prepare

```
$ python -m crfdnt prepare -h
usage: __main__.py prepare [-h] [-i INP] [-o OUT] [-s]
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
  -f {src-tags,tags,conll}, --format {src-tags,tags,conll}
                        Format of output: `src-tag`: output SOURCE\tTAG per
                        line. `tag`: output just TAG sequence per line.
                        `conll`: output in CoNLL 2013 NER format. (default:
                        src-tags)
```

**Example**

```
cat lang1-lang2.tsv | python -m crfdnt prepare > all-seq.tsv

# split all-seq into train and test
cat all-seq.tsv | shuf > all-seq-shuf.tsv
l=`wc -l all-seq-shuf.tsv | awk '{print int($1*0.8)}'`
split -l $l all-seq-shuf.tsv part
mv partaa train-seq.tsv
mv partab test-seq.tsv
```

## 2. Train

```
python -m crfdnt train -h
usage: __main__.py train [-h] [-i INP] [-c CONTEXT] model

positional arguments:
  model                 Path to store model file

optional arguments:
  -h, --help            show this help message and exit
  -i INP, --inp INP     Input stream of Training data. Default is STDIN. When
                        specified, it should be a file path. Data
                        Format=SRC_SEQUENCE\tTAG_SEQUENCE per line (default:
                        <_io.TextIOWrapper name='<stdin>' mode='r'
                        encoding='UTF-8'>)
  -c CONTEXT, --context CONTEXT
                        Context in sequence. (default: 2)
  -v, --verbose         Verbose (default: False)
```

**Example**
```
 python -m crfdnt train -i train-seq.tsv dnt-model1.pycrf
```


## Evaluate

```
python -m crfdnt eval -h
usage: __main__.py eval [-h] [-i INP] [-c CONTEXT] [-e] model

positional arguments:
  model                 Path to the stored model file

optional arguments:
  -h, --help            show this help message and exit
  -i INP, --inp INP     Input stream of Test data. Default is STDIN. When
                        specified, it should be a file path. Data
                        Format=SRC_SEQUENCE\tTAG_SEQUENCE per line (default:
                        <_io.TextIOWrapper name='<stdin>' mode='r'
                        encoding='UTF-8'>)
  -c CONTEXT, --context CONTEXT
                        Context in sequence. (default: 2)
  -e, --explain         Explain top state transitions and weights (default:
                        False)

```

**Example**

```
python -m crfdnt eval -i test-seq.tsv dnt-model1.pycrf -e
```


# Predict tags for new sequence
```
python -m crfdnt tag -h
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
  -c CONTEXT, --context CONTEXT
                        Context in sequence. (default: 2)

```
**Example**

```
cat test-seq.tsv | cut -f1 | python -m crfdnt tag  dnt-model1.pycrf

```


## Questions?

Send them to *Thamme Gowda TG(at)ISI(dot)EDU*
