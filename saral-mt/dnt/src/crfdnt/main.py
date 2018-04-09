#!/usr/bin/env python

# Author = Thamme Gowda
# Created = April 07, 2018

"""
Command line interface to the tagger
"""
import argparse
import sys
import logging as log

from .utils import tag_src_iob
from .tagger import Featurizer, CRFTagger, CRFTrainer

log.basicConfig(level=log.INFO)


def prepare(inp, out, format, **args):

    def iob_tag():
        if format == 'conll':
            yield ()
        for rec in inp:
            src, tgt = rec.split('\t')
            if args.get('swap'):
                tgt, src = src, tgt
            src, tgt = src.split(), tgt.split()
            tags = tag_src_iob(src, tgt)
            if format == 'src-tags':
                yield (' '.join(src), ' '.join(tags))
            elif format == 'tags':
                yield (' '.join(tags),)
            elif format == 'conll':
                yield from zip(src, tgt)
                yield ('',)  # empty line at the end of sentence
            else:
                raise Exception(f'Unknown format requested: {format}')

    count = write_recs(iob_tag(), out)
    log.info(f"Wrote {count} records, format={format}")


def train(inp, model, context, verbose, **kwargs):
    if 'task' in kwargs:
        del kwargs['task']
    featurizer = Featurizer(context)
    train_data = list(featurizer.featurize_dataset(inp))
    trainer = CRFTrainer(verbose=verbose)
    trainer.train_model(train_data, model, **kwargs)


def evaluate(inp, model, context, **kwargs):
    featurizer = Featurizer(context)
    tagger = CRFTagger(model)
    test_data = list(featurizer.featurize_dataset(inp))
    if kwargs.get('explain'):
        tagger.explain()
    tagger.evaluate(test_data)


def tag(inp, out, model, context, **kwargs):
    featurizer = Featurizer(context)
    tagger = CRFTagger(model)
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


def get_arg_parser():
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
            Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line''')
    train_arg_parser.add_argument('-c', '--context', type=int, default=2, help="Context in sequence.")
    train_arg_parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose")

    # Tagging
    tag_arg_parser.add_argument('model', type=str, help='''Path to the stored model file''')
    tag_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream of data. Default is STDIN. When specified, it should be a file path.
             Data Format=one SRC_SEQUENCE per line''')
    tag_arg_parser.add_argument('-o', '--out', default=sys.stdout, type=argparse.FileType('w'), help='''
        Output stream. Default is STDOUT. When specified, it should be a file path. 
        Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line.''')
    tag_arg_parser.add_argument('-c', '--context', type=int, default=2, help="Context in sequence.")

    # Evaluation
    eval_arg_parser.add_argument('model', type=str, help='''Path to the stored model file''')
    eval_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream of Test data. Default is STDIN. When specified, it should be a file path. 
            Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line''')
    eval_arg_parser.add_argument('-c', '--context', type=int, default=2, help="Context in sequence.")
    eval_arg_parser.add_argument('-e', '--explain', action='store_true',
                                 help='Explain top state transitions and weights')

    return parser


def main():
    assert sys.version_info[0] >= 3
    args = get_arg_parser().parse_args()
    tasks = {
        'train': train,
        'prepare': prepare,
        'tag': tag,
        'eval': evaluate
    }
    tasks.get(args.task, not_implemented)(**vars(args))


if __name__ == '__main__':
    main()


