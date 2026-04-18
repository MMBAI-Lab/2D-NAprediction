"""RNAstructure Fold wrapper.

Writes sequence to a temp .seq file, runs `Fold` to produce a CT file,
then converts to dot-bracket using `ct2dot`. Requires DATAPATH env var.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from scripts.config import RNASTRUCTURE_DIR, RNASTRUCTURE_DATAPATH
from scripts.predictors.base import NAType, Prediction, Predictor


class RNAstructure(Predictor):
    name = "RNAstructure"

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        fold_bin = RNASTRUCTURE_DIR / "exe" / ("Fold" if na_type == "RNA" else "Fold-smp")
        ct2dot = RNASTRUCTURE_DIR / "exe" / "ct2dot"
        if not fold_bin.exists():
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error=f"binary not found: {fold_bin}")

        env = {**os.environ, "DATAPATH": str(RNASTRUCTURE_DATAPATH)}
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            seq_file = td / "in.seq"
            ct_file = td / "out.ct"
            bpseq_file = td / "out.bracket"
            seq_file.write_text(f";\nquery\n{sequence.upper()}1\n")

            dt1, proc = self._run(
                [str(fold_bin), str(seq_file), str(ct_file), "--MFE"]
                + (["--DNA"] if na_type == "DNA" else []),
                env=env,
            )
            if proc.returncode != 0:
                return Prediction(self.name, sequence, na_type, None, None,
                                  proc.stderr, dt1,
                                  error=proc.stderr.strip() or "Fold failed")

            dt2, proc2 = self._run(
                [str(ct2dot), str(ct_file), "1", str(bpseq_file)], env=env,
            )
            if proc2.returncode != 0 or not bpseq_file.exists():
                return Prediction(self.name, sequence, na_type, None, None,
                                  proc2.stderr, dt1 + dt2,
                                  error=proc2.stderr.strip() or "ct2dot failed")

            content = bpseq_file.read_text()
            lines = [ln for ln in content.splitlines() if ln.strip() and not ln.startswith(">")]
            dot_bracket = next((ln for ln in lines if re.fullmatch(r"[().]+", ln)), None)

            # Parse energy from the CT file first-line header: "... ENERGY = -X.Y  query"
            mfe = None
            first_line = ct_file.read_text().splitlines()[0] if ct_file.exists() else ""
            m = re.search(r"ENERGY\s*=\s*(-?[\d.]+)", first_line)
            if m:
                mfe = float(m.group(1))

            return Prediction(self.name, sequence, na_type,
                              dot_bracket=dot_bracket,
                              mfe_kcal_mol=mfe,
                              raw_output=content,
                              runtime_s=dt1 + dt2,
                              error=None if dot_bracket else "no dot-bracket parsed")
