#!/usr/bin/env python

# Author: Thamme  Gowda
# Created On: May 1, 2018

import spacy
from spacy.tokens import Doc
import logging as log
import unicodedata as ud
from abc import ABC, abstractmethod
import re
import sys

log.basicConfig(level=log.DEBUG)
log.info(f'Spacy Version: {spacy.__version__}')

# list because the order of application could be important
PATTERNS = [
    ('NUMBER', r'^[+-]?\d+(\.\d+)?$'),
    ('HANDLE', r'^[a-zA-Z0-9\.\-\_]+@(([a-z0-9A-Z]+\.)+[a-z]{2,})$'),
    ('HASH', r'^#.+'),
    ('HANDLE', r'^@[^ @/]{3,}$'),
    ('NUM_GROUP', r'^[0-9]+([\\\-/\.][0-9]+){2,}$'),
    # No, TG didn't write this URL pattern, it is copied from  https://gist.github.com/gruber/249502
    ('URL', r'^(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\((' +
        r'[^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))$')
]


class BaseTagger(ABC):

    @abstractmethod
    def tag(self, text, other_tag):
        raise NotImplementedError()

    def tag_tok(self, tok):
        raise NotImplementedError()

    def tag_all(self, recs, other_tag='O'):
        """Tags a stream of lines with NER annotation
        :param recs: stream of lines
        :param other_tag: tag the non NE tokens as this tag
        :return: yields tuples ([toks...], [tags...])
        """
        for line in recs:
            yield self.tag(line.strip(), other_tag)

    def tag_and_project(self, from_seq, to_seq, other_tag='O', fallback_tag='MISC', fallback_tagger=None):
        """
        Combines tag() and project_tags() together
        :param from_seq: text sequence known to the NER model (eg: eng sequence)
        :param to_seq: foreign text sequence
        :param other_tag: tag the non NER tokens with this
        :param fallback_tagger: use this tagger as fall back
        :param fallback_tag: if a common token happen to have `other_tag`, then instead use this tag as final one
        :return: (from_toks, from_tags, to_toks, to_tags)
        """
        from_toks, from_tags = self.tag(' '.join(from_seq), other_tag=other_tag)
        to_tags = self.project_tags(from_seq, from_tags, to_seq, other_tag, fallback_tag, fallback_tagger)
        return from_seq, from_tags, to_seq, to_tags

    @classmethod
    def project_tags(cls, seq1, seq1_tags, seq2, other_tag='O', fallback_tag='MISC', fallback_tagger=None):
        """
        Finds common tokens between seq1 and seq2, and projects tags of seq1 to seq2
        :param seq1: First sequence that has tags
        :param seq1_tags: tags of first sequence
        :param seq2: second sequence that needs to have tags projected to
        :param other_tag: Tag name for non-common tokens
        :param fallback_tagger: use this tagger as fall back when the
        :param fallback_tag: if a common token happen to have `other_tag`, then instead use this tag as final one
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
                if tag == other_tag and not is_punct(norm_tok):  # DNT word tagged as `other` by the previous tagger
                    if fallback_tagger:
                        tag = fallback_tagger.tag_tok(tok, fallback_tag)
                    else:
                        tag = fallback_tag
            seq2_tags.append(tag)
        return seq2_tags


class RegexTagger(BaseTagger):
    """
    regex based tagger, good for tagging emails, numbers etc
    """

    def __init__(self, patterns=PATTERNS):
        """
        :param patterns: List of tuples, having (name, pattern) strings
        """
        assert len(patterns) > 0
        self.patterns = [(typ.upper(), re.compile(pat)) for typ, pat in patterns]

    def tag(self, text, other_tag):
        toks = text.split() if type(text) is str else text
        tags = [self.tag(tok, other_tag) for tok in toks]
        return toks, tags

    def tag_tok(self, tok, other_tag=None):
        tag = other_tag
        for typ, pat in self.patterns:
            if pat.match(tok):
                tag = typ
                break
        return tag


class NER(BaseTagger):

    def __init__(self, model='en_core_web_sm'):
        log.info(f'Loading spacy model {model}')
        try:
            self.model = spacy.load(model, disable=['parser'])
            log.debug(f'Loaded spacy model {model}')
            # The default Tokenizer breaks punctuations. Expect pre tokenized input
            self.model.tokenizer = WhitespaceTokenizer(self.model.vocab)
        except OSError as e:
            log.error(f'Failed to load model.  Please run `python -m spacy download {model}` to download the model')
            raise e

    def tag(self, text, other_tag):
        """
        tokenizes and tags text
        :param text: untokenized text string
        :param other_tag:
        :return: ([toks...], [tags...])
        """
        doc = self.model(text)
        ent_types = [tok.ent_type_ if tok.ent_type_ else other_tag for tok in doc]
        return list(map(str, doc)), ent_types


class WhitespaceTokenizer(object):

    """White Space tokenizer for spacy."""
    def __init__(self, vocab):
        self.vocab = vocab

    def __call__(self, text):
        words = text.strip().split()
        # All tokens 'own' a subsequent space character in this tokenizer
        spaces = [True] * len(words)
        return Doc(self.vocab, words=words, spaces=spaces)


def is_punct(tok):
    """
    :param tok: text
    :return: True if the text is not solely made of punctuation characters
    """
    for ch in tok:
        if not ud.category(ch).startswith('P'):
            return False
    return True


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
