#!/usr/bin/env python3
# code by Jon May [jonmay@isi.edu]

import re
import string
import unicodedata as ud

DICT = set()
ANTIDICT = set()


def setdict(thedict):
    global DICT
    DICT = thedict


def setantidict(theantidict):
    global ANTIDICT
    ANTIDICT = theantidict


def haspunc(tok, v=1):
    ''' returns true any character is punc or symbol '''
    if v < 1: return False
    solveset = set(['S', 'P'])
    for x in tok:
        if ud.category(x)[0] in solveset and x != "'":
            return True
    return False


def hasdigit(tok, v=1):
    ''' returns true if any character is a digit '''
    if v < 1: return False
    for x in tok:
        if x.isdigit():
            return True
    return False


def hasnonlatin(tok, v=3):  # v3
    ''' returns true if any character is a letter but not A-Za-z '''
    if v < 3: return False
    az = set(string.ascii_letters)
    for x in tok:
        if ud.category(x)[0] == "L" and x not in az:
            return True
    return False


def laughter(tok, v=3):  # v3
    ''' returns true if it looks like laughing '''
    if v < 3: return False
    return re.match("h[ha]+y?$", tok, flags=re.I) is not None


def dictmatches(tok, v=2):
    ''' returns true if in english dict but not in il6 dict '''
    if v < 2: return False
    return (tok.lower() in DICT and tok.lower() not in ANTIDICT)


def rt(tok, v=1):
    return re.match("rt$", tok, flags=re.I) is not None


def ethiopia(tok, v=3):
    if v < 3: return False
    return re.match("ethiopia", tok, flags=re.I)


ORGLIST = ["ABO", "TPLF", "WBO", "OPDO", "QBO", "FXG", "FDG", "OMN"]


def orgs(tok, v=5):
    if v < 5:
        return False, tok
    for org in ORGLIST:
        if tok.startswith(org):
            return True, org
    return False, tok


def skip(token, v=3):
    ''' heuristics to skip replacement '''
    ret, token = orgs(token, v)
    ret = ret or token.startswith("@") or \
          token.startswith("#") or \
          "http" in token or \
          rt(token, v) or \
          ethiopia(token, v) or \
          haspunc(token, v) or \
          hasdigit(token, v) or \
          dictmatches(token, v) or \
          hasnonlatin(token, v) or \
          laughter(token, v)
    return ret, token
