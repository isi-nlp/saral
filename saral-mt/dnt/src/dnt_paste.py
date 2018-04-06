#!/usr/bin/env python

# Author = Thamme Gowda tg@isi.edu
# Date = March 08, 2018

import sys
import re

PHRASE_DELIM = '|+|'


def restore_dnt(text, dnt_words, ignore_errors, dnt_pattern):
    """
    restores DNT tokens
    :param text: text with template tokens
    :param dnt_words:  DNT tokens sequence
    :param ignore_errors: Should any out of bound erros be ignored?
    :param pattern:
    :return:
    """

    res = []
    for word in text:
        out_word = word
        match = dnt_pattern.match(word)
        if match:
            pos = int(match.groups()[0])
            assert pos > 0
            if pos <= len(dnt_words):
                out_word = dnt_words[pos - 1]  # DNT index starts from 1
            elif not ignore_errors:
                raise Exception('Cant find replacement. DNT Index=%d, DNT Words=%s' % (pos, dnt_words))
        res.append(out_word)
    return ' '.join(res)


def restore_all(inp, outp, dnt_pattern=r"DNT_(\d+)", ignore_errors=False, phrase_delim=None):
    """
    Restores DNT Tokens back to the sequence.
    :param inp: input file stream that reads line by line
    :param outp: output file stream
    :param dnt_pattern: regex pattern for matching DNT template tokens, default=DNT_(\d+)
    :param ignore_errors: ignore errors such as index is larger than token array. default=False
    :param phrase_delim: delimiter to expand phrases
    :return: None
    """
    pattern = re.compile(dnt_pattern)
    for line in inp:
        text, dnt_words = line.split('\t')
        text, dnt_words = text.split(), dnt_words.split()
        line = restore_dnt(text, dnt_words, ignore_errors, pattern)
        if phrase_delim:
            line = line.replace(phrase_delim, ' ')
        outp.write('%s\n' % line)


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
    parser.add_argument('-t', '--template', type=str, default=r'DNT_(\d+)', help='Regex Pattern for matching DNT tokens')
    parser.add_argument('-ie', '--ignore-errors', default=False, action='store_true',
                        help='Ignore replacement errors such as index out of bound.')

    parser.add_argument('-pd', '--phrase-delim', type=str, default=PHRASE_DELIM,
                        help='Phrase delimiter for expanding phrases')

    args = vars(parser.parse_args())
    restore_all(args['in'], args['out'], dnt_pattern=args['template'], ignore_errors=args['ignore_errors'],
                phrase_delim=args['phrase_delim'])
