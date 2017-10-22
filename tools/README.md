## Tools

### Corpus Splitter

Useful for splitting corpus in to train, dev and test, subject to following 2 constraints:
 - number of token count per each split is set by user
 - All segments of a document belong to a single a split

Example Usage

```
$ ./corpus_splitter.py -i .../IARPA_MATERIAL_BASE-1B-BUILD_v1.0/bitext/MATERIAL_BASE-1B-BUILD_bitext.txt \
 -dev 50000 -test 30000 -o .../bitexts/1B/1B-bitext

```

Usage manual:
```
./corpus_splitter.py -h
usage: corpus_splitter.py [-h] -i IN -o OUT -dev DEV -test TEST

optional arguments:
  -h, --help            show this help message and exit
  -i IN, --in IN        material data file
  -o OUT, --out OUT     Output prefix
  -dev DEV, --dev DEV   Development size in number of tokens
  -test TEST, --test TEST
                        Test Size in number of tokens

```

