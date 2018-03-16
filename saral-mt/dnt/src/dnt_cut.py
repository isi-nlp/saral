#!/usr/bin/env python

# Author = Thamme Gowda tg@isi.edu
# Date = March 07, 2018

import sys


def cut_dnt_toks(inp, outp, max_toks=200, template="DNT_%d", dnt_tag='N'):
    """
    replaces DNT Tokens with templates
    :param inp: input file stream that reads line by line
    :param outp: output file stream
    :param max_toks: upper bound on number of tokens to replace. default is 200
    :param template: template string for replacement. default is DNT_%d
    :param dnt_tag: tag that means DNT. default is N
    :return: None
    """
    for line in inp:
        text, tags = line.split('\t')
        text, tags = text.split(), tags.split()
        assert len(text) == len(tags), 'words and tags must match!'
        seq1, seq2 = [], []
        for word, tag in zip(text, tags):
            out_word = word
            if tag == dnt_tag and len(seq2) < max_toks:
                out_word = template % (len(seq2) + 1)
                seq2.append(word)
            seq1.append(out_word)
        seq1, seq2 = ' '.join(seq1), ' '.join(seq2)
        outp.write('%s\t%s\n' % (seq1, seq2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Replaces DNT words with template words from the source',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--in', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input. Each line should have \'SEQ1<tab>SEQ2\'.  SEQ1 is sequence of words'
                             ' separated by regular space and SEQ2 should be DNT tags separated by regular spaces'
                             ' where \'N\' indicates DNT(copy) word. Number of items in both should match.')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output. Each line will have \'SEQ1<tab>SEQ2\'. SEQ1 is SEQ1 of input after replacements. '
                             'SEQ2 will have words words that are cut from source, each position will correspond to'
                             ' the suffix of template token. Example: DNT_1 template token in SEQ1 correspond to the'
                             ' first token in SEQ2')
    parser.add_argument('-m', '--max-toks', type=int, default=200, help='Max DNT tokens per record')
    parser.add_argument('-t', '--template', type=str, default='DNT_%d', help='Template for tokens to be inserted')
    parser.add_argument('-d', '--dnt-tag', type=str, default='N', help='Tag that means do not translate')

    args = vars(parser.parse_args())
    cut_dnt_toks(args['in'], args['out'], max_toks=args['max_toks'], template=args['template'], dnt_tag=args['dnt_tag'])
