# Author = Thamme Gowda
# Created = April 07, 2018

import pycrfsuite as pycrf
import logging as log
from crfdnt.utils import evaluate_multi_class
from collections import Counter

log.basicConfig(level=log.INFO)


class Featurizer(object):
    """
    Creates features for sequences
    """

    def __init__(self, context):
        """
        :param context: number of words in context (backsize and front side) to use for features
        """
        self._version = 1
        self.context = context

    @staticmethod
    def featurize_word(word):
        buff = f'''
        bias
        word.lower={word.lower()}
        word.isupper={word.isupper()}
        word.islower={word.islower()}
        word.istitle={word.istitle()}
        word.isdigit={word.isdigit()}
        '''
        return [x.strip() for x in buff.strip().split('\n')]

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
            seq = self.featurize_seq(words)
            if tags:
                assert len(seq) == len(tags)
                yield seq, tags
            else:
                yield seq


class CRFTrainer(pycrf.Trainer):
    """
    An object of this class can be used to train a CRF tagger model
    """

    def __init__(self, *args, **kwargs):
        super(CRFTrainer, self).__init__(*args, **kwargs)

    @staticmethod
    def get_trainer_params():
        return {
            'c1': 1.0,  # coefficient for L1 penalty
            'c2': 1e-3,  # coefficient for L2 penalty
            'max_iterations': 100,  # stop earlier
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

    def evaluate(self, test_set, label_mapper=None, just=15):
        recs = evaluate_multi_class(self.tag, test_set, label_mapper)
        keys = ['Label', 'GoldCount', 'PredictedCount', 'Correct', 'Precision', 'Recall', 'F1']

        def print_row(row):
            row = ['%.6f' % cell if type(cell) is float else str(cell) for cell in row]
            print(''.join(cell.rjust(just) for cell in row))

        print_row(keys)
        for rec in recs:
            print_row([rec[key] for key in keys])

        avg = ['(Average)', '', '', '']
        avg.extend([sum(rec[col] for rec in recs) / len(recs) for col in ['Precision', 'Recall', 'F1']])
        print_row(avg)
        return recs

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
