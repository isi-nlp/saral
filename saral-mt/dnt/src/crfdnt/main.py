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
import json
from .utils import tag_src_iob, dnt_tag_toks, evaluate_multi_class, cut_dnt_bio, cut_dnt_groups
from .tagger import Featurizer, CRFTagger, CRFTrainer

log.basicConfig(level=log.INFO)

FEATS_SUFFIX = ".feats.pkl"
DELIM = "|+|"
TEMPLATE = 'DNT_%d'
RE_PATTERN = re.compile(r"^DNT(_(.+))?_(\d+)$")


def prepare(inp, out, format, swap=False, ner_model=None):

    def iob_tag():
        if format == 'conll':
            yield ()
        ner = None
        if ner_model:
            from .ner import NER
            ner = NER(ner_model)

        for rec in inp:
            if '\t' not in rec:
                raise Exception(f'Invalid record: cant split:: {rec}')
            src, tgt = rec.split('\t')
            if swap:
                tgt, src = src, tgt
            src, tgt = src.split(), tgt.split()
            if format == 'TN':
                tags = ['N' if tag else 'T' for tok, tag in dnt_tag_toks(src, tgt)]
                yield (' '.join(tags),)
            else:
                if ner:
                    tgt, tgt_tags, src, src_tags = ner.tag_and_project(tgt, src)
                else:
                    src_tags = tag_src_iob(src, tgt)
                assert len(src_tags) == len(src)
                if format == 'src-tags':
                    yield (' '.join(src), ' '.join(src_tags))
                elif format == 'tags':
                    yield (' '.join(src_tags),)
                elif format == 'conll':
                    yield from zip(src, src_tags)
                    yield ('',)  # empty line at the end of sentence
                else:
                    raise Exception(f'Unknown format requested: {format}')

    count = write_recs(iob_tag(), out)
    log.info(f"Wrote {count} records, format={format}")


def train(inp, model, context, verbose, bitext=False, no_memorize=False, ner_model=None, **kwargs):
    featurizer = Featurizer(context, memorize=not no_memorize, ner_model=ner_model)
    train_data = featurizer.featurize_parallel_set(inp) if bitext else featurizer.featurize_dataset(inp)
    trainer = CRFTrainer(verbose=verbose)
    trainer.train_model(train_data, model, **kwargs)

    with open(model + FEATS_SUFFIX, 'wb') as f:
        pickle.dump(featurizer, f)


def evaluate_model(inp, model, explain=False):

    tagger = CRFTagger(model)
    with open(model + FEATS_SUFFIX, 'rb') as f:
        featurizer = Featurizer.load(f)
    test_data = list(featurizer.featurize_dataset(inp))
    if explain:
        tagger.explain()
    tagger.evaluate(test_data)


def evaluate_result(inp):
    recs = (line.strip().split('\t') for line in inp)
    recs = ((pred.split(), gold.split()) for pred, gold in recs)
    evaluate_multi_class(lambda x: x, recs, do_print=True)


def tag(inp, out, model, format='tags'):
    tagger = CRFTagger(model)
    with open(model + FEATS_SUFFIX, 'rb') as f:
        featurizer = Featurizer.load(f)
    data = featurizer.featurize_dataset(inp)
    y_seqs = (tagger.tag(x_seq) for x_seq in data)
    if format == 'tags':
        pass
    elif format == 'TN':
        # Convert tags to binary
        y_seqs = (['T' if y == 'O' else 'N' for y in y_seq] for y_seq in y_seqs)
    else:
        raise Exception(f'Unknown Format {format}')
    y_seqs = ((' '.join(y_seq),) for y_seq in y_seqs)
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
            src_tags = tagger.tag(featurizer.featurize_seq(src))
            if featurizer.is_group_mode():
                rec = cut_dnt_groups(src, src_tags, tgt)
            else:
                rec = cut_dnt_bio(src, src_tags, tgt)
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
        err_count = 0
        for line in inp:
            text, dnt_words = line.split('\t')
            text, dnt_words = text.strip().split(), dnt_words.strip()
            if dnt_words[0] == '{' and dnt_words[-1] == '}':
                dnt_words = json.loads(dnt_words)
            else:   # Old format
                dnt_words = [x.replace(DELIM, ' ') for x in dnt_words.split()]

            res = []
            for word in text:
                out_word = word
                match = RE_PATTERN.match(word)
                if match:
                    _, dnt_type, pos = match.groups()
                    pos = int(pos)
                    dnt_word_list = dnt_words.get(dnt_type, []) if dnt_type else dnt_words
                    assert pos > 0
                    if pos <= len(dnt_word_list):
                        out_word = dnt_word_list[pos - 1]  # DNT index starts from 1
                    elif ignore_errors:
                        out_word = ''
                        err_count += 1
                    else:
                        raise Exception('Cant find replacement. DNT Index=%d, DNT Words=%s' % (pos, dnt_words))
                res.append(out_word)
            yield (' '.join(res),)
        log.warning(f"Found {err_count} DNT replacement errors..")
    write_recs(_dnt_paste(), out)


def get_arg_parser():
    # TODO: reorganize these parsers as parent-child, avoid redefinition of arguments
    parser = argparse.ArgumentParser(description='Do Not Translate (DNT) tagger', prog='crfdnt',
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

    eval_res_arg_parser = sub_parsers.add_parser('eval-res', help='Evaluate Result of tagger',
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
    prep_arg_parser.add_argument('-f', '--format', choices=['src-tags', 'tags', 'conll', 'TN'], default='src-tags',
                                 type=str, help='''Format of output: `src-tag`: output SOURCE\\tTAG per line.
                                   `tag`: output just TAG sequence per line.
                                   `conll`: output in CoNLL 2013 NER format. 
                                   `TN`: outputs binary flags: T for Translate, N for Not-translate''')

    prep_arg_parser.add_argument('-ner', '--ner-model', type=str,
                                 help='''NER model for categorising the DNT tags.
                                  NER is powered by Spacy, hence the value should be a valid spacy model. Example:
                                  {en_core_web_sm, en_core_web_md, en_core_web_lg}. 
                                  When not specified, no NER categorization will be done.''')

    # Train
    train_arg_parser.add_argument('model', type=str, help='''Path to store model file''')
    train_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream of Training data. Default is STDIN. When specified, it should be a file path.
            Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line by default
            Data Format=SRC_SEQUENCE\\tTGT_SEQUENCE i.e. parallel bitext when --bitext is used''')
    train_arg_parser.add_argument('-c', '--context', type=int, default=2, help="Context in sequence.")
    train_arg_parser.add_argument('-bt', '--bitext', action='store_true', help="input is a parallel bitext")
    train_arg_parser.add_argument('-ner', '--ner-model', type=str,
                                  help='''Applicable for --bitext mode. NER model for categorising the tags.
                                      NER is powered by Spacy, hence the value should be a valid spacy model. Example:
                                      {en_core_web_sm, en_core_web_md, en_core_web_lg}. 
                                      When not specified, no NER categorization will be done.''')

    train_arg_parser.add_argument('-nm', '--no-memorize', action='store_true', default=False,
                                  help="Do not memorize words")
    train_arg_parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose")

    # Tagging
    tag_arg_parser.add_argument('model', type=str, help='''Path to the stored model file''')
    tag_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream of data. Default is STDIN. When specified, it should be a file path.
             Data Format=one SRC_SEQUENCE per line''')
    tag_arg_parser.add_argument('-o', '--out', default=sys.stdout, type=argparse.FileType('w'), help='''
        Output stream. Default is STDOUT. When specified, it should be a file path. 
        Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line.''')
    tag_arg_parser.add_argument('-f', '--format', choices=['tags', 'TN'], default='tags',
                                 type=str, help='''Format of output: 
                                       `tag`: output just TAG sequence per line. 
                                       `TN`: outputs binary flags: T for Translate, N for Not-translate''')

    # Evaluation
    eval_arg_parser.add_argument('model', type=str, help='''Path to the stored model file''')
    eval_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
            Input stream of Test data. Default is STDIN. When specified, it should be a file path. 
            Data Format=SRC_SEQUENCE\\tTAG_SEQUENCE per line''')
    eval_arg_parser.add_argument('-e', '--explain', action='store_true',
                                 help='Explain top state transitions and weights')

    eval_res_arg_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help='''
                Input stream of result and gold. Default is STDIN. When specified, it should be a file path. 
                Data Format=PREDICTED_SEQUENCE\\tGOLD_SEQUENCE per line''')

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
        'eval': evaluate_model,
        'eval-res': evaluate_result,
        'dnt-cut': dnt_cut,
        'dnt-paste': dnt_paste,
    }
    args = vars(args)
    task = args['task']
    del args['task']
    tasks.get(task, not_implemented)(**args)


if __name__ == '__main__':
    main()
