#!/usr/bin/env python
import numpy as np
import sys
import argparse

def line_to_ratio(line):
    cols = line.split('\t')
    s1, s2 = cols[0] if cols else "", cols[1] if len(cols) > 1 else ""
    s1, s2 = s1.strip().split(), s2.strip().split()
    return (1.0 + len(s1)) / (1.0 + len(s2))

def gaussian(inp):
    arr = list(map(line_to_ratio, inp))
    arr = np.array(arr)
    return arr.mean(), arr.std()

def filter_parallel(inp, low, high, flip=False):
    assert flip in (True, False)
    for line in inp:
        ratio = line_to_ratio(line)
        is_in =low <= ratio <= high
        if flip != is_in: # exclusive or
            yield line

def main(inp, out, deviations=2.0, flip=False):
    with open(inp) as fi:
        mean, std = gaussian(fi)
    devs = deviations * std
    low, high = mean - devs, mean + devs

    with open(inp) as fi:
        for line in filter_parallel(fi, low, high, flip):
            out.write(line)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='filter lines')
    parser.add_argument('-i', '--inp', required=True)
    parser.add_argument('-o', '--out', default=sys.stdout,
                        type=argparse.FileType('w', encoding='utf-8', errors='ignore'))
    parser.add_argument('-f', '--flip', action='store_true', help="flip the filter criteria")
    parser.add_argument('-d', '--deviations', type=float, default=2, help="How many standard deviations?")
    args = vars(parser.parse_args())
    main(**args)
