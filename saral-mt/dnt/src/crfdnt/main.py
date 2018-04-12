#!/usr/bin/env python

# Author = Thamme Gowda
# Created = April 07, 2018

"""
Command line interface to the tagger
"""
import argparse
import sys
import logging as log
import re
import pickle

from .utils import tag_src_iob
from .tagger import Featurizer, CRFTagger, CRFTrainer

log.basicConfig(level=log.INFO)


FEATS_SUFFIX = ".feats.pkl"
DELIM = "|+|"
TEMPLATE = 'DNT_%d'
RE_PATTERN = re.compile(r"DNT_(\d+)")


def prepare(inp, out, format, swap=False):

    def iob_tag():
        if format == 'conll':
            yield ()
        for rec in inp:
            src, tgt = rec.split('\t')
            if swap:
                tgt, src = src, tgt
            src, tgt = src.split(), tgt.split()
            tags = tag_src_iob(src, tgt)
            assert len(tags) == len(src)
            if format == 'src-tags':
                yield (' '.join(src), ' '.join(tags))
            elif format == 'tags':
                yield (' '.join(tags),)
            elif format == 'conll':
                yield from zip(src, tags)
                yield ('',)  # empty line at the end of sentence
            else:
                raise Exception(f'Unknown format requested: {format}')

    count = write_recs(iob_tag(), out)
    log.info(f"Wrote {count} records, format={format}")


def train(inp, model, context, verbose, bitext=False, **kwargs):
    featurizer = Featurizer(context)
    train_data = featurizer.featurize_parallel_set(inp) if bitext else featurizer.featurize_dataset(inp)
    train_data = list(train_data)

    with open(model + FEATS_SUFFIX, 'wb') as f:
        pickle.dump(featurizer, f)

    trainer = CRFTrainer(verbose=verbose)
    trainer.train_model(train_data, model, **kwargs)


def evaluate(inp, model, explain=False):

    tagger = CRFTagger(model)
    with open(model + FEATS_SUFFIX, 'rb') as f:
        featurizer = pickle.load(f)
    test_data = list(featurizer.featurize_dataset(inp))
    if explain:
        tagger.explain()
    tagger.evaluate(test_data)


def tag(inp, out, model):
    tagger = CRFTagger(model)
    with open(model + FEATS_SUFFIX, 'rb') as f:
        featurizer = pickle.load(f)
    data = featurizer.featurize_dataset(inp)
    y_seqs = ([' '.join(tagger.tag(xseq))] for xseq in data)
    write_recs(y_seqs, out)


def not_implemented(x):
    raise Exception('Not implemented %s' % x)


def write_recs(recs, outp):
    count = 0
    for rec in recs:
        line = '\t'.join(rec)
        outp.write(line)
        outp.write('\n')
        count += 1
    return count


def dnt_cut(inp, out, model):
    """
    Cuts DNT words from the text
    :param inp: stream of TEXT or SOURCE\\tTARGET records. The first column is ran against tagger to locate DNT words.
                when the second column exists, the DNT words found in first column will also be replaced
    :param out: stream that can consume output
    :param model: DNT tagger model
    :return:
    """
    tagger = CRFTagger(model)
    with open(model + FEATS_SUFFIX, 'rb') as f:
        featurizer = pickle.load(f)

    def _dnt_cut():
        for line in inp:
            line = line.strip()
            if not line:
                continue
            recs = line.split('\t')
            if len(recs) == 1:
                src, tgt = recs[0].split(), None
            elif len(recs) == 2:
                src, tgt = recs
                src, tgt = src.split(), tgt.split()
            else:
                raise Exception("Input should be either SRC or SRC\\tTGT")
            tags = tagger.tag(featurizer.featurize_seq(src))
            assert len(tags) == len(src)
            src_cut, dnt_toks = [], []
            last_tag = None
            for word, tag in zip(src, tags):
                if tag == 'O':
                    src_cut.append(word)
                else:
                    if tag.startswith('B-') or last_tag == 'O':
                        # last == O and this tag!=B is an erroneous transition
                        dnt_toks.append([word])
                        src_cut.append(TEMPLATE % len(dnt_toks))
                    else:
                        # extend the last one
                        dnt_toks[-1].append(word)
                last_tag = tag

            tgt_cut = []
            if tgt:
                idx = 0
                while idx < len(tgt):
                    dnt_idx = 0
                    for jdx, dnts in enumerate(dnt_toks):
                        if tgt[idx: idx + len(dnts)] == dnts:
                            dnt_idx = jdx + 1
                            idx += len(dnts)
                            break
                    if dnt_idx:
                        tgt_cut.append(TEMPLATE % dnt_idx)
                    else:
                        tgt_cut.append(tgt[idx])
                        idx += 1
            dnt_toks = [DELIM.join(x) for x in dnt_toks]
            rec = [' '.join(src_cut), ' '.join(dnt_toks)]
            if tgt:
                rec.insert(1, ' '.join(tgt_cut))
            yield rec
    write_recs(_dnt_cut(), out)


def dnt_paste(inp, out, ignore_errors=True):
    """
    restores DNT words back into the text
    :param inp: stream of text \\t dnt_words records
    :param out: stream to consume output
    :param ignore_errors: Should the errors (such as out of bound DNT_%d)  be ignored?
    :return:
    """

    def _dnt_paste():
        for line in inp:
            text, dnt_words = line.split('\t')
            text, dnt_words = text.split(), dnt_words.split()
            dnt_words = [x.replace(DELIM, ' ') for x in dnt_words]
            res = []
            for word in text:
                out_word = word
                match = RE_PATTERN.match(word)
                if match:
                    pos = int(match.groups()[0])
                    assert pos > 0
                    if pos <= len(dnt_words):
                        out_word = dnt_words[pos - 1]  # DNT index starts from 1
                    elif not ignore_errors:
                        raise Exception('Cant find replacement. DNT Index=%d, DNT Words=%s' % (pos, dnt_words))
                res.append(out_word)
            yield (' '.join(res),)
    write_recs( _dnt_paste(), out)


def get_arg_parser():
    # TODO: reorganize these parsers as parent-child, avoid redefinition of arguments
    parser = argparse.ArgumentParser(description='Do Not Translate (DNT) tagger',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sub_parsers = parser.add_subparsers(help='tasks', dest='task')
    sub_parsers.required = True
    prep_arg_parser = sub_parsers.add_parser('prepare', help='Prepare training data from parallel MT corpus',
                                             formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    train_arg_parser = sub_parsers.add_parser('train', help='Train a CRF DNT Tagger model',
                                              formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    tag_arg_parser = sub_parsers.add_parser('tag', help='Tag DNT words using CRF DNT model',
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    eval_arg_parser = sub_parsers.add_parser('eval', help='Evaluate a CRF DNT model',
                                             formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    cut_arg_parser = sub_parsers.add_parser('dnt-cut', help='Cut DNT words',
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    paste_arg_parser = sub_parsers.add_parser('dnt-paste', help='Paste DNT words',
                                              formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Preparation
    prep_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream. Default is STDIN. When specified, it should be a file path.
             Data Format=SRC_SEQUENCE\\tTGT_SEQUENCE per line''')

    prep_arg_parser.add_argument('-o', '--out', default=sys.stdout, type=argparse.FileType('w'), help='''
            Output stream. Default is STDOUT. When specified, it should be a file path. 
            Data Format depends on the (-f, --format) argument''')
    prep_arg_parser.add_argument('-s', '--swap', action='store_true', help='Swap the columns in input')
    prep_arg_parser.add_argument('-f', '--format', choices=['src-tags', 'tags', 'conll'], default='src-tags', type=str,
                                 help='''Format of output: `src-tag`: output SOURCE\\tTAG per line.
                                   `tag`: output just TAG sequence per line.
                                   `conll`: output in CoNLL 2013 NER format.''')

    # Train
    train_arg_parser.add_argument('model', type=str, help='''Path to store model file''')
    train_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream of Training data. Default is STDIN. When specified, it should be a file path.
            Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line by default
            Data Format=SRC_SEQUENCE\\tTGT_SEQUENCE i.e. parallel bitext when --bitext is used''')
    train_arg_parser.add_argument('-c', '--context', type=int, default=2, help="Context in sequence.")
    train_arg_parser.add_argument('-bt', '--bitext', action='store_true', help="input is a parallel bitext")
    train_arg_parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose")

    # Tagging
    tag_arg_parser.add_argument('model', type=str, help='''Path to the stored model file''')
    tag_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream of data. Default is STDIN. When specified, it should be a file path.
             Data Format=one SRC_SEQUENCE per line''')
    tag_arg_parser.add_argument('-o', '--out', default=sys.stdout, type=argparse.FileType('w'), help='''
        Output stream. Default is STDOUT. When specified, it should be a file path. 
        Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line.''')

    # Evaluation
    eval_arg_parser.add_argument('model', type=str, help='''Path to the stored model file''')
    eval_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream of Test data. Default is STDIN. When specified, it should be a file path. 
            Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line''')
    eval_arg_parser.add_argument('-e', '--explain', action='store_true',
                                 help='Explain top state transitions and weights')

    # Cut task
    cut_arg_parser.add_argument('model', type=str, help='''Path to the stored model file''')
    cut_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
                Input stream of data. Default is STDIN. When specified, it should be a file path.
                 Data Format=one SRC_SEQUENCE per line or SRC\\tTGT sequence per line.''')
    cut_arg_parser.add_argument('-o', '--out', default=sys.stdout, type=argparse.FileType('w'), help='''
            Output stream. Default is STDOUT. When specified, it should be a file path''')

    # Paste task
    paste_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
                Input stream of data. Default is STDIN. When specified, it should be a file path.
                 Data Format=one TEXT\\tDNT_WORD sequence per line.''')
    paste_arg_parser.add_argument('-o', '--out', default=sys.stdout, type=argparse.FileType('w'), help='''
        Output stream. Default is STDOUT. When specified, it should be a file path''')
    return parser


def main():
    assert sys.version_info[0] >= 3
    args = get_arg_parser().parse_args()
    tasks = {
        'train': train,
        'prepare': prepare,
        'tag': tag,
        'eval': evaluate,
        'dnt-cut': dnt_cut,
        'dnt-paste': dnt_paste,
    }
    args = vars(args)
    task = args['task']
    del args['task']
    tasks.get(task, not_implemented)(**args)


if __name__ == '__main__':
    main()
