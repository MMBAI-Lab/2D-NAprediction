"""CONTRAfold wrapper (subprocess).

Called with `predict <file>` — the binary expects a FASTA on disk and
writes structure to stdout in the format:
    >query
    ACGU...
    ((...))
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from scripts.config import CONTRAFOLD_BIN
from scripts.predictors.base import NAType, Prediction, Predictor


class CONTRAfold(Predictor):
    name = "CONTRAfold"

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        if not CONTRAFOLD_BIN.exists():
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error=f"binary not found: {CONTRAFOLD_BIN}")

        # RNA-trained model: transcribe T->U regardless of na_type so DNA
        # inputs don't feed unknown bases into the scoring function.
        seq = sequence.upper().replace("T", "U")
        with tempfile.NamedTemporaryFile("w", suffix=".fa", delete=False) as f:
            f.write(f">query\n{seq}\n")
            fa = Path(f.name)
        try:
            dt, proc = self._run([str(CONTRAFOLD_BIN), "predict", str(fa)])
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
                          mfe_kcal_mol=None,   # CONTRAfold gives log-prob, not ΔG
                          raw_output=proc.stdout,
                          runtime_s=dt,
                          error=None if db else "could not parse")
