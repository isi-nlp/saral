#!/usr/bin/env python3
# Author: TG;; Created July 16, 2018
# Force split records that exceeds given length
import sys
import argparse
from pathlib import Path


def ssplit_tsv_len(inp, out, max_len):
    recs = (line.split('\t') for line in inp)
    recs = ((rec[0].strip(), rec[1].strip().split()) for rec in recs if len(rec) >= 2)
    for _id, toks in recs:
        if not toks: # if there is an empty line with an ID, preserve it!!
            toks = [' ']
        for i in range(0, len(toks), max_len):
            seq = ' '.join(toks[i: i+max_len])
            out.write(f'{_id}\t{seq}\n')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-i', '--inp', help='input TSV file', default=sys.stdin, type=argparse.FileType('r'))
    p.add_argument('-o', '--out', help='Output TSV file', default=sys.stdout, type=argparse.FileType('w'))
    p.add_argument('-l', '--max-len', help='Max Length', default=80, type=int)
    args = p.parse_args()
    ssplit(**vars(args))

if __name__ == '__main__':
    main()
