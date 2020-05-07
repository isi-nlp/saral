#!/usr/bin/env python
import argparse
from pathlib import Path
import logging as log
import re
import sys
import subprocess
from typing import List

script_dir = Path(__file__).parent
sys.path.append(str(script_dir))
from ssplit_tsv_len import ssplit_tsv_len

tsv_tok_script = script_dir / 'ulftok-tsv.sh'
assert tsv_tok_script.exists()

log.basicConfig(level=log.INFO)

def asr_to_mt_path(file: Path, out_dir: Path, lang: str, split: str, unfused: bool=False) -> Path:
    name = file.name
    assert name.endswith(".txt")
    name = name.replace(".txt", ".src.tsv")
    name = name.replace(lang, lang + '-asr')
    dir =  out_dir / split / (lang + '-asr') 
    if unfused:
        dir = dir / 'unfused'
    return dir / name

def line_mapper(mapper, inp: Path, out: Path, skip_empty=False) -> int:
    ct = 0
    skips = 0
    if not out.parent.exists():
        log.info(f"Create dir {out.parent}")
        out.parent.mkdir(exist_ok=True, parents=True)
    with inp.open('r', encoding='utf8', errors='ignore') as inp, \
            out.open('w', encoding='utf8', errors='ignore') as out:
        for line in inp:
            line = mapper(line)
            if skip_empty and not line:
                skips += 1
                continue
            out.write(line)
            out.write('\n')
            ct += 1
    return (ct, skips) if skip_empty else ct


def ulf_tok_tsv(inp: Path, out: Path, dry_run: bool = False, overwrite=True):
    if overwrite and out.exists():
        log.info(f"Overwrite {out}")
        if not dry_run:
            out.unlink()
    cmd = [str(tsv_tok_script), str(inp), str(out)]
    log.info('Run : ' + f' '.join(cmd))
    if not dry_run:
        subprocess.run(cmd)


def asr_to_mt_copy(asr: Path, mt: Path, dry_run=False):
    log.info(f"Copy: {asr} --> {mt}")
    if dry_run:
        return
    tags_patrn = re.compile("<[a-z-]+>")

    def mapper(line):
        parts = line.split()
        id, txt = parts[0], ' '.join(parts[1:])
        txt = tags_patrn.sub('…', txt)
        return f'{id}\t{txt}'

    line_mapper(mapper=mapper, inp=asr, out=mt)

def get_tsv_column(tsv: Path, col_idx, delim='\t'):
    with tsv.open('r', encoding='utf8', errors='ignore') as inp:
        cols = (line.split(delim)[col_idx] for line in inp)
        cols = (c.strip() for c in cols)
        yield from cols


def write_lines(out: Path, lines):
    with out.open('w', encoding='utf8', errors='ignore') as w:
        for line in lines:
            w.write(line)
            w.write('\n')


def create_ids(tsv: Path, dry_run=False):
    ids_file = tsv.parent / (tsv.name.split('.')[0] + '.ids')
    log.info(f"Create ids file {ids_file}")
    if dry_run:
        return
    ids_col = get_tsv_column(tsv, col_idx=0)
    write_lines(ids_file, ids_col)


def create_ssplit(inp_tsv, out_tsv, max_len=80, dry_run=False):
    log.info(f'SSPLIT: {inp_tsv} --> {out_tsv}; max_len={max_len}')
    if dry_run:
        return
    with inp_tsv.open('r', encoding='utf8', errors='ignore') as inp,\
         out_tsv.open('w', encoding='utf8', errors='ignore') as out:
        ssplit_tsv_len(inp, out, max_len)


def main(lang: str, splits: List[str], asr_dir: Path, mt_dir: Path, dry_run: bool=False,
         unfused:bool=False, **args):
    if isinstance(splits, str):
        splits = [splits]

    for split in splits:
        in_dir = asr_dir / split
        log.info(f"Inside {in_dir}")
        assert in_dir.exists(), in_dir

        in_dir = in_dir / lang
        if unfused:
            in_dir = in_dir / 'unfused'
        assert in_dir.exists()

        asr_files = list(in_dir.glob("*.txt"))
        log.info(f"Found {len(asr_files)} in {in_dir}")
        assert asr_files
        pairs = [(a, asr_to_mt_path(a, out_dir=mt_dir, lang=lang, split=split, unfused=unfused)) for a in asr_files]
        # remove existing files
        pairs = [(asr, mt) for asr, mt in pairs if not mt.exists()]
        log.info(f"Found {len(pairs)} asr files with missing MT counterparts")

        for asr, mt in pairs:
            asr_to_mt_copy(asr, mt, dry_run=dry_run)
            tok_out = mt.parent / mt.name.replace('.tsv', '.tok.tsv')
            ulf_tok_tsv(inp=mt, out=tok_out, dry_run=dry_run)
            create_ids(mt, dry_run=dry_run)
            ssplit_out = tok_out.parent / tok_out.name.replace('-asr', '-asr-ssplit')
            create_ssplit(tok_out, ssplit_out, dry_run=dry_run)
            create_ids(ssplit_out,  dry_run=dry_run)
        log.info("All Done")

def parse_args():
    parser = argparse.ArgumentParser(description='asrout to mt out')
    parser.add_argument('-l', '--lang', required=True, help="lang code such as 1A, 1B, 2B etc ")
    parser.add_argument('-s', '--splits', nargs='+', help="split such as analysis dev etc")
    parser.add_argument('-ad', '--asr-dir', required=True, type=Path)
    parser.add_argument('-md', '--mt-dir', required=True, type=Path)
    parser.add_argument('-dr', '--dry-run', action='store_true',
                        help='Dont actually Run, just do a dry run.')
    parser.add_argument('-un', '--unfused', action='store_true',
                        help='process unfused subdir contents of asr-out/<split>/<lang>.')
    return vars(parser.parse_args())


if __name__ == "__main__":
    main(**parse_args())
