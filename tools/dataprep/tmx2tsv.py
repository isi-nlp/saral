#!/usr/bin/env python
"""
this script extract parallel sentences from a .tmx xml file

Author: Thamme Gowda [tg at isi dot edu]
Date: April 12,  2019
"""

import sys
from lxml import etree
import argparse
import logging as log

log.basicConfig(level=log.INFO)


def filter_segments(xmlfile):
    """
    streaming read XML
    """
    assert isinstance(xmlfile, str)
    log.info(f"Reading from {xmlfile}")
    doc = etree.iterparse(xmlfile, events=('start', 'end'))
    _, root = next(doc)
    i = 0
    for event, element in doc:
        if event == 'end' and element.tag == 'tu':
            #print(element)
            if i == 0: # initialize
                langs = element.xpath('.//tuv/@xml:lang')
                log.info(f"found languages = {langs}")
            else: # validate
                assert langs == element.xpath('.//tuv/@xml:lang')
            segs = element.xpath('.//seg/text()')
            assert len(langs) == len(segs)
            yield segs
            root.clear()
            i += 1
    log.info(f"read {i} segments")

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-i', '--inp', help='input .tmx xml file', required=True)
    p.add_argument('-o', '--out', help="output file, default is STDOUT", default=sys.stdout,
                   type=argparse.FileType('w', encoding='utf8', errors='ignore'))
    args = p.parse_args()
    return args.inp, args.out


def write_segments(segs, out):
    i = 0
    for seg in segs:
        line = '\t'.join(seg) + '\n'
        out.write(line)
        i += 1
    log.info(f"Wrote {i} lines to {out.name}")


if __name__ == '__main__':
    inp, out = parse_args()
    segs = filter_segments(inp)
    write_segments(segs, out)
