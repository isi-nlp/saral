# Do Not Translate  (DNT)

## Requires
 - python (>= 3)


## Gold Annotations 

### Scripts

1. makegold.py - make gold annoatations
2. dnt_cut.py - cut DNT tokens from the sequence and put them away (to a separate column in TSV)
3. dnt_paste.py - restore DNT tokens to the sequence
4. dnt_cut_train.py - combines makegold.py and dnt_cut.py into one pipeline

*Example Usage:*

```bash
# If you have tags, how to replace 'em
$ printf "I love Los Angeles\tT T N N" | python3 dnt_cut.py
 I love DNT_1 DNT_2	Los Angeles

# If you have Parallel data, how to replace DNT tokens
$ printf "I love Los Angeles\tAmo Los Angeles" | python3 dnt_cut_train.py
 I love DNT_1 DNT_2	Amo DNT_1 DNT_2	Los Angeles

# How to restore the original tokens 
printf "Amo DNT_1 DNT_2\tLos Angeles" | ./dnt_paste.py

```

---

## Heuristics based Tagger

 It uses two dictionaries, for source and target respectively.

Usage of copyme testing models 3-5.
IIRC 4 or 5 worked best for in LORELEI. This was specficially tuned for il6 = oromo.

```bash
for i in 3 4 5; do
   src/copyme.py -D data/vocab.gz -N data/il6.common.vocab -v $i \
      -i set1.source.tok.tc.head -o set1.source.tok.tc.copyme.v$i ;
done
```