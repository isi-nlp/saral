#!/usr/bin/env python

# Author = Thamme Gowda tg@isi.edu
# Date = March 07, 2018

import sys
from collections import namedtuple

PHRASE_DELIM = "|+|"
Segment = namedtuple('Segment', ['toks', 'tag'])


def dnt_cut(text, tags, dnt_tag='N', template="DNT_%d"):
    """
     replaces DNT Tokens with templates
    :param text: list of tokens from input text
    :param tags: list of tags for each input token
    :param template: template string for replacement. default is DNT_%d
    :param dnt_tag: tag that means DNT. default is N
    :return: (text seq after replacement, DNT sequence)
    """
    assert len(text) == len(tags), 'words and tags must match! words=%d, tags=%d' % (len(text), len(tags))
    # Step : groups tokens into segments based on similar tag
    segments = []
    for tok, tag in zip(text, tags):
        if segments and tag == segments[-1].tag:
            # extend the last segment
            segments[-1].toks.append(tok)
        else: # initialize or create a new segment
            segments.append(Segment([tok], tag))

    # Step: DNTs are replaced with templates and non DNTs are copied
    seq1, seq2 = [], []
    phrase_mem = {}     # if same segment appear multiple times, remember them
    for seg in segments:
        if seg.tag == dnt_tag:
            phrase = PHRASE_DELIM.join(seg.toks)
            if phrase in phrase_mem:
                out_word = phrase_mem[phrase_mem]
            else:
                out_word = template % (len(seq2) + 1)
                seq2.append(phrase)
            seq1.append(out_word)
        else:
            seq1.extend(seg.toks)
    return ' '.join(seq1), ' '.join(seq2)


def run(inp, outp, template="DNT_%d", dnt_tag='N'):
    """
    replaces DNT Tokens with templates
    :param inp: input file stream that reads line by line
    :param outp: output file stream
    :param template: template string for replacement. default is DNT_%d
    :param dnt_tag: tag that means DNT. default is N
    :return: None
    """
    for line in inp:
        text, tags = line.split('\t')
        text, tags = text.split(), tags.split()
        seq1, seq2 = dnt_cut(text, tags, dnt_tag, template)
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
    parser.add_argument('-t', '--template', type=str, default='DNT_%d', help='Template for tokens to be inserted')
    parser.add_argument('-d', '--dnt-tag', type=str, default='N', help='Tag that means do not translate')

    args = vars(parser.parse_args())
    run(args['in'], args['out'], template=args['template'], dnt_tag=args['dnt_tag'])
