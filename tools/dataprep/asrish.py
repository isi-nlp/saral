#!/usr/bin/env python
#
# Author: Thamme Gowda [tg (at) isi (dot) edu] 
# Created: 2019-08-12

"""
This tool converts text to look like asr output.
It does so by
- converting text to lowercase
- removing punctuations, except dot (.)
"""
import argparse
import sys
import logging as log
from typing import TextIO, Iterator
import string
log.basicConfig(level=log.INFO)

keep_puncts = {'.'}
remove_puncts = ''.join(x for x in string.punctuation if x not in keep_puncts)
punct_to_space = str.maketrans(remove_puncts, ' ' * len(remove_puncts))

def asr_ish(sentence: str, lowercase: bool = True, remove_puncts: bool = True) -> str:
    if lowercase:
        sentence = sentence.lower()
    if remove_puncts:
        sentence = sentence.translate(punct_to_space) # remove puncts
        sentence = ' '.join(sentence.split()) # multiple spaces with single space
    return sentence


def main(inp: Iterator[str], out: TextIO):
    count = 0
    for line in inp:
        line = asr_ish(line)
        out.write(line.strip() + '\n')
        count += 1
    log.info(f"Wrote {count} lines to {out.name}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('-i', '--inp', type=argparse.FileType('r'), default=sys.stdin,
                   help='Input file path')
    p.add_argument('-o', '--out', type=argparse.FileType('w'), default=sys.stdout,
                   help='Output file path')
    args = vars(p.parse_args())
    main(**args)
