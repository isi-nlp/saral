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
from .ner import BaseTagger

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


def project_tags(inp, out):
    """Projects tags from one column to other for common tokens
    INPUT: FROM_SEQ \\t FROM_SEQ_TAGS \\t TO_SEQ
    OUTPUT: TO_SEQ \\t TO_SEQ_TAGS
    """

    def _project():
        for line in inp:
            parts = line.split('\t')
            assert len(parts) == 3
            from_seq, from_seq_tags, to_seq = (col.strip().split() for col in parts)
            assert len(from_seq) == len(from_seq_tags)
            to_seq_tags = BaseTagger.project_tags(from_seq, from_seq_tags, to_seq)
            assert len(to_seq) == len(to_seq_tags)
            yield ' '.join(to_seq), ' '.join(to_seq_tags)
    write_recs(_project(), out)


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


def dnt_cut_tagged(inp, out):
    """
    Cut DNT tokens from external tagger
    :param inp: stream of either "SRC \t SRC_TAGS  or SRC \t SRC_TAGS \t TGT
    :param outp: stream to write output
    :return: None
    """
    lines = (line.strip() for line in inp)
    lines = (l.split('\t') for l in lines if l)

    def _cut(recs):
        for rec in recs:
            rec = [c.split() for c in rec]
            assert len(rec) == 2 or len(rec) == 3
            src, src_tags = rec[:2]
            assert len(src) == len(src_tags), f'{src} and {src_tags} should have 1-to-1 map'
            tgt = None if len(rec) < 3 else rec[2]
            yield cut_dnt_bio(src, src_tags, tgt)
    write_recs(_cut(lines), out)


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


def add_task(parser, name, desc, inp_format=None, out_format=None, requires_model=False):
    task_parser = parser.add_parser(name, help=desc, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    if requires_model:
        task_parser.add_argument('model', type=str, help='''Path to the model file''')
    if inp_format:
        task_parser.add_argument('-i', '--inp', default=sys.stdin, type=argparse.FileType('r'), help=f'''
                Input stream. Default is STDIN. When specified, it should be a file path.
                 Data Format= {inp_format}''')
    if out_format:
        task_parser.add_argument('-o', '--out', default=sys.stdout, type=argparse.FileType('w'), help=f'''
                Output stream. Default is STDOUT. When specified, it should be a file path. 
                Data Format= {out_format}''')

    return task_parser


def get_arg_parser():
    parser = argparse.ArgumentParser(description='Do Not Translate (DNT) tagger', prog='crfdnt',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sub_parsers = parser.add_subparsers(help='tasks', dest='task')
    sub_parsers.required = True

    # Prep
    prep_arg_parser = add_task(sub_parsers, 'prepare', 'Prepare training data from parallel MT corpus',
                               inp_format='SRC_SEQUENCE\\tTGT_SEQUENCE per line', out_format='Depends on -f argument')
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
    train_arg_parser = add_task(sub_parsers, 'train', 'Train a CRF DNT Tagger model', requires_model=True,
                                inp_format='''SRC_SEQUENCE\\tTAG_SEQUENCE per line by default
            or SRC_SEQUENCE\\tTGT_SEQUENCE[\\tSRC_TAGS] when --bitext is used''', out_format=None)
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

    train_arg_parser.add_argument('-mi', dest='max_iterations', type=int, help='Maximum Trainer Iterations',
                                  default=100)
    train_arg_parser.add_argument('-c1', dest='c1', type=float, help='L1 regularization Coefficient', default=1.0)
    train_arg_parser.add_argument('-c2', dest='c2', type=float, help='L2 regularization Coefficient', default=1e-3)

    # Tag
    tag_arg_parser = add_task(sub_parsers, 'tag', 'Tag DNT words using CRF DNT model', requires_model=True,
                              inp_format='one SRC_SEQUENCE per line',
                              out_format='SRC_SEQUENCE\\tTAG_SEQUENCE per line')
    tag_arg_parser.add_argument('-f', '--format', choices=['tags', 'TN'], default='tags',
                                type=str, help='''Format of output: 
                                       `tag`: output just TAG sequence per line. 
                                       `TN`: outputs binary flags: T for Translate, N for Not-translate''')
    # Eval
    eval_arg_parser = add_task(sub_parsers, 'eval', 'Evaluate a CRF DNT model', requires_model=True,
                               inp_format='SRC_SEQUENCE\\tTAG_SEQUENCE per line')
    eval_arg_parser.add_argument('-e', '--explain', action='store_true',
                                 help='Explain top state transitions and weights')

    # Eval Res
    add_task(sub_parsers, 'eval-res', 'Evaluate Result of tagger',
             inp_format='PREDICTED_SEQUENCE\\tGOLD_SEQUENCE per line')

    # Cut
    add_task(sub_parsers, 'dnt-cut', 'Cut DNT words', requires_model=True,
             inp_format='one SRC_SEQUENCE per line or SRC\\tTGT sequence per line.',
             out_format='SRC_SEQ_CUT\\tDNT or SRC_SEQ_CUT\\tTGT_SEQ_CUT\\tDNT')

    # Cut
    add_task(sub_parsers, 'dnt-cut-ex', 'Cut DNT words, using tagged source from external tagger',
             requires_model=False,
             inp_format='one SRC_SEQ\\tSRC_TAGS per line or '
                        'SRC_SEQ\\tSRC_TAGS\\tTGT sequence per line.',
             out_format='SRC_SEQ_CUT\\tDNT or SRC_SEQ_CUT\\tTGT_SEQ_CUT\\tDNT')

    add_task(sub_parsers, 'project', 'Project tags',
             inp_format='FROM_SEQ \\t FROM_SEQ_TAGS \\t TO_SEQ per line.',
             out_format='TO_SEQ \\t TO_SEQ_TAGS')

    # Paste
    add_task(sub_parsers, 'dnt-paste', 'Paste DNT words',
             inp_format='one TEXT_SEQ\\tDNT sequence per line',
             out_format='replaced TEXT_SEQ per line')
    return parser


def main():
    assert sys.version_info[0] >= 3
    args = get_arg_parser().parse_args()
    tasks = {
        'train': train,
        'prepare': prepare,
        'project': project_tags,
        'tag': tag,
        'eval': evaluate_model,
        'eval-res': evaluate_result,
        'dnt-cut': dnt_cut,
        'dnt-cut-ex': dnt_cut_tagged,
        'dnt-paste': dnt_paste,
    }
    args = vars(args)
    task = args['task']
    del args['task']
    tasks.get(task, not_implemented)(**args)


if __name__ == '__main__':
    main()
