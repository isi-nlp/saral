#!/usr/bin/env python3
# boilerplate code by Jon May (jonmay@isi.edu)
import argparse
import sys
import codecs

import os.path
import gzip
import tempfile
import shutil
import atexit
import unicodedata as ud

scriptdir = os.path.dirname(os.path.abspath(__file__))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
    if type(fh) is str:
        fh = open(fh, code)
    ret = gzip.open(fh.name, code if code.endswith("t") else code + "t") if fh.name.endswith(".gz") else fh
    if sys.version_info[0] == 2:
        if code.startswith('r'):
            ret = reader(fh)
        elif code.startswith('w'):
            ret = writer(fh)
        else:
            sys.stderr.write("I didn't understand code " + code + "\n")
            sys.exit(1)
    return ret


def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
    ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
    group = parser.add_mutually_exclusive_group()
    dest = arg if dest is None else dest
    group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
    group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)


def ispunc(word):
    ''' return true if all characters of word are punctuation '''
    for char in word:
        if not ud.category(char).startswith('P'):
            return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="mark source tokens as T(ranslate), (do) N(ot translate), or P(unctuation) "
                    "based on simple heuristic of finding token on target side",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    addonoffarg(parser, 'debug', help="debug mode", default=False)
    parser.add_argument("--srcfile", "-s", nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help="input src file")
    parser.add_argument("--trgfile", "-t", nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help="input trg file")
    parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help="output label file")

    try:
        args = parser.parse_args()
    except IOError as msg:
        parser.error(str(msg))

    workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

    def cleanwork():
        shutil.rmtree(workdir, ignore_errors=True)

    if args.debug:
        print(workdir)
    else:
        atexit.register(cleanwork)

    srcfile = prepfile(args.srcfile, 'r')
    trgfile = prepfile(args.trgfile, 'r')
    outfile = prepfile(args.outfile, 'w')

    for srcline, trgline in zip(srcfile, trgfile):
        trgset = set()
        for word in trgline.strip().lower().split():
            if not ispunc(word):
                trgset.add(word)
        outline = []
        for word in srcline.strip().lower().split():
            if ispunc(word):
                outline.append('P')
            elif word in trgset:
                outline.append('N')
            else:
                outline.append('T')
        outfile.write(' '.join(outline) + "\n")


if __name__ == '__main__':
    main()
