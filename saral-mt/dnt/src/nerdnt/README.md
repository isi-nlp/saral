# Tagger v2 - DNT with categories:

This tagger uses Named Entity Recognition model of Target(which happens to be English) to categorize the DNT tags on source side.

Pipeline inlcudes 2 steps

1. dnt_cut.py
2. dnt_paste.py

## Usage: 
```bash
$ printf  "USC yu Los Angeles alli ide .\tUSC is in Los Angeles " | ./dnt_cut.py   
DNT_ORG_1 yu DNT_GPE_1 alli ide .       DNT_ORG_1 is in DNT_GPE_1       {"ORG": ["USC"], "GPE": ["Los Angeles"]}

$ printf  "USC yu Los Angeles alli ide .\tUSC is in Los Angeles " | ./dnt_cut.py | cut -f1,3 
DNT_ORG_1 yu DNT_GPE_1 alli ide .       {"ORG": ["USC"], "GPE": ["Los Angeles"]} 

printf  "USC yu Los Angeles alli ide .\tUSC is in Los Angeles " | ./dnt_cut.py | cut -f1,3 | ./dnt_paste.py 
USC yu Los Angeles alli ide .
```


# Setup 

    conda install spacy
    python -m spacy download en_core_web_lg
    
## More options:
```bash
./dnt_cut.py -h
INFO:root:Spacy Version: 2.0.11
usage: dnt_cut.py [-h] [-i INP] [-o OUTP] [-m MODEL]

Replaces copy words with template tokens in source and target of parallel
corpus.

optional arguments:
  -h, --help            show this help message and exit
  -i INP, --in INP      Input. Each line should have 'SRC_SEQ<tab>TGT_SEQ'.
                        Source SEQ is source text and target SEQ is target
                        text. (default: <_io.TextIOWrapper name='<stdin>'
                        mode='r' encoding='UTF-8'>)
  -o OUTP, --out OUTP   Output. Each line will have 'SEQ1<tab>SEQ2<tab>SEQ3'.
                        SEQ1 and SEQ2 will be SEQ1 and SEQ2 of inputs after
                        replacements. SEQ3 will have words words that are cut
                        from inputs, each position will correspond to the
                        suffix of template token. Example: DNT_1 template
                        token in SEQ1 correspond to the first token in SEQ2
                        (default: <_io.TextIOWrapper name='<stdout>' mode='w'
                        encoding='UTF-8'>)
  -m MODEL, --model MODEL
                        Spacy Model for NER. Example: en_core_web_sm,
                        en_core_web_md, en_core_web_lg etc (default:
                        en_core_web_lg)
```


