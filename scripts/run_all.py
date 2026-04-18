#!/usr/bin/env python3
"""Run all predictors on a FASTA and write a CSV summary.

Usage:
    python scripts/run_all.py resources/my_aptamers.fa results/run_name
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# allow `python scripts/run_all.py` from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.predictors.contrafold import CONTRAfold
from scripts.predictors.eternafold import EternaFold
from scripts.predictors.ipknot import IPknot
from scripts.predictors.mcfold import MCFold
from scripts.predictors.mfold import MFold
from scripts.predictors.mxfold2 import MXfold2
from scripts.predictors.nupack import NUPACK
from scripts.predictors.rnastructure import RNAstructure
from scripts.predictors.vfold2d import VFold2D
from scripts.predictors.vienna import ViennaRNA

ALL_PREDICTORS = [
    ViennaRNA(), NUPACK(), RNAstructure(), MFold(),
    CONTRAfold(), EternaFold(), MCFold(),
    MXfold2(), VFold2D(), IPknot(),
]


def parse_fasta(path: Path):
    seq_id, seq = None, []
    with path.open() as fh:
        for line in fh:
            line = line.rstrip()
            if line.startswith(">"):
                if seq_id is not None:
                    yield seq_id, "".join(seq)
                seq_id = line[1:].split()[0] or "unnamed"
                seq = []
            elif line:
                seq.append(line)
        if seq_id is not None:
            yield seq_id, "".join(seq)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fasta", type=Path)
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--na", choices=["RNA", "DNA"], default="RNA")
    ap.add_argument("--only", nargs="*", default=None,
                    help="Restrict to a subset of predictor names")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    out_csv = args.outdir / "predictions.csv"

    predictors = ALL_PREDICTORS
    if args.only:
        names = {n.lower() for n in args.only}
        predictors = [p for p in predictors if p.name.lower() in names]

    with out_csv.open("w", newline="", buffering=1) as fh:
        w = csv.writer(fh)
        w.writerow(["seq_id", "tool", "na_type", "dot_bracket", "mfe_kcal_mol",
                    "runtime_s", "error"])
        fh.flush()
        for seq_id, seq in parse_fasta(args.fasta):
            for p in predictors:
                print(f"[{p.name}] {seq_id} ({len(seq)} nt)...", flush=True)
                r = p.predict(seq, na_type=args.na)
                w.writerow([seq_id, p.name, r.na_type,
                            r.dot_bracket or "", f"{r.mfe_kcal_mol:.2f}" if r.mfe_kcal_mol is not None else "",
                            f"{r.runtime_s:.3f}", r.error or ""])
                fh.flush()
                print(f"    -> {'OK' if r.ok else 'ERR: ' + (r.error or '?')} "
                      f"({r.runtime_s:.2f}s) {r.dot_bracket or ''}", flush=True)

    print(f"\nWrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
