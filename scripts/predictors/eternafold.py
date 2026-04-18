"""EternaFold wrapper — contrafold binary invoked with EternaFold params."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from scripts.config import ETERNAFOLD_BIN, ETERNAFOLD_PARAMS
from scripts.predictors.base import NAType, Prediction, Predictor


class EternaFold(Predictor):
    name = "EternaFold"

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        if not ETERNAFOLD_BIN.exists():
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error=f"binary not found: {ETERNAFOLD_BIN}")

        seq = sequence.upper().replace("T", "U") if na_type == "RNA" else sequence.upper()
        with tempfile.NamedTemporaryFile("w", suffix=".fa", delete=False) as f:
            f.write(f">query\n{seq}\n")
            fa = Path(f.name)

        cmd = [str(ETERNAFOLD_BIN), "predict", str(fa)]
        if ETERNAFOLD_PARAMS.exists():
            cmd += ["--params", str(ETERNAFOLD_PARAMS)]
        try:
            dt, proc = self._run(cmd)
        finally:
            fa.unlink(missing_ok=True)

        if proc.returncode != 0:
            return Prediction(self.name, sequence, na_type, None, None,
                              proc.stderr, dt,
                              error=proc.stderr.strip() or "nonzero exit")

        db = next((ln.strip() for ln in proc.stdout.splitlines()
                   if re.fullmatch(r"[().]+", ln.strip())), None)
        return Prediction(self.name, sequence, na_type,
                          dot_bracket=db,
                          mfe_kcal_mol=None,
                          raw_output=proc.stdout,
                          runtime_s=dt,
                          error=None if db else "could not parse")
