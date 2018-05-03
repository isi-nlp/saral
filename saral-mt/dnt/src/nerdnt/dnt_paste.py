#!/usr/bin/env python
# Author Thamme Gowda
# Created on : May 2, 2018

import sys
import re
import json
import logging as log

log.basicConfig(level=log.INFO)
DNT_PATTERN = re.compile(r"^DNT_(.+)_(\d+)$")


def restore_dnt(text, dnt_words):
    res = []
    err_count = 0
    for word in text:
        out_word = word
        match = DNT_PATTERN.match(word)
        if match:
            dnt_type, pos = match.groups()[0], int(match.groups()[1])
            assert pos > 0
            if dnt_type in dnt_words and pos <= len(dnt_words[dnt_type]):
                out_word = dnt_words[dnt_type][pos - 1]  # DNT index starts from 1
            else:
                err_count += 1
                log.debug(f'Could not restore {word} : {dnt_type} {pos}')
                out_word = ''
        res.append(out_word)
    return ' '.join(res), err_count


def restore_all(inp, outp):
    """
    Restores DNT Tokens back to the sequence.
    :param inp: input file stream that reads line by line
    :param outp: output file stream
    :return: None
    """
    total_err_count = 0
    for line in inp:
        text, dnt_words = line.split('\t')
        text, dnt_words = text.split(), json.loads(dnt_words)
        line, err_count = restore_dnt(text, dnt_words)
        outp.write('%s\n' % line)
        total_err_count += err_count
    log.warning(f'Found {total_err_count} errors while restoring DNTs')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Replaces DNT words with template words from the source',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--in', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input. Each line should have \'SEQ1<tab>SEQ2\'.  SEQ1 is sequence of words'
                             ' separated by regular space and SEQ2 should be DNT tags separated by regular spaces'
                             ' where \'N\' indicates DNT(copy) word.')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output. Each line will have SEQ1 of input after pasting DNT words. ')

    args = vars(parser.parse_args())
    restore_all(args['in'], args['out'])
