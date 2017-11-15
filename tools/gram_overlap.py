#!/usr/bin/env python
# Author: Thamme Gowda tg@isi.edu
# Crated on: November 14, 2017
"""
N-gram Overlap between two files.
This can be useful for finding n gram overlaps between training, dev and test splits
"""


def tokenize(text):
    """Tokenizes text by whitespace"""
    return text.split()


def make_grams(file, max_grams, lowercase=False):
    """Makes n-grams from file"""
    grams = [set() for _ in range(max_grams+1)]
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            if lowercase:
                line = line.lower()
            tokens = tokenize(line)
            for gram_size in range(1, min(max_grams, len(tokens)) + 1):
                for idx in range(len(tokens) - gram_size + 1):
                    gram = tuple(tokens[idx:idx + gram_size])
                    grams[gram_size].add(gram)
    return grams


def find_overlap(file1, file2, max_grams, lowercase=False):
    """Computes overlap between n-grams"""
    mem1 = make_grams(file1, max_grams, lowercase)
    mem2 = make_grams(file2, max_grams, lowercase)
    print("%s\t%s\t%s\t%s\t%s" % ("n_gram", "Unique_1", "Unique_2", "Common", "Ratio"))
    for i, (set1, set2) in enumerate(zip(mem1[1:], mem2[1:])):
        common = len(set1 & set2)
        dnr = min(len(set1), len(set2))
        ratio = common / dnr if dnr > 0 else 0
        print("%d\t%d\t%d\t%d\t%.4f" % (i+1, len(set1), len(set2), common, ratio))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser("""n-gram overlap between two text files""",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n', '--max-gram', type=int, help="Maximum N-Grams", default=7)
    parser.add_argument('-lc', action="store_true", help="Case insensitive match")
    parser.add_argument('file', nargs=2, help='Plain text input with white spaces between tokens.')
    args = vars(parser.parse_args())
    n = args['max_gram']
    assert n > 0
    assert len(args['file']) == 2
    first, second = args['file']
    find_overlap(first, second, n, lowercase=args.get("lc"))
