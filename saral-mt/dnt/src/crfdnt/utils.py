# Author = Thamme Gowda
# Created = April 07, 2018


import unicodedata as ud
from collections import defaultdict


def is_not_punct(tok):
    """
    :param tok: text
    :return: True if the text is not solely made of punctuation characters
    """
    for ch in tok:
        if not ud.category(ch).startswith('P'):
            return True
    return False


def normalize(toks):
    return set(filter(is_not_punct, [x.lower() for x in toks]))


def dnt_tag_toks(src_seq, tgt_seq):
    """
    tags DNT tokens
    :param src_seq:
    :param tgt_seq:
    :return:
    """
    """
    1. set of common tokens between source and target, ignore the case
    2. Mark source token as DNT (True if they are in the set in Step 1)
    """
    # Step 1
    common_toks = normalize(src_seq) & normalize(tgt_seq)
    # Step 2
    return [(tok, tok.lower() in common_toks) for tok in src_seq]


def tag_src_iob(src, tgt, tag='DNT'):
    """
    Tags the DNT words in source sequence using
    :param src: source sentence
    :param tgt: target sentence
    :param tag: tag name for dnt words
    :return: IOB tags for source
    """
    tagged_src = dnt_tag_toks(src, tgt)
    tags = []
    for tok, dnt in tagged_src:
        """ State Transition Table :: 
        last↓\DNT| T | F
             Nil | B | O
               O | B | O
               B | I | O 
               I | I | O
        """
        if not dnt:
            # The 'F' column in  the state transition table (this is not a DNT token) -> O .
            tags.append('O')
        else:
            # The T column in the table  (This is a DNT token)
            if not tags or tags[-1] == 'O':
                # The first two rows in the table
                # no history or last one was O , therefore B
                tags.append(f'B-{tag}')
            else:
                # the last two rows of in the table
                # Last one was either B or I, therefore I
                tags.append(f'I-{tag}')
    assert len(src) == len(tags)
    return tags


def evaluate_multi_class(label_func, test_set, label_normalizer=None, do_print=True):
    """
    Evaluates a multi class labelling function
    :param label_func: function that accepts X and returns predictions
    :param test_set: stream of records, each having (X, Y) where X is input and Y is gold. Both X and Y are sequences
    :param label_normalizer: optional function to map label names
    :param do_print: print the results
    :return: List of records, one per label
    """
    conf_matrix = defaultdict(lambda: defaultdict(int))
    for x_seq, y_gold in test_set:
        y_pred = label_func(x_seq)
        assert len(x_seq) == len(y_gold) == len(y_pred)
        if label_normalizer:
            y_gold = [label_normalizer(l) for l in y_gold]
            y_pred = [label_normalizer(l) for l in y_pred]

        for row, col in zip(y_gold, y_pred):
            conf_matrix[row][col] += 1
    conf_matrix = dict(conf_matrix)
    labels = list(conf_matrix.keys())

    result = []
    for label in labels:
        rec = {
            'Label': label,
            'GoldCount': sum(conf_matrix[label].values()),
            'PredictedCount': sum(row[label] for row in conf_matrix.values()),
            'Correct': conf_matrix[label][label]
        }
        rec['Precision'] = rec['Correct'] / rec['PredictedCount']
        rec['Recall'] = rec['Correct'] / rec['GoldCount']
        rec['F1'] = 2 * rec['Precision'] * rec['Recall'] / (rec['Precision'] + rec['Recall'])
        result.append(rec)
    if do_print:
        print_eval(result)
    return result


def print_eval(recs, just=15):

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
