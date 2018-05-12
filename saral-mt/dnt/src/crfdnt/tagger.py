# Author = Thamme Gowda
# Created = April 07, 2018

import sys
import pycrfsuite as pycrf
import logging as log
from crfdnt.utils import evaluate_multi_class
from collections import Counter
import random
import pickle
import unicodedata as ud
from emoji import UNICODE_EMOJI

from .utils import tag_src_iob

log.basicConfig(level=log.INFO)


class Featurizer(object):
    """
    Creates features for sequences
    """

    def __init__(self, context, memorize=True, ner_model=None):
        """
        :param context: number of words in context (back side and front side) to use for features
        :param memorize: memorize words
        """
        """
        Versions:
        1 - base version without below
        2 - Memorize and no-memorize  distinction
        3 - More features for detecting URL, email, emoji etc
        4 - Integrate NER tagger
        """
        self._version = 4
        self.context = context
        self.pos_vocab = set()
        self.neg_vocab = set()
        self.memorize = memorize
        self.ner_model = ner_model
        log.info(f"Memorize words: {self.memorize}")

    def featurize_word(self, word):
        lc_word = word.lower()
        buff = f'''
        bias
        word.isupper={word.isupper()}
        word.islower={word.islower()}
        word.istitle={word.istitle()}
        word.isdigit={word.isdigit()}
        word.ispunct={self.is_punct(word)}'''
        if self._version >= 3:
            buff += f'''
            word.isurl={lc_word.startswith('http')}
            word.has_scheme={'://' in word }
            word.has_at={'@' in word }
            word.begin_at={word.startswith('@')}
            word.has_hash={'#' in word}
            word.begin_hash={word.startswith('#')}
            word.is_emoji={self.is_emoji(word)}
            word.has_emoji={self.has_emoji(word)}
            '''
        feats = [x.strip() for x in buff.strip().split('\n')]
        if self.memorize:
            feats.append(f'word.lower={lc_word}')
        if lc_word in self.pos_vocab:
            feats.append('word.pos_vocab')
        if lc_word in self.neg_vocab:
            feats.append('word.neg_vocab')
        return feats

    @staticmethod
    def is_punct(tok):
        """
        :param tok: token
        :return: True if token is made of only punctuation characters; False otherwise
        """
        for x in tok:
            if ud.category(x)[0] != 'P':
                return False
        return True

    @staticmethod
    def is_emoji(tok):
        """
        :param tok: token
        :return: True if token is made of only emoji characters; False otherwise
        """
        for x in tok:
            if x not in UNICODE_EMOJI:
                return False
        return True

    @staticmethod
    def has_emoji(tok):
        """
        :param tok: token
        :return: True if token is made of at least one emoji characters; False otherwise
        """
        for x in tok:
            if x in UNICODE_EMOJI:
                return True
        return False

    def featurize_seq(self, words):
        seq = [self.featurize_word(word) for word in words]
        seq[0].append('BOS')
        seq[-1].append('EOS')
        context_feats = [[] for _ in range(len(seq))]
        for i in range(len(seq)):
            # Forward Context
            for j in range(i+1, min(len(seq), i+self.context+1)):
                context_feats[i].extend([f'+{j-i}:{feat}' for feat in seq[j]])
            # backward context
            for j in range(i - 1, max(-1, i-self.context-1), -1):
                context_feats[i].extend([f'{j-i}:{feat}' for feat in seq[j]])
        assert len(seq) == len(context_feats)
        for feats, ctx in zip(seq, context_feats):
            feats.extend(ctx)
        return seq

    def featurize_dataset(self, stream):
        for line in stream:
            words = line.strip()
            tags = None
            if '\t' in words:
                words, tags = words.split('\t')
                tags = tags.split()

            words = words.split()
            if not words:
                print(f"Error: Skip:: {line}", file=sys.stderr)
                continue
            seq = self.featurize_seq(words)
            if tags:
                assert len(seq) == len(tags)
                yield seq, tags
            else:
                yield seq

    def get_gold_tagger(self):
        """Makes a gold tagger - for use when bitext is available"""
        if self.ner_model:
            from .ner import NER, RegexTagger
            ner = NER(self.ner_model)
            re_tagger = RegexTagger()

            def v2_tag_func(src, tgt):
                _, _, src, src_tags = ner.tag_and_project(tgt, src)
                _, re_src_tags = re_tagger.tag(src, None)
                assert len(src_tags) == len(re_src_tags)
                # Regex Tagger gets higher priority here
                src_tags = [r_tag if r_tag else n_tag for r_tag, n_tag in zip(re_src_tags, src_tags)]
                return src, src_tags
            return v2_tag_func
        else:
            def v1_tag_func(src, tgt):
                # return signature looks ugly, but made it to match v2_tagger
                return src, tag_src_iob(src, tgt)
            return v1_tag_func

    def is_group_mode(self):
        return True if self.ner_model else False

    def featurize_parallel_set(self, stream, swap=False, update_vocab_prob=0.7):
        tag_func = self.get_gold_tagger()
        for line in stream:
            line = line.strip()
            if not line:
                continue
            if '\t' not in line:
                print(f"Error! Cant split  :: {line}", file=sys.stderr)
                continue
            src, tgt = line.split('\t')
            if swap:
                src, tgt = tgt, src
            src, tgt = src.split(), tgt.split()
            src, src_tags = tag_func(tgt, src)
            assert len(src) == len(src_tags)
            if self.memorize and update_vocab_prob > 0 and random.uniform(0, 1) <= update_vocab_prob:
                self.pos_vocab.update(tgt)
                self.neg_vocab.update(src)

            x_seq = self.featurize_seq(src)
            yield x_seq, src_tags

    def migrate(self):
        if self._version < 2:
            self.memorize = True
        if self._version < 4 or not hasattr(self, 'ner_model'):
            setattr(self, 'ner_model', None)

    @staticmethod
    def load(stream):
        obj = pickle.load(stream)
        obj.migrate()
        return obj


class CRFTrainer(pycrf.Trainer):
    """
    An object of this class can be used to train a CRF tagger model
    """

    def __init__(self, *args, **kwargs):
        super(CRFTrainer, self).__init__(*args, **kwargs)

    @staticmethod
    def get_trainer_params():
        return {
            'c1': 1,  # coefficient for L1 penalty
            'c2': 1e-3,  # coefficient for L2 penalty
            'max_iterations': 100,  # stop after
            # include transitions that are possible, but not observed
            'feature.possible_transitions': True
        }

    def train_model(self, train_set, model_path, **trainer_params):
        """
        Train a model
        :param train_set: set of training examples (could be a stream too),
         each item should have X and Y sequences of equal length (mapped by index)
        :param model_path: path to store model
        :param trainer_params: dictionary containing parameters to crf trainer
        :return: None
        """

        params = self.get_trainer_params()
        params.update(trainer_params)
        log.info(f"Trainer Params: {params}")
        self.set_params(params)
        for x_seq, y_seq in train_set:
            self.append(x_seq, y_seq)
        log.info("Training...")
        self.train(model_path)
        log.info(f"Model should be saved at {model_path}")
        log.info(self.logparser.last_iteration)


class CRFTagger(pycrf.Tagger):
    """
    An instance of this class is useful for making predictions (aka tagging).
    In addition, it also have methods to self evaluate using a given test set, and self explanation of model weights
    """

    def __init__(self, model_path, *args, **kwarsg):
        super(CRFTagger, self).__init__(*args, **kwarsg)
        log.info(f"Loading model from {model_path}")
        self.open(model_path)

    def evaluate(self, test_set, label_mapper=None):
        return evaluate_multi_class(self.tag, test_set, label_mapper, do_print=True)

    def explain(self, top_trans=10, top_feats=20):
        """
        Prints explanations of state transitions and feature weights
        :param top_trans: number of top transitions to print
        :param top_feats: number of top features to print
        :return: None
        """
        info = self.info()

        def print_transitions(trans_features):
            for (label_from, label_to), weight in trans_features:
                print("%-6s -> %-7s %0.6f" % (label_from, label_to, weight))

        trans = Counter(info.transitions).most_common()

        if len(trans) > top_trans:
            print("Top Likely transitions:")
            print_transitions(trans[:top_trans])

            print("\nTop unlikely transitions:")
            print_transitions(trans[-top_trans:])
        else:
            print("Transitions:")
            print_transitions(trans)

        def print_state_features(state_features):
            for (attr, label), weight in state_features:
                print("%0.6f %-6s %s" % (weight, label, attr))

        state_feats = Counter(info.state_features).most_common()
        print("\nTop positive:")
        print_state_features(state_feats[:top_feats])

        print("\nTop negative:")
        print_state_features(state_feats[-top_feats:])
        print("\n")
