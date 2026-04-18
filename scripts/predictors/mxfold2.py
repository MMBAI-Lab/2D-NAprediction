"""MXfold2 wrapper — invokes the mxfold2 CLI inside nap-hybrid env."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from scripts.config import ENV_HYBRID, MICROMAMBA, MAMBA_ROOT
from scripts.predictors.base import NAType, Prediction, Predictor


class MXfold2(Predictor):
    name = "MXfold2"
    env = ENV_HYBRID

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        # RNA-trained model: transcribe T->U regardless of na_type so DNA
        # inputs don't feed unknown bases into the scoring function.
        seq = sequence.upper().replace("T", "U")
        with tempfile.NamedTemporaryFile("w", suffix=".fa", delete=False) as f:
            f.write(f">query\n{seq}\n")
            fa = Path(f.name)
        try:
            cmd = [str(MICROMAMBA), "run", "-r", str(MAMBA_ROOT), "-n", self.env,
                   "mxfold2", "predict", str(fa)]
            dt, proc = self._run(cmd)
        finally:
            fa.unlink(missing_ok=True)

        if proc.returncode != 0:
            return Prediction(self.name, sequence, na_type, None, None,
                              proc.stderr, dt,
                              error=proc.stderr.strip() or "nonzero exit")

        # Format: ">id\nSEQ\n((....)) (energy)"
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        db = None
        mfe = None
        for ln in lines:
            m = re.match(r"^([().]+)(?:\s+\(\s*([-\d.]+)\s*\))?\s*$", ln.strip())
            if m:
                db = m.group(1)
                mfe = float(m.group(2)) if m.group(2) else None
                break
        return Prediction(self.name, sequence, na_type,
                          dot_bracket=db,
                          mfe_kcal_mol=mfe,
                          raw_output=proc.stdout,
                          runtime_s=dt,
                          error=None if db else "could not parse")
