#!/usr/bin/env python3

import argparse
import sys
from collections import defaultdict as ddict
import logging as log

log.basicConfig(level=log.INFO)


def read_docs(fptr):
    """
    returns list of docs.
    format = [(doc1, [(sent1, [words..]), ...]
              ]), ...]
    """
    docs = []
    last_doc = None
    for line in fptr:
        assert '\t' in line, line
        id, text = line.split('\t')
        text = text.split()
        doc_id,sent_id = id.split('_')
        if doc_id != last_doc:
            docs.append((doc_id, []))
        docs[-1][1].append((sent_id, text))
        last_doc = doc_id
    return docs


def merge_doc(orig, split, inp, doc_id=None):

    orig_wc = sum([len(ws) for sid, ws in orig])
    split_wc = sum([len(ws) for sid, ws in orig])
    if orig_wc != split_wc:
        raise Exception("Alignment not possible, DOCID : %s" % doc_id)
    if len(split) != len(inp):
        raise Exception("Alignment not possible, DOCID : %s, splits:%d, input:%d" % (doc_id, len(split), len(inp)))
    # FIXME: merge
    oi, si = 0, 0
    res = []
    while oi < len(orig) and si < len(split):
        buff = []
        o_id, o_toks = orig[oi]
        i = si
        while len(buff) < len(o_toks) and i < len(split) and buff != o_toks:
            buff.extend(split[i][1])
            i += 1
        if buff == o_toks:
            res_toks = [tok for _, toks in inp[si:i] for tok in toks]
            res.append((o_id, ' '.join(res_toks)))
            oi += 1 # go to next
            si = i  # jump to next
        else:
            raise Exception('Cant join doc %s :: SRC: %s, SRCSPLIT:%s' % (doc_id, orig[oi], buff))

    return res

def merge(src, ssplit, inp, out):
    log.info("Reading src")
    srcs = read_docs(src)
    log.info("Reading ssplit")
    ssplits = read_docs(ssplit)
    log.info("Reading inp")
    inps = read_docs(inp)
    assert len(srcs) == len(ssplits) == len(inps), "Doc count should match.. SRC:%s SSPLIT:%s INPUT:%s" % (len(srcs), len(ssplits), len(inps))
    for orig, split, rec in zip(srcs, ssplits, inps):
        assert orig[0] == split[0] == rec[0], 'Doc Id should match: Src:%s SSplit:%s Inp:%s' % (orig[0], split[0], out[0])
        doc_id = orig[0]
        out_rec = merge_doc(orig[1], split[1], rec[1], doc_id=doc_id)
        for sent_id, sent in out_rec:
            out.write('%s_%s\t%s\n' % (doc_id, sent_id, sent))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-src', help='Source File before Splitting.'
                   ' Value should be a TSV file with ID\\tTEXT', required=True,
                   type=argparse.FileType('r'))
    p.add_argument('-ssplit', help='Source File After Splitting.'
                   'Value should be a TSV file with ID\\tTEXT', required=True,
                   type=argparse.FileType('r'))
    p.add_argument('-inp', help='MT output of -sssplit which needs to be combined.'
                   'Value should be a TSV file with ID\\tTEXT', required=True,
                   type=argparse.FileType('r'))
    p.add_argument('-out', help='MT output unsplit', required=False,
                   type=argparse.FileType('w'), default=sys.stdout)
    args = vars(p.parse_args())
    merge(**args)
