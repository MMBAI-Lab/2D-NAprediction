#!/usr/bin/env bash
set -euo pipefail

# MC-Fold distribution is fragile. Strategy (in order):
#   (a) Try MC-Fold-DP (C++ reimplementation by Zakov) from GitHub.
#   (b) If that fails, fall back to a web-service wrapper (implemented
#       in scripts/predictors/mcfold.py, no local install needed).
#
# We prefer MC-Fold-DP because it produces deterministic, offline
# dot-bracket output compatible with the rest of the pipeline.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MC_DIR="$REPO_ROOT/tools/mc-fold"
mkdir -p "$MC_DIR"

if [[ -x "$MC_DIR/bin/mcfold-dp" ]]; then
  echo "[22] MC-Fold-DP already built at $MC_DIR/bin/mcfold-dp"
  exit 0
fi

REPO_URL="https://github.com/major-lab/MC-Fold-DP.git"
SRC="$MC_DIR/src"

if [[ ! -d "$SRC/.git" ]]; then
  echo "[22] Cloning $REPO_URL ..."
  if ! git clone "$REPO_URL" "$SRC"; then
    echo "[22] WARN: clone failed. Will rely on web-service wrapper."
    echo "[22] See scripts/predictors/mcfold.py for the fallback implementation."
    exit 0
  fi
fi

pushd "$SRC" >/dev/null
echo "[22] Building MC-Fold-DP (inside nap-learning env for Boost/GSL)..."
source "$REPO_ROOT/.envrc"
if [[ -f Makefile ]]; then
  micromamba run -n nap-learning bash -c "make -j$(nproc)"
elif [[ -f CMakeLists.txt ]]; then
  mkdir -p build && cd build && micromamba run -n nap-learning bash -c "cmake .. && make -j$(nproc)"
else
  echo "[22] ERROR: no known build file in repo. Inspect $SRC."
  exit 1
fi
popd >/dev/null

mkdir -p "$MC_DIR/bin"
# Binary name varies between forks; pick whatever was produced.
for cand in "$SRC/mcfold-dp" "$SRC/build/mcfold-dp" "$SRC/MCFold" "$SRC/mc-fold"; do
  [[ -x "$cand" ]] && cp "$cand" "$MC_DIR/bin/mcfold-dp" && break
done

if [[ -x "$MC_DIR/bin/mcfold-dp" ]]; then
  echo "[22] Binary: $MC_DIR/bin/mcfold-dp"
else
  echo "[22] WARN: built, but couldn't locate binary. Check $SRC manually."
fi
echo "[22] Done."
