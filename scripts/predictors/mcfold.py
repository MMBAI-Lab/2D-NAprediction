"""MC-Fold wrapper.

Two modes, auto-selected at runtime:
  * LOCAL  — if `tools/mc-fold/bin/mcfold-dp` exists, call it.
  * WEB    — otherwise POST to the IRIC mcfold.static.cgi endpoint.

Web mode sends a multipart form with pass=lucy (shared academic password
published in the MC-Fold docs). The response is HTML containing a Top-50
list; we parse the rank-1 dot-bracket as the MC-Fold prediction.

Responses are cached under tools/mc-fold/cache/<sha1>.txt and requests
are rate-limited to one per _web_cooldown_s seconds.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
import time
from pathlib import Path

from scripts.config import MCFOLD_BIN, MCFOLD_WEB, MCFOLD_WEB_PASS, TOOLS
from scripts.predictors.base import NAType, Prediction, Predictor


CACHE_DIR = TOOLS / "mc-fold" / "cache"
# rank-1 structure line: "   1) (((...)))  [...]"
_RANK1_RE = re.compile(r"^\s*1\)\s+([().]+)\s", re.MULTILINE)


class MCFold(Predictor):
    name = "MC-Fold"
    _last_web_call: float = 0.0
    _web_cooldown_s: float = 5.0
    _web_timeout_s: int = 300

    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        if na_type != "RNA":
            return Prediction(self.name, sequence, na_type, None, None, "",
                              0.0, error="MC-Fold is RNA-only")
        seq = sequence.upper().replace("T", "U")
        if MCFOLD_BIN.exists():
            return self._local(seq)
        return self._web(seq)

    def _local(self, seq: str) -> Prediction:
        with tempfile.NamedTemporaryFile("w", suffix=".fa", delete=False) as f:
            f.write(f">query\n{seq}\n")
            fa = Path(f.name)
        try:
            dt, proc = self._run([str(MCFOLD_BIN), str(fa)])
        finally:
            fa.unlink(missing_ok=True)
        if proc.returncode != 0:
            return Prediction(self.name, seq, "RNA", None, None, proc.stderr, dt,
                              error=proc.stderr.strip() or "nonzero exit")
        m = _RANK1_RE.search(proc.stdout)
        db = m.group(1) if m else None
        return Prediction(self.name, seq, "RNA", db, None, proc.stdout, dt,
                          error=None if db else "parse failed")

    def _web(self, seq: str) -> Prediction:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(seq.encode()).hexdigest()
        cache = CACHE_DIR / f"{key}.html"

        if cache.exists():
            body = cache.read_text(encoding="utf-8", errors="replace")
            m = _RANK1_RE.search(body)
            db = m.group(1) if m else None
            return Prediction(self.name, seq, "RNA", db, None, body, 0.0,
                              error=None if db else "cached response had no rank-1 structure")

        delta = time.monotonic() - MCFold._last_web_call
        if delta < self._web_cooldown_s:
            time.sleep(self._web_cooldown_s - delta)

        # Using curl mirrors the reference invocation in the MC-Fold docs:
        #   curl -Y 0 -y 300 -F pass=lucy -F sequence=... <url>
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                ["curl", "-sS", "-Y", "0", "-y", str(self._web_timeout_s),
                 "-F", f"pass={MCFOLD_WEB_PASS}",
                 "-F", f"sequence={seq}",
                 MCFOLD_WEB],
                capture_output=True, timeout=self._web_timeout_s + 60,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            return Prediction(self.name, seq, "RNA", None, None, "", 0.0,
                              error=f"web request timed out after {e.timeout}s")
        dt = time.monotonic() - t0
        MCFold._last_web_call = time.monotonic()

        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            return Prediction(self.name, seq, "RNA", None, None, err, dt,
                              error=f"curl failed ({proc.returncode}): {err}")

        body = proc.stdout.decode("utf-8", errors="replace")
        cache.write_text(body)
        m = _RANK1_RE.search(body)
        db = m.group(1) if m else None
        return Prediction(self.name, seq, "RNA", db, None, body, dt,
                          error=None if db else "web response had no rank-1 structure")
