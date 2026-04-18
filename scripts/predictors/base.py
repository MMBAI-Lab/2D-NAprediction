from __future__ import annotations

import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

NAType = Literal["RNA", "DNA"]


@dataclass
class Prediction:
    tool: str
    sequence: str
    na_type: NAType
    dot_bracket: Optional[str]
    mfe_kcal_mol: Optional[float]
    raw_output: str
    runtime_s: float
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.dot_bracket is not None


class Predictor(ABC):
    name: str
    env: Optional[str] = None
    version: Optional[str] = None

    @abstractmethod
    def predict(self, sequence: str, na_type: NAType = "RNA") -> Prediction:
        ...

    def _run(self, cmd, stdin: Optional[str] = None, cwd: Optional[Path] = None,
             env: Optional[dict] = None, timeout: int = 600) -> tuple[float, subprocess.CompletedProcess]:
        t0 = time.monotonic()
        proc = subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            env=env,
            timeout=timeout,
            check=False,
        )
        return time.monotonic() - t0, proc


def _in_env(env_name: str, python_snippet: str, repo_root: Path) -> subprocess.CompletedProcess:
    """Run a Python snippet inside a micromamba env. Used by wrappers that import native bindings."""
    from scripts.config import MICROMAMBA, MAMBA_ROOT
    return subprocess.run(
        [str(MICROMAMBA), "run", "-r", str(MAMBA_ROOT), "-n", env_name, "python", "-c", python_snippet],
        capture_output=True, text=True, check=False,
    )
