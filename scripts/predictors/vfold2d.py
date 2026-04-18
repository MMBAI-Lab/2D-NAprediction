"""Vfold2D wrapper (Chen Lab, Univ. Missouri).

Drives the local `vfold2D_cl.out` binary built from
tools/VfoldPipeline_standalone/Vfold2D/src/. Falls back to the public
web service at rna.physics.missouri.edu if the binary is not present.

Input format (two lines, equal length):
  line 1: RNA sequence in AUGCaugc
  line 2: per-base constraint string. For unconstrained prediction, all '.'

Binary requires the env var `VfoldPipeline` pointing at the standalone root
so it can locate Vfold2D/INPUT/ for energy parameter files.

Output is written under -outpath=<dir>/<basename>.sym in two lines:
  <seq> free-energy(kcal/mol)
  <dot-bracket> <energy>

We call with -fast for 37 C single-pass prediction (faster, no SHAPE).
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from scripts.config import VFOLD2D_DIR
from scripts.predictors.base import NAType, Prediction, Predictor


VFOLD_ROOT = VFOLD2D_DIR.parent
LOCAL_BIN = VFOLD2D_DIR / "bin" / "vfold2D_cl.out"


class VFold2D(Predictor):
    name = "VFold2D"

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        if na_type != "RNA":
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error="Vfold2D is RNA-only")
        if not LOCAL_BIN.exists():
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error=f"binary not found: {LOCAL_BIN}")

        seq = sequence.upper().replace("T", "U")
        sym = "." * len(seq)

        env = {**os.environ, "VfoldPipeline": str(VFOLD_ROOT)}
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            in_file = td / "query.txt"
            in_file.write_text(f"{seq}\n{sym}\n")
            out_dir = td / "OUTPUT"
            out_dir.mkdir()

            cmd = [str(LOCAL_BIN), f"-outpath={out_dir}/", "-fast", str(in_file)]
            dt, proc = self._run(cmd, cwd=td, env=env)

            out_file = out_dir / "query.sym"
            if not out_file.exists():
                return Prediction(self.name, sequence, "RNA", None, None,
                                  proc.stdout + proc.stderr, dt,
                                  error=(proc.stderr.strip() or proc.stdout.strip()
                                         or "no .sym file produced"))

            lines = out_file.read_text().strip().splitlines()
            if len(lines) < 2:
                return Prediction(self.name, sequence, "RNA", None, None,
                                  out_file.read_text(), dt,
                                  error="malformed .sym output")

            m = re.match(r"^([().\[\]{}]+)\s+(-?[\d.]+)", lines[1].strip())
            if not m:
                return Prediction(self.name, sequence, "RNA", None, None,
                                  out_file.read_text(), dt,
                                  error="no dot-bracket parsed")
            db = m.group(1)
            mfe = float(m.group(2))
            return Prediction(self.name, sequence, "RNA",
                              dot_bracket=db, mfe_kcal_mol=mfe,
                              raw_output=out_file.read_text(),
                              runtime_s=dt)
