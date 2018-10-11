#!/usr/bin/env python
#
# Author: Thamme Gowda [tg at isi dot edu] 
# Created: 10/10/18

import argparse
import sys
import logging as log
import unicodedata as ud

log.basicConfig(level=log.INFO)


def is_punct(tok):
    """
    :param tok: token
    :return: True if token is made of only punctuation characters; False otherwise
    """
    for x in tok:
        if ud.category(x)[0] != 'P':
            return False
    return True


def asr_like_rec_v1(text):
    """
    first version of ASR Like
    :param text: input text
    :return: asr like text
    """
    # lowercase text
    # remove punctuations
    text = text.lower()
    toks = text.split()
    toks = [tok for tok in toks if not is_punct(tok)]
    return ' '.join(toks)


def make_asr_like(inp, tsv_mode=False, rules=asr_like_rec_v1):
    for line in inp:
        if tsv_mode:
            rec_id, text = line.split('\t')
            rec_id, text = rec_id.strip(), text.strip()
        else:
            rec_id, text = None, line.strip()
        out_text = rules(text)
        yield (rec_id, out_text) if tsv_mode else out_text


def write_out(recs, out, tsv_mode=False):
    count = 0
    for rec in recs:
        line = '\t'.join(rec) if tsv_mode else rec
        out.write(line)
        out.write('\n')
        count += 1
    log.info(f"Wrote {count} records to {out.name}")


def main():
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('-i', '--inp', type=argparse.FileType('r'), default=sys.stdin,
                   help='Input file path')
    p.add_argument('-o', '--out', type=argparse.FileType('w'), default=sys.stdout,
                   help='Output file path')
    p.add_argument('-t', '--tsv', dest='tsv_mode', action='store_true', default=False,
                   help='Input is a TSV data with ID \\t Text')
    args = vars(p.parse_args())
    asr_like_recs = make_asr_like(args['inp'], args['tsv_mode'])
    write_out(asr_like_recs, args['out'], args['tsv_mode'])


if __name__ == '__main__':
    main()

