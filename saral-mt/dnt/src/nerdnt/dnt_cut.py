#!/usr/bin/env python

# Author : Thamme Gowda
# Created on : May 2, 2018
import sys
import json

from ner import NER
from collections import defaultdict as ddict


def project_tags(seq1, seq1_tags, seq2, other_tag='O', overwrite_tag='MISC'):
    """
    Finds common tokens between seq1 and seq2, and projects tags of seq1 to seq2
    :param seq1: First sequence that has tags
    :param seq1_tags: tags of first sequence
    :param seq2: second sequence that needs to have tags projected to
    :param other_tag: Tag name for non-common tokens
    :param overwrite_tag: if a common token happen to have `other_tag`, then instead use this tag as final one
    :return: sequence of tags for sequence2
    """
    assert len(seq1) == len(seq1_tags), f'Cant match tags {seq1} {seq1_tags}'
    seq1_tag_lookup = dict(zip([x.lower() for x in seq1], seq1_tags))
    # seq2_tags = [seq1_tag_lookup.get(tok.lower(), other_tag) for tok in seq2]
    seq2_tags = []
    for tok in seq2:
        norm_tok = tok.lower()
        tag = other_tag
        if norm_tok in seq1_tag_lookup:  # DNT word
            tag = seq1_tag_lookup[norm_tok]
            if tag == other_tag:    # DNT word tagged as `other` by the previous tagger
                tag = overwrite_tag
        seq2_tags.append(tag)
    return seq2_tags


def replace_all(inp, model):
    ner = NER(model)
    for line in inp:
        src, tgt = line.strip().split('\t')
        src = src.split()
        tgt, tgt_tags = ner.tag(tgt, other_tag='O')
        src_tags = project_tags(tgt, tgt_tags, src)
        memory = ddict(list)
        src_out = []
        tok_to_template = {}
        for i, (tok, tag) in enumerate(zip(src, src_tags)):
            if tag == 'O':
                src_out.append(tok)
            else:
                if i > 0 and tag == src_tags[i-1]:
                    # same as previous one, expand the previous DNT phrase
                    memory[tag][-1].append(tok)
                else:
                    # create a new DNT phrase
                    memory[tag].append([tok])
                    src_out.append('DNT_%s_%d' % (tag, len(memory[tag])))
                tok_to_template[tok.lower()] = src_out[-1]
        tgt_out = []
        for tok in tgt:
            tok_out = tok_to_template.get(tok.lower(), tok)
            if tgt_out and tok_out.startswith('DNT_') and tgt_out[-1] == tok_out:
                continue    # part of a continuing DNT phrase
            else:
                tgt_out.append(tok_out)
        for phrases in memory.values():
            for i, words in enumerate(phrases):
                phrases[i] = ' '.join(words)
        yield ' '.join(src_out), ' '.join(tgt_out), json.dumps(memory)


def run(inp, outp, model):
    recs = replace_all(inp, model)
    for rec in recs:
        outp.write('\t'.join(rec))
        outp.write('\n')


if __name__ == '__main__':
    if sys.version_info[0] < 3:
        raise Exception('Please run this on Python 3 or newer. (∵ I NEED UNICODE)')
    import argparse

    parser = argparse.ArgumentParser(description='Replaces copy words with template tokens in source and target of '
                                                 'parallel corpus.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--in', dest='inp', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input. Each line should have \'SRC_SEQ<tab>TGT_SEQ\'.  Source SEQ is source text '
                             ' and target SEQ is target text. ')
    parser.add_argument('-o', '--out', dest='outp', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output. Each line will have \'SEQ1<tab>SEQ2<tab>SEQ3\'. '
                             'SEQ1 and SEQ2 will be SEQ1 and SEQ2 of inputs after replacements. '
                             'SEQ3 will have words words that are cut from inputs, each position will correspond to'
                             ' the suffix of template token. Example: DNT_1 template token in SEQ1 correspond to the'
                             ' first token in SEQ2')
    parser.add_argument('-m', '--model', dest='model', default='en_core_web_lg', type=str,
                        help='Spacy Model for NER. Example: en_core_web_sm, en_core_web_md, en_core_web_lg etc')
    run(**vars(parser.parse_args()))