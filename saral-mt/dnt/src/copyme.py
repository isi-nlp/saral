#!/usr/bin/env python3

# PBS -l walltime=5:00:00
# PBS -q isi

# code by Jon May [jonmay@isi.edu]
import argparse
import sys
import codecs
import os.path
import gzip
import tempfile
import shutil
import atexit

import skip
import unicodedata as ud

scriptdir = os.path.dirname(os.path.abspath(__file__))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def is_punct(tok):
    """
    :param tok: token
    :return: True if token is made of only punctuation characters; False otherwise
    """
    for x in tok:
        if ud.category(x)[0] != 'P':
            return False
    return True


def prepfile(fh, code):
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


# TODO: adapt to ulf-mode so no external file needed
def main():
    parser = argparse.ArgumentParser(description="given flat text file guess if each word should be copied",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    addonoffarg(parser, 'debug', help="debug mode", default=False)
    parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
    parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help="output file")
    parser.add_argument("--dict", "-D", default=None, type=argparse.FileType('r'), help="dictionary to filter against")
    parser.add_argument("--antidict", "-N", default=None, type=argparse.FileType('r'),
                        help="dictionary of terms to include")

    parser.add_argument("--copysymbol", default="@@", help="how to mark")
    parser.add_argument("-ep", "--exclude-puncts", default=False, action='store_true', help="Exclude Punctuations")
    parser.add_argument("--version", "-v", type=int, default=5, help="what version of skip heuristcs")
    workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

    try:
        args = parser.parse_args()
    except IOError as msg:
        parser.error(str(msg))
        sys.exit(2)

    def cleanwork():
        shutil.rmtree(workdir, ignore_errors=True)

    if args.debug:
        print(workdir)
    else:
        atexit.register(cleanwork)

    infile = prepfile(args.infile, 'r')
    outfile = prepfile(args.outfile, 'w')
    if args.dict is not None:
        dictfile = prepfile(args.dict, 'r')
        DICT = set()
        for line in dictfile:
            DICT.add(line.strip().lower())
        skip.setdict(DICT)

    if args.antidict is not None:
        antidictfile = prepfile(args.antidict, 'r')
        ANTIDICT = set()
        for line in antidictfile:
            ANTIDICT.add(line.strip().lower())
        skip.setantidict(ANTIDICT)

    for line in infile:
        otoks = []
        skipcount = 0
        for tok in line.strip().split():
            if args.exclude_puncts and is_punct(tok):
                outcome, tok = False, tok
            else:
                outcome, tok = skip.skip(tok, args.version)
            if outcome:
                tok = "{}{}".format(args.copysymbol, tok)
                skipcount += 1
            otoks.append(tok)
        # skip all if skipping most
        if args.version >= 4 and (skipcount + 0.0) / len(otoks) > 0.75:
            otoks = ["{}{}".format(args.copysymbol, x) for x in line.strip().split()]
        outfile.write(' '.join(otoks) + "\n")


if __name__ == '__main__':
    main()
