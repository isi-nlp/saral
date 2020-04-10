#!/usr/bin/env python
#
# Author: Thamme Gowda [tg (at) isi (dot) edu] 
# Created: 4/10/20
# !/usr/bin/env python3

"""Script to filter possibly mis aligned sentences"""

import argparse
import sys
import numpy as np
import unicodedata
import logging as log
from collections import defaultdict as ddict
import json

log.basicConfig(level=log.INFO)


def len_alignment(src, tgt):
    """Check that the length ratios are in the permissible range (3x)"""
    return 0.33 <= (1 + len(src)) / (1 + len(tgt)) <= 3.0

def digit_alignment(src, tgt, diff=0):
    n_src = sum(1 for c in src if c.isdigit())
    n_tgt = sum(1 for c in tgt if c.isdigit())
    return abs(n_src - n_tgt) <= diff


def punctuation_alignment(src, tgt, diff=5):
    n_src = sum(1 for c in src if unicodedata.category(c).startswith('P'))
    n_tgt = sum(1 for c in tgt if unicodedata.category(c).startswith('P'))
    return abs(n_src - n_tgt) <= diff

def is_url(str):
    # dummy checker
    return ' ' not in str and (str.startswith('http://') or str.startswith('https://'))

def urls_alignment(src, tgt):
    src_urls = set(w for w in src.split() if is_url(w))
    tgt_urls = set(w for w in tgt.split() if is_url(w))
    return len(src_urls) == len(tgt_urls) == len(src_urls & tgt_urls)

def ascii_alignment(src, tgt):
    """Check that there are approximately same ratio of punctuations and numerals (2x). exclude alphabets"""
    src_ct = 1.0 + sum(1 for c in src if ord(c) < 256 and not c.isalpha())
    tgt_ct = 1.0 + sum(1 for c in tgt if ord(c) < 256 and not c.isalpha())
    return 0.5 <= src_ct / tgt_ct <= 2.0


def get_extremes(data, n_stds):
    data = np.array(data)
    mean = np.mean(data)
    std = np.std(data)
    return mean - std * n_stds, mean + std * n_stds

def format_table(data, col_names):

    res = f'Name\t' + "\t".join(col_names) + '\n'
    for name, row in data.items():
        cols = '\t'.join([f'{row[c]:,}'.rjust(8) for c in col_names])
        res += f'{name}\t{cols}\n'
    return res

def main(inp, out, negate=False, n_stds=2, min_len=1, max_len=200, digits=-1, puncts=-1):
    data = []
    log.info(f'Loading data to memory from {inp}. This could take some time')

    for line in inp:
        parts = line.strip().split('\t')
        if len(parts) > 1:
            src, tgt = parts[:2]
        else:
            src, tgt =  parts[0], ''
        data.append((src, tgt))
    log.info(f'Number of segments {len(data)}')
    word_lens = [(len(src.split()), len(tgt.split())) for src, tgt in data]
    word_len_ratios = [s / t if t > 0 else float('inf') for s, t in word_lens]
    low_wlr, high_wlr = get_extremes(word_len_ratios, n_stds)
    log.info(f'Word length ratios [{low_wlr:g}, {high_wlr:g}]')

    # char_lens = [(len(src.replace(' ', '')), len(src.replace(' ', ''))) for src, tgt in data]
    word_len_diffs = [s - t for s, t in word_lens]
    low_wld, high_wld = get_extremes(word_len_diffs, n_stds)
    log.info(f'Word count diffs  [{low_wld:g}, {high_wld:g}]')
    counts = ddict(lambda :ddict(int))
    counts['total']['total'] = len(data)
    for i, (src, tgt) in enumerate(data):
        src_len, tgt_len = word_lens[i]
        len_ratio, len_diff = word_len_ratios[i], word_len_diffs[i]
        checks = [('src_len',  min_len <= src_len <= max_len),
                   ('tgt_len', min_len <= tgt_len <= max_len),
                   ('len_ratio', low_wlr <= len_ratio <= high_wlr),
                   ('len_diff', low_wld <= len_diff <= high_wld),
                   ('urls', urls_alignment(src, tgt)),
                  ]
        is_good = all(val for n, val  in checks)
        for name, val in checks:
            counts[name]['good' if val else 'bad'] += 1

        optionals = []
        if digits >= 0:
            optionals += [('digits', digit_alignment(src, tgt, diff=digits))]
        if puncts >= 0:
            optionals += [('puncts', punctuation_alignment(src, tgt, diff=puncts))]
        is_good = is_good and all(val for n, val in optionals)
        for name, val in optionals:
            counts[name]['good' if val else 'bad'] += 1

        counts['total']['good' if is_good else 'bad'] += 1
        if (negate and not is_good) or (not negate and is_good):
            out.write(f'{src}\t{tgt}\n')
    log.info(f"Done. Wrote to {out}")
    log.info(format_table(counts, col_names=['good', 'bad']))


if __name__ == '__main__':
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('-i', '--inp', type=argparse.FileType('r'), default=sys.stdin,
                   help='SOURCE<tab>TARGET per line')
    p.add_argument('-o', '--out', type=argparse.FileType('w'), default=sys.stdout,
                   help='output same as input')
    p.add_argument('-ns', '--n-stds', type=float, default=1.5,
                   help='Number of standard deviations in length')
    p.add_argument('-ng', '--negate', action='store_true', default=False,
                   help='Negate to output mis aligned sentences instead of aligned sentences')
    p.add_argument('-d', '--digits', type=int, default=0,
                   help='Match is when the number of digit chars differ no more than this value.'
                        'Specifying a negative value disables it.')

    p.add_argument('-p', '--puncts', type=int, default=6,
                   help='Match is when the number of punctuations differ no more than this value.'
                        'Specifying a negative value disables it.')
    p.add_argument('-mx', '--max-len', type=int, default=100,
                   help='Match is when sentences are shorter than the specified value.')
    p.add_argument('-mn', '--min-len', type=int, default=1,
                   help='Match is when sentences are longer than the specified value.')
    args = vars(p.parse_args())
    main(**args)
