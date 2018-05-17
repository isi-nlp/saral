#!/usr/bin/env python

# Author: Thamme  Gowda
# Created On: May 1, 2018

import spacy
import sys
import logging as log

log.basicConfig(level=log.DEBUG)
log.info(f'Spacy Version: {spacy.__version__}')


class NER(object):

    def __init__(self, model='en_core_web_sm'):
        log.info(f'Loading spacy model {model}')
        try:
            self.model = spacy.load(model, disable=['parser'])
            log.debug(f'Loaded spacy model {model}')
        except OSError as e:
            log.error(f'Failed to load model.  Please run `python -m spacy download {model}` to download the model')
            raise e

    def tag(self, text, other_tag):
        doc = self.model(text)
        ent_types = [tok.ent_type_ if tok.ent_type_ else other_tag for tok in doc]
        return list(map(str, doc)), ent_types

    def tag_all(self, recs, other_tag='O'):
        """Tags a stream of lines with NER annotation
        :param recs: stream of lines
        :param model: Spacy Model name
        :param other_tag: tag the non NE tokens as this tag
        :return: yields tuples ([toks...], [tags...])
        """
        for line in recs:
            yield self.tag(line.strip(), other_tag)


def main(fin, fout, model):
    nlp = NER(model)
    count = 0
    for toks, tags in nlp.tag_all(fin):
        fout.write(' '.join(toks))
        fout.write('\t')
        fout.write(' '.join(tags))
        fout.write('\n')
        count += 1
    log.info(f'Processed {count} lines')


if __name__ == '__main__':
    import argparse as ap
    parser = ap.ArgumentParser(description='Name Tagger', formatter_class=ap.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--in', dest='fin', default=sys.stdin, type=ap.FileType('r'), help='Input')
    parser.add_argument('-o', '--out', dest='fout', default=sys.stdout, type=ap.FileType('w'), help='Output')
    parser.add_argument('-m', '--model', dest='model', default='en_core_web_sm', type=str,
                        help='Spacy Model for NER. Example: en_core_web_sm, en_core_web_md, en_core_web_lg etc')
    args = vars(parser.parse_args())
    main(**args)