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
