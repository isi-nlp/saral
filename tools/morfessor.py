#!/usr/bin/env python
# Author: Thamme Gowda tg@isi.edu
# Crated on: October 30, 2017
"""
Morfessor utility for morphological segmentation of bitext data.


Note:
 1. Training can be done using `morfessor-train` command line tool.
 Example::
    morfessor-train -s morf-model.src.pkl 1A-v1-train.src
 2. Use only the training data split for the morfessor training
"""

import morfessor

def main(args):
    models = args['model']
    assert type(models) is list and len(models) >= 1
    models = [morfessor.MorfessorIO().read_binary_file(m) for m in models]
    multi = len(models) > 1
    out = args['output']
    delim = args.get('delim', '\t')
    for line in args['input']:
        cols = line.strip().split(delim) if multi else [line.strip()]
        res = []
        assert len(cols) == len(models), "Cols %d == Models %d ?" % (len(cols), len(models))
        for i, col in enumerate(cols):
            tokens = col.split()
            morphs = [models[i].viterbi_segment(w) for w in tokens]
            morphems = []
            for j, (parts, conf) in enumerate(morphs):
                #print("%s --> %s :: %f" % (tokens[j], parts, conf))
                # todo filter
                morphems.append(' '.join(parts))
            #print(morphems)
            res.append(' '.join(morphems))
        out.write(delim.join(res))
        out.write('\n')


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser("""Morfessor.""")
    parser.add_argument('model', nargs='+', help='Morfessor model, one per text column (for TSV)')
    parser.add_argument('-in', '--input', help='Input file. Default=STDIN', default=sys.stdin, type=argparse.FileType('r'))
    parser.add_argument('-out', '--output', help='Output file. DEFAULT=STDOUT', default=sys.stdout, type=argparse.FileType('w'))
    args = vars(parser.parse_args())
    main(args)

