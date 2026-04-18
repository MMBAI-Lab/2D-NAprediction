"""IPknot wrapper.

IPknot predicts RNA secondary structures including pseudoknots via integer
programming. Output is a FASTA-like 3-line block:
    >name
    <sequence>
    <dot-bracket with optional [] {} for pseudoknot levels>

The binary links dynamically against the ViennaRNA shared lib from the
nap-thermo conda env, so we set LD_LIBRARY_PATH accordingly.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from scripts.config import IPKNOT_BIN, MAMBA_ROOT
from scripts.predictors.base import NAType, Prediction, Predictor


# ViennaRNA shared-lib path from nap-thermo env
_VIENNA_LIB = MAMBA_ROOT / "envs" / "nap-thermo" / "lib"
_DB_CHARS = re.compile(r"^[().\[\]{}<>]+$")


class IPknot(Predictor):
    name = "IPknot"

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        if na_type != "RNA":
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error="IPknot is RNA-only")
        if not IPKNOT_BIN.exists():
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error=f"binary not found: {IPKNOT_BIN}")

        seq = sequence.upper().replace("T", "U")
        env = {
            **os.environ,
            "LD_LIBRARY_PATH": f"{_VIENNA_LIB}:{os.environ.get('LD_LIBRARY_PATH','')}",
        }

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            fa = td / "query.fa"
            fa.write_text(f">query\n{seq}\n")
            dt, proc = self._run([str(IPKNOT_BIN), str(fa)], env=env)

        if proc.returncode != 0:
            return Prediction(self.name, sequence, "RNA", None, None,
                              proc.stderr, dt,
                              error=proc.stderr.strip() or "ipknot failed")

        db = next((ln.strip() for ln in proc.stdout.splitlines()
                   if _DB_CHARS.fullmatch(ln.strip())), None)
        return Prediction(self.name, sequence, "RNA", db, None, proc.stdout, dt,
                          error=None if db else "no dot-bracket line found")
