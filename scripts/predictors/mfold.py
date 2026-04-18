"""mfold 3.6 (Zuker) wrapper.

Drives the `mfold` shell script (installed under tools/mfold-3.6/install/bin/)
which fans out to Fortran kernels and writes a family of files into the CWD:
  <prefix>.ct        — multi-structure CT, header line per structure
  <prefix>_1.ct ...  — per-structure CTs when MAX>1 produces alternates
  <prefix>.dG, .det, .plot, .ann, .h-num, .ss-count, ...

We pick the lowest-energy structure (the first one in <prefix>.ct) and
convert it to dot-bracket. mfold can output pseudoknot-free MFE structures
only.

Slot history: this predictor was previously called "UNAFold" in the pipeline
because the original install script targeted unafold.org's hybrid-ss-min.
The actual installed tool is mfold-3.6, so the predictor is renamed.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from scripts.config import MFOLD_BIN, MFOLD_DATA
from scripts.predictors.base import NAType, Prediction, Predictor


def _ct_to_dot_bracket(ct_text: str) -> tuple[str | None, float | None]:
    """Parse the FIRST structure block in a (possibly multi-structure) CT file."""
    lines = ct_text.strip().splitlines()
    if not lines:
        return None, None
    header = lines[0]

    # Header looks like: "  76  dG = -22.4   query"  OR  "76  ENERGY = -22.4  query"
    m_dg = re.search(r"(?:dG|ENERGY)\s*=\s*(-?[\d.]+)", header)
    mfe = float(m_dg.group(1)) if m_dg else None
    m_n = re.match(r"\s*(\d+)", header)
    if not m_n:
        return None, mfe
    n = int(m_n.group(1))

    pairs = {}
    for ln in lines[1 : n + 1]:
        parts = ln.split()
        if len(parts) < 5:
            continue
        try:
            idx = int(parts[0])
            partner = int(parts[4])
        except ValueError:
            continue
        if 1 <= idx <= n and partner > idx:
            pairs[idx] = partner

    db = ["."] * n
    for i, j in pairs.items():
        db[i - 1] = "("
        db[j - 1] = ")"
    return "".join(db), mfe


class MFold(Predictor):
    name = "mfold"

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        if not MFOLD_BIN.exists():
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error=f"binary not found: {MFOLD_BIN}")

        # mfold's helper binaries (mfold_datdir, sir_graph, etc.) live in the
        # same bin dir and are looked up via PATH from inside the script.
        env = {**os.environ, "PATH": f"{MFOLD_BIN.parent}:{os.environ.get('PATH','')}"}

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            # nafold (the Fortran kernel) was compiled with a hardcoded
            # /usr/local/share/mfold/ data path regardless of ./configure's
            # --prefix. It falls back to CWD, so symlink the energy tables
            # in before running.
            for dat in MFOLD_DATA.glob("*.dat"):
                (td / dat.name).symlink_to(dat)

            seq_file = td / "query.seq"
            seq = sequence.upper()
            if na_type == "RNA":
                seq = seq.replace("T", "U")
            else:
                seq = seq.replace("U", "T")
            seq_file.write_text(f">query\n{seq}\n")

            cmd = [str(MFOLD_BIN), f"SEQ=query.seq", f"NA={na_type}"]
            dt, proc = self._run(cmd, cwd=td, env=env)

            ct = td / "query.ct"
            if not ct.exists():
                return Prediction(self.name, sequence, na_type, None, None,
                                  proc.stderr or proc.stdout, dt,
                                  error=(proc.stderr.strip() or proc.stdout.strip()
                                         or "no CT file produced"))

            db, mfe = _ct_to_dot_bracket(ct.read_text())
            return Prediction(self.name, sequence, na_type,
                              dot_bracket=db,
                              mfe_kcal_mol=mfe,
                              raw_output=ct.read_text(),
                              runtime_s=dt,
                              error=None if db else "parse failed")
