#!/usr/bin/env python
# coding=UTF8

# Author = Thamme Gowda tg@isi.edu
#
# Version 0: March 09, 2018
# Version 1: April 05, 2018


import sys
import unicodedata as ud


def is_punct(tok):
    for ch in tok:
        if ud.category(ch).startswith('P'):
            return True
    return False


def is_not_punct(x):
    return not is_punct(x)


def make_grams(seq, max_gram=None):
    """
    Creates n-grams from the sequence

    :param seq: input sequence
    :param max_gram: max n-gram size, default=sequence length
    :return: set of n-grams
    """
    grams = set()
    if max_gram is None:
        max_gram = len(seq)
    for gram_len in range(1, max_gram + 1):
        for start in range(0, len(seq) - gram_len + 1):
            gram = tuple(seq[start: start + gram_len])
            grams.add(gram)
    return grams


def cut_dnt_toks(src_sent, tgt_sent, template="DNT_%d", phrase_join='|+|'):
    """
    replaces DNT Tokens with templates
    :param src_sent: Source sentence
    :param tgt_sent: target Sentence
    :param template: replacement template, DNT_%d
    :param phrase_join: delimter used to join tokens within a phrase
    :return: (src_seq, tgt_seq, dnt_seq) after replacements
    """
    """
    Goal:
        Group adjacent DNT tokens into one big DNT phrase, and use only one DNT template token for that phrase.

    ALGORITHM:
        Greedily group adjacent sequence of DNTs 
        1. set of common tokens between source and target, ignore the case
        2. Mark each source and target token as DNT (True if they are in the set in Step 1) 
        3. Segment each sequence into groups of DNT tokens,
            and create n-grams of each segments, upto their maximum length. Create an indexed set for fast lookup
        4. Lets do the target side first. 
            a. segment the tokens by grouping adjacent DNTs together. Begin with the max length segment. 
            b. If this segment exists in the set created in Step 3, cool!
             Mark it as one big DNT phrase, assign a number to it. that number will help create a template DNT_%d
             advance to the next segment (i.e. skip number of words = len of segment) 
            c. If max length segment doesnt exist in set, then ignore the last token. repeat 4.b and 4.c.
                the worst case will be unigram token and  
        5. On the source side,
            do the similar process as step 4. 
            i.e. begin with max segment and  keep shrinking from right; 
            stop when an n-gram, with DNT_%d was already assigned in step 4.b
    """
    # Step 1
    common_toks = set(filter(is_not_punct, tgt_sent.lower().split())) & \
        set(filter(is_not_punct, src_sent.lower().split()))
    # Step 2
    src = [(tok, tok.lower() in common_toks) for tok in src_sent.split()]
    tgt = [(tok, tok.lower() in common_toks) for tok in tgt_sent.split()]

    # Step 3
    src_dnt_grams = set()
    start = -1  # -1 not grouping, >=0 means grouping from that index
    for cur, (tok, dnt_flag) in enumerate(src):
        if dnt_flag:
            if start == -1:  # start of a new group
                start = cur
        else:
            if start > -1:  # end the previous group
                sub_seq = [x[0].lower() for x in src[start: cur]]
                src_dnt_grams.update(make_grams(sub_seq))
                start = -1
    if start > -1:  # left over at the end
        sub_seq = [x[0].lower() for x in src[start:]]
        src_dnt_grams.update(make_grams(sub_seq))

    # Step 4
    dnt_phrases = {}
    original_case = {}
    tgt_res = []
    cur = 0

    while cur < len(tgt):
        handled = False
        tok, dnt_flag = tgt[cur]
        if not dnt_flag:
            tgt_res.append(tok)
            cur += 1
            handled = True
        else:
            # look ahead => Greediness => go for max segment
            end = cur + 1
            while end < len(tgt) and tgt[end][1]:
                end += 1
            # keep shrinking right side until we find a gram in the set created in step 3
            while end > cur:
                gram = tuple(x[0].lower() for x in tgt[cur: end])

                if gram in src_dnt_grams:
                    dnt_idx = dnt_phrases.get(gram, len(dnt_phrases) + 1)
                    dnt_phrases[gram] = dnt_idx
                    original_case[gram] = tuple(x[0] for x in tgt[cur: end])
                    tgt_res.append(template % dnt_idx)
                    cur = end
                    handled = True
                    break
                end -= 1    # leave the last one and try again
        assert handled, 'Every token should be handled. what to do with %s ? ' % tok

    # Step 5
    src_res = []
    cur = 0
    while cur < len(src):
        handled = False
        tok, dnt_flag = src[cur]
        if not dnt_flag:
            src_res.append(tok)
            cur += 1
            handled = True
        else:
            # look ahead => Greediness => go for max segment
            end = cur + 1
            while end < len(src) and src[end][1]:
                end += 1
            # keep shrinking right side until we find a gram in the set created in step 3
            while end > cur:
                gram = tuple(x[0].lower() for x in src[cur: end])
                if gram in dnt_phrases:
                    src_res.append(template % dnt_phrases[gram])
                    cur = end
                    handled = True
                    break
                end -= 1
        assert handled, 'Each token should handled. what to do with %s ? ' % tok

    # DNT tokens -- restore the original case ( from the target side)
    dnt_phrases = dict((original_case[lc_phrase], index) for lc_phrase, index in dnt_phrases.items())
    phrases = [phrase for phrase, pos in sorted(dnt_phrases.items(), key=lambda x: x[0], reverse=True)]
    dnt_seq = [phrase_join.join(phrase) for phrase in phrases]
    return src_res, tgt_res, dnt_seq


def run(inp, outp, template="DNT_%d"):
    """
    replaces DNT Tokens with templates
    :param inp: input file stream that reads line by line
    :param outp: output file stream
    :param template: template string for replacement. default is DNT_%d
    :return: None
    """
    for line in inp:
        src_sent, tgt_sent = line.split('\t')
        src_seq, tgt_seq, dnt_seq = cut_dnt_toks(src_sent, tgt_sent, template)
        seq1, seq2, seq3 = ' '.join(src_seq), ' '.join(tgt_seq), ' '.join(dnt_seq)
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
    run(args['in'], args['out'], template=args['template'])
