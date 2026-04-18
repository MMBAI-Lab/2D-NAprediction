"""ViennaRNA RNAfold wrapper.

Runs inside the nap-thermo env, where `RNAfold` is on PATH and the
Python binding `import RNA` is available. We invoke the binary via
subprocess for consistency with the other wrappers.
"""

from __future__ import annotations

import re

from scripts.config import ENV_THERMO, MICROMAMBA, MAMBA_ROOT
from scripts.predictors.base import NAType, Prediction, Predictor


class ViennaRNA(Predictor):
    name = "ViennaRNA"
    env = ENV_THERMO

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        seq = sequence.upper().replace("T", "U") if na_type == "RNA" else sequence.upper()
        cmd = [str(MICROMAMBA), "run", "-r", str(MAMBA_ROOT), "-n", self.env,
               "RNAfold", "--noPS"]
        if na_type == "DNA":
            # Approximation: Vienna uses the Turner RNA params; for DNA,
            # users usually call ViennaRNA's DNA parameter file.
            cmd += ["--paramFile=DNA"]
        dt, proc = self._run(cmd, stdin=seq + "\n")

        if proc.returncode != 0:
            return Prediction(self.name, sequence, na_type, None, None,
                              proc.stderr, dt, error=proc.stderr.strip() or "nonzero exit")

        # stdout: two lines — sequence then "struct ( mfe)"
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        if len(lines) < 2:
            return Prediction(self.name, sequence, na_type, None, None,
                              proc.stdout, dt, error="unexpected output")
        m = re.match(r"^([().]+)\s+\(\s*([-\d.]+)\s*\)", lines[1])
        if not m:
            return Prediction(self.name, sequence, na_type, None, None,
                              proc.stdout, dt, error="could not parse dot-bracket")
        return Prediction(self.name, sequence, na_type,
                          dot_bracket=m.group(1),
                          mfe_kcal_mol=float(m.group(2)),
                          raw_output=proc.stdout,
                          runtime_s=dt)
