#!/usr/bin/env python
# Author: Thamme Gowda tg@isi.edu
# Crated on: November 14, 2017
"""
N-gram Overlap between two files.
This can be useful for finding n gram overlaps between training, dev and test splits
"""

from collections import defaultdict

def tokenize(text, lowercase=False):
    """Tokenizes text by whitespace"""
    if lowercase:
        text = text.lower()
    return text.split()


def make_grams(file, min_grams=1, max_grams=7,lowercase=False):
    """Makes n-grams from file"""
    grams = dict((i, set()) for i in range(min_grams, max_grams+1))
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            tokens = tokenize(line, lowercase)
            for gram_size in range(min_grams, min(max_grams, len(tokens)) + 1):
                for idx in range(len(tokens) - gram_size + 1):
                    gram = tuple(tokens[idx:idx + gram_size])
                    grams[gram_size].add(gram)
    return grams


def text_to_grams(text, min_grams=1, max_grams=7, lowercase=False):
    """Makes n-grams from text"""
    grams = dict((i, set()) for i in range(min_grams, max_grams+1))
    tokens = tokenize(text, lowercase)
    for gram_size in range(min_grams, min(max_grams, len(tokens)) + 1):
        for idx in range(len(tokens) - gram_size + 1):
            gram = tuple(tokens[idx:idx + gram_size])
            grams[gram_size].add(gram)
    return grams


def count_grams(text, gram_size, lowercase=False):
    """Counts n gram frequencies in text"""

    counts = defaultdict(int)
    ids = defaultdict(set)
    if type(text) is str:
        text = [text]
    seq = 0
    for s in text:
        seq += 1
        tokens = tokenize(s, lowercase)
        for idx in range(len(tokens) - gram_size + 1):
            gram = tuple(tokens[idx:idx + gram_size])
            counts[gram] += 1
            ids[gram].add(seq)
    return counts, ids


def find_overlap(file1, file2, min_grams=1, max_grams=7, lowercase=False):
    """Computes overlap between n-grams"""
    mem1 = make_grams(file1, max_grams=max_grams, lowercase=lowercase)
    mem2 = make_grams(file2, max_grams=max_grams, lowercase=lowercase)
    print("%s\t%s\t%s\t%s\t%s" % ("n_gram", "Unique_1", "Unique_2", "Common", "Ratio"))
    for gram_size in range(min_grams, max_grams + 1):
        set1, set2 = mem1[gram_size], mem2[gram_size]
        common = len(set1 & set2)
        dnr = min(len(set1), len(set2))
        ratio = common / dnr if dnr > 0 else 0
        print("%d\t%d\t%d\t%d\t%.4f" % (gram_size, len(set1), len(set2), common, ratio))


def print_overlaps(file1, file2, min_grams, max_grams, lowercase=False):
    """
    prints overlapping lines in files based on n-gram match
    :param file1:  first file, n-grams will be held in memory
    :param file2:  second file, processed line by line and matched lines are printed
    :param min_grams: minimum grams to start with
    :param max_grams: upto maximum grams
    :param lowercase: case insensitive match
    :return: number of lines matched
    """
    mem = make_grams(file1, max_grams=max_grams, min_grams=min_grams, lowercase=lowercase)
    count = 0
    with open(file2, 'r', encoding='utf-8') as f:
        print("size\tcount\tsample\ttext")
        for line in f:
            grams = text_to_grams(line, min_grams=min_grams, max_grams=max_grams, lowercase=lowercase)
            for gram_size in range(max_grams, min_grams-1, -1):
                common = mem[gram_size] & grams[gram_size]
                if common:
                    count += 1
                    print("%d-gram\t%d\t%s\t%s" % (gram_size, len(common), " ".join(list(common)[0]), line.strip()))
                    break
    return count


def print_freq_n_grams(file1, file2, n, top=100, lowercase=False):
    with open(file1) as f1:
        tf1, seq1 = count_grams(f1, n, lowercase)
    with open(file2) as f2:
        tf2, seq2 = count_grams(f2, n, lowercase)

    res = defaultdict(int)
    union = set(tf1.keys()) | set(tf2.keys())
    for elem in union:
        res[elem] = tf1[elem] + tf2[elem]

    top_grams = sorted(res.items(), key=lambda x: x[1], reverse=True)[:top]
    print("n-gram\tcount(First)\tCount(Second)\tLines(First)\tLines(second)")
    for gram, count in top_grams:
        ids1 = '; '.join(map(str, seq1[gram]))
        ids2 = '; '.join(map(str, seq2[gram]))
        print('%s\t%d\t%d\t"%s"\t"%s"' % (' '.join(gram), tf1[gram], tf2[gram], ids1, ids2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser("""n-gram overlap between two text files""",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n', '--max-gram', type=int, help="Maximum N-Grams", default=7)
    parser.add_argument('-m', '--min-gram', type=int, default=1,
                        help='Write common n-grams to file longer than this size')
    parser.add_argument('-lc', action="store_true", help="Case insensitive match")
    parser.add_argument('file', nargs=2, help='Plain text input with white spaces between tokens.')
    parser.add_argument('-print', action="store_true", help="Print matches")
    parser.add_argument('-t', '--top-grams', type=int, help="Top grams to be printed", default=-1)

    args = vars(parser.parse_args())
    first, second = args['file']
    m, n = args['min_gram'], args['max_gram']
    if n < m:
        n = m
    if args['print']:
        print_overlaps(first, second, m, n, args['lc'])
    if args['top_grams'] > 0:
        print_freq_n_grams(first, second, m, args['top_grams'], args['lc'])
    else:
        find_overlap(first, second, m, n, args.get("lc"))
