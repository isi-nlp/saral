#!/usr/bin/env python
# coding=UTF8

# Author = Thamme Gowda tg@isi.edu
# Date = March 09, 2018

import sys
import unicodedata as ud


def is_punct(tok):
    for ch in tok:
        if ud.category(ch).startswith('P'):
            return True
    return False


def cut_dnt_toks(inp, outp, template="DNT_%d"):
    """
    replaces DNT Tokens with templates
    :param inp: input file stream that reads line by line
    :param outp: output file stream
    :param template: template string for replacement. default is DNT_%d
    :return: None
    """
    def is_not_punct(x): return not is_punct(x)

    for line in inp:
        src_sent, tgt_sent = line.split('\t')

        common_toks = set(filter(is_not_punct, tgt_sent.lower().split()))\
                      & set(filter(is_not_punct, src_sent.lower().split()))
        dnt_toks = {}
        seq1, seq2 = [], []
        for src_tok in src_sent.split():
            lc_tok = src_tok.lower()
            out_tok = src_tok
            if lc_tok in common_toks:
                if lc_tok not in dnt_toks:
                    dnt_toks[lc_tok] = (len(dnt_toks) + 1, src_tok)
                pos, _ = dnt_toks[lc_tok]
                out_tok = template % pos
            seq1.append(out_tok)

        # Target
        for tgt_tok in tgt_sent.split():
            lc_tok = tgt_tok.lower()
            out_tok = tgt_tok
            if lc_tok in common_toks:
                assert lc_tok in dnt_toks  # already added during source seq copy
                pos, _ = dnt_toks[lc_tok]
                out_tok = template % pos
            seq2.append(out_tok)
        # DNT tokens
        seq3 = [tok for pos, tok in sorted(dnt_toks.values(), key=lambda x: x[0])]

        seq1, seq2, seq3 = ' '.join(seq1), ' '.join(seq2), ' '.join(seq3)
        outp.write('%s\t%s\t%s\n' % (seq1, seq2, seq3))


if __name__ == '__main__':

    if sys.version_info[0] < 3:
        raise Exception('Please run this on Python 3 or newer. (∵ I NEED UNICODE)')
    import argparse

    parser = argparse.ArgumentParser(description='Replaces copy words with template tokens in source and target of '
                                                 'parallel corpus.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--in', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input. Each line should have \'SRC_SEQ<tab>TGT_SEQ\'.  Source SEQ is source text '
                             ' and target SEQ is target text. ')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output. Each line will have \'SEQ1<tab>SEQ2<tab>SEQ3\'. '
                             'SEQ1 and SEQ2 will be SEQ1 and SEQ2 of inputs after replacements. '
                             'SEQ3 will have words words that are cut from inputs, each position will correspond to'
                             ' the suffix of template token. Example: DNT_1 template token in SEQ1 correspond to the'
                             ' first token in SEQ2')
    parser.add_argument('-t', '--template', type=str, default='DNT_%d', help='Template for tokens to be inserted')

    args = vars(parser.parse_args())
    cut_dnt_toks(args['in'], args['out'], template=args['template'])
