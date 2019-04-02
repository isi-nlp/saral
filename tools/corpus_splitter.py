#!/usr/bin/env python

"""
Corpus Splitter
Splits one big corpus file into training, development and test sets. It makes random assignments subject to word count constraints set by user.

---

# Author : Thamme Gowda
# Created : October 20, 2017
"""

import argparse
import codecs
from collections import defaultdict
import random
from random import shuffle

import logging as log
log.basicConfig(level=log.INFO)

random.seed(100)    # to reproduce the same split


def tokenize(text):
    """
    very basic tokenizer using whitespace
    :param text:
    :return:
    """
    return text.split()


def parse_id(id):
    """
    splits id into doc_id and seg_id
    """
    parts = id.split('_')
    doc_id = '_'.join(parts[:-1])
    seg_id = parts[-1]
    return doc_id, seg_id

def assign_splits(path, dev_count, test_count, delim='\t'):

    index = defaultdict(int)
    log.info("Computing token and docs statistics of file %s" % path)
    seg_count = 0
    with codecs.open(path, 'r', 'utf8') as f:
        for line in f:
            id, src, tgt = line.strip().split(delim)
            doc_id, seg_id = parse_id(id)
            # counts target side
            text = tgt
            index[doc_id] += len(tokenize(text))
            seg_count += 1

    total_toks = sum(index.values())
    avg_toks = total_toks / float(len(index))
    doc_stats = list(index.items())
    shuffle(doc_stats)

    log.info("Found %d docs, %d total tokens, %d segments. Average tokens per doc = %f" %
             (len(index), total_toks, seg_count, avg_toks))

    # Assign buckets to each doc in the list
    bucket_labels = ['train', 'dev', 'test']
    # At first everything belongs to train, then we update them
    assignment = [0] * len(doc_stats)

    def random_select(total, assign_label, choose_from_label=0):
        """
        random assignment function
        :param total: total word count to be assigned
        :param assign_label: the label to be assigned
        :param choose_from_label: from this label
        :return: None
        """
        count = 0
        upper_bound = total + avg_toks
        attempts = 0
        max_attempts = 3 * total
        while count <= upper_bound and attempts <= max_attempts:
            idx = random.randint(0, len(doc_stats) - 1)
            doc_id, doc_tok_count = doc_stats[idx]
            if assignment[idx] == choose_from_label and doc_tok_count + count <= upper_bound:
                # assign this document
                assignment[idx] = assign_label
                count += doc_tok_count
            attempts += 1
        if attempts >= max_attempts and count < total - avg_toks:
            log.warning("Maximum attempts to split label %s exceeded. Not an optimal solution" % bucket_labels[assign_label])
        log.info("Assigned %d words to '%s'. requested %d which is %.2f%% of request" %
                 (count, bucket_labels[assign_label], total, 100.0 * count/total))

    # Next, make  dev and test assignment
    random_select(dev_count, 1)
    random_select(test_count, 2)

    # assignment stats
    counts = defaultdict(int)
    doc_assignments = {}
    label_stats = defaultdict(set)
    assert len(assignment) == len(doc_stats)
    for i, label in enumerate(assignment):
        doc_id, doc_tok_count = doc_stats[i]
        counts[bucket_labels[label]] += doc_tok_count
        doc_assignments[doc_id] = bucket_labels[label]
        label_stats[bucket_labels[label]].add(doc_id)
    return doc_assignments, dict(counts), label_stats


def split_records(path, out_prefix, assignment, delim='\t'):
    """
    Splits the records into multiple output files based on the assignment
    :param path:
    :param out_prefix:
    :param assignment:
    :param delim:
    :return:
    """
    names = set(assignment.values())
    files = {}
    for name in names:
        fp = "%s.%s.%s" % (out_prefix, name, path.split(".")[-1])
        log.info("%s records are written to %s" % (name, fp))
        files[name] = codecs.open(fp, 'w', 'utf8')
    with open(path) as inp:
        for line in inp:
            line = line.strip()
            doc_id, _ = parse_id(line.split(delim)[0])
            name = assignment[doc_id]
            files[name].write(line)
            files[name].write('\n')
    for name in names:
        files[name].close()


def write_label_assignment(assignment, path, count_stats):
    log.info("The split-assignment meta data is written to %s" % path)
    with open(path, 'w') as out:
        out.write("## Token Counts: %s \n" % count_stats)
        for label, items in assignment.items():
            out.write("# %s :\n" % label)
            out.write("\t %s \n" % ','.join(items))



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Corpus Splitter - makes test and dev"
             "splits, by isolating all segments of each document into a split, "
                                     "and also satisfies word count constraints set in commandline args.")
    parser.add_argument("-i", '--in', help="material data file", required=True)
    parser.add_argument("-o", '--out', help="Output prefix", required=True)
    parser.add_argument("-dev", '--dev', help="Development size in number of tokens", type=int, required=True)
    parser.add_argument("-test", '--test', help="Test Size in number of tokens", type=int, required=True)

    args = vars(parser.parse_args())
    doc_assignments, count_stats, label_assignments = assign_splits(args['in'], args['dev'], args['test'])
    split_records(args['in'], args['out'], doc_assignments)
    write_label_assignment(label_assignments, args['out'] + '-assignments.meta', count_stats)
