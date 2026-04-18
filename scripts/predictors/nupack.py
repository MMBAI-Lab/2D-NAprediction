"""NUPACK 4 wrapper — uses the Python API inside nap-thermo env."""

from __future__ import annotations

import json
import textwrap
import time

from scripts.config import ENV_THERMO, MICROMAMBA, MAMBA_ROOT
from scripts.predictors.base import NAType, Prediction, Predictor
import subprocess


class NUPACK(Predictor):
    name = "NUPACK4"
    env = ENV_THERMO

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        material = "rna" if na_type == "RNA" else "dna"
        snippet = textwrap.dedent(f"""
            import json, nupack
            seq = {sequence.upper()!r}
            model = nupack.Model(material={material!r}, celsius=37)
            mfe = nupack.mfe(strands=[seq], model=model)
            if not mfe:
                print(json.dumps({{"error": "no mfe"}})); raise SystemExit
            top = mfe[0]
            print(json.dumps({{
                "structure": str(top.structure),
                "energy": float(top.energy),
            }}))
        """)
        t0 = time.monotonic()
        proc = subprocess.run(
            [str(MICROMAMBA), "run", "-r", str(MAMBA_ROOT), "-n", self.env, "python", "-c", snippet],
            capture_output=True, text=True, check=False,
        )
        dt = time.monotonic() - t0

        if proc.returncode != 0:
            return Prediction(self.name, sequence, na_type, None, None,
                              proc.stderr, dt, error=proc.stderr.strip() or "nonzero exit")
        try:
            data = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return Prediction(self.name, sequence, na_type, None, None,
                              proc.stdout, dt, error="could not parse JSON output")
        if "error" in data:
            return Prediction(self.name, sequence, na_type, None, None,
                              proc.stdout, dt, error=data["error"])
        return Prediction(self.name, sequence, na_type,
                          dot_bracket=data["structure"],
                          mfe_kcal_mol=data["energy"],
                          raw_output=proc.stdout,
                          runtime_s=dt)
