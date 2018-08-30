#!/usr/bin/env python
# Author TG; Created Aug 23, 2018

import argparse
import sys
from typing import TextIO, Iterator, Union
import logging as log

log.basicConfig(level=log.DEBUG)
TextStream = Union[Iterator[str], TextIO]


def len_ratio(list1, list2, smoothing=1.0):
    """
    Computes the length ratio between two sequences with smoothing
    :param list1:
    :param list2:
    :param smoothing:
    :return:
    """
    l1, l2 = len(list1), len(list2)
    return (min(l1, l2) + smoothing) / (max(l1, l2) + smoothing)


def fallback_combine(src: TextStream, hyp: TextStream, fallback: TextStream, threshold):
    """
    uses fall back model outputs to fix or combine occasional breakdown of main model
    :param src: source sentences
    :param hyp: hypothesis from main translation model
    :param fallback: hypothesis from fallback translational model
    :param threshold: threshold to trigger the fallback
    :return: iterator of sentences
    """
    fix_count = 0
    tot_count = 0
    for src_sent, hyp_sent, fb_sent in zip(src, hyp, fallback):  # fb stands for fall back
        src_sent, hyp_sent, fb_sent = src_sent.strip(), hyp_sent.strip(), fb_sent.strip()
        src_toks, hyp_toks, fb_toks = src_sent.split(), hyp_sent.split(), fb_sent.split()
        hyp_ratio = len_ratio(src_toks, hyp_toks)
        out_sent = hyp_sent
        if hyp_ratio <= threshold:
            fb_ratio = len_ratio(src_toks, fb_toks)
            fix_count += 1
            if fb_ratio > threshold:
                log.debug(f"Using Fallback:SRC:{src_sent} \t HYP:{hyp_sent} \t FALLBACK:{fb_sent}")
                out_sent = fb_sent
            else:
                log.debug(f"Restoring Source:SRC:{src_sent} \t HYP:{hyp_sent} \t FALLBACK:{fb_sent}")
                out_sent = src_sent
        tot_count += 1
        yield out_sent.strip()
    log.info(f"Fixed {fix_count} sentences of {tot_count}; ratio={fix_count/tot_count}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='A tool to fix occational buggy translations using a '
                                            'fallback model')
    p.add_argument('-s', '--src', help='Source', type=argparse.FileType('r'), default=sys.stdin)
    p.add_argument('-m', '--hyp', '--mt', dest='hyp', help='hypothesis from unreliable model',
                   type=argparse.FileType('r'), default=sys.stdin)
    p.add_argument('-f', '--fallback', help='Fall back hypothesis from second model',
                   type=argparse.FileType('r'), default=sys.stdin)
    p.add_argument('-o', '--out', help='File to write output.', type=argparse.FileType('w'),
                   default=sys.stdout)
    p.add_argument('-t', '--threshold', help='Length ratio threshold', type=float, default=0.33)

    args = p.parse_args()
    if sys.stdin == args.src == args.fallback == args.hyp:
        raise Exception('Invalid args, stdin can be argument fp=or -s, -h or -f, but not both')
    args = vars(args)
    out = args.pop('out')
    for line in fallback_combine(**args):
        out.write(line + '\n')
