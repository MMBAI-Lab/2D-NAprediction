#!/usr/bin/env bash
set -euo pipefail

# mfold 3.6 (Zuker, 2013) — Fortran/C/C++ build via autoconf.
# Source extracted under tools/mfold-3.6/ by user.
# Installs into tools/mfold-3.6/install/ (no system writes, no sudo).
#
# This occupies the slot historically called "UNAFold" in this pipeline,
# but the binary is `mfold` (script that drives Fortran kernels) — not
# UNAFold's `hybrid-ss-min`. The wrapper at scripts/predictors/mfold.py
# is rewritten accordingly.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$REPO_ROOT/tools/mfold-3.6"
PREFIX="$SRC/install"

if [[ ! -f "$SRC/configure" ]]; then
  echo "[13] ERROR: $SRC/configure not found." >&2
  exit 1
fi

if ! command -v gfortran >/dev/null 2>&1; then
  echo "[13] ERROR: gfortran not found. Install with: sudo apt install gfortran" >&2
  exit 1
fi

mkdir -p "$PREFIX"

# mfold's Fortran binaries (nafold, newtemp, efn, mfold_datdir) hardcode
# `/usr/local/share/mfold/` as the path to energy-table files, ignoring
# the prefix passed to ./configure. newtemp in particular aborts with
# "Error opening asint1x2.__ input data file(s)" whenever NA=DNA or any
# non-default temperature is requested. Patch the source tree to point
# every hardcoded path at our actual install share dir before building.
# Idempotent: a second run finds nothing left to replace.
DATADIR="$PREFIX/share/mfold/"
echo "[13] Patching hardcoded data paths to $DATADIR ..."
grep -rlZ "/usr/local/share/mfold/" "$SRC/src" "$SRC/c++" 2>/dev/null \
  | xargs -0 -r sed -i "s|/usr/local/share/mfold/|$DATADIR|g"

pushd "$SRC" >/dev/null
echo "[13] Configuring (prefix=$PREFIX)..."
./configure --prefix="$PREFIX"

echo "[13] Building..."
make clean >/dev/null 2>&1 || true
make -j"$(nproc)"

echo "[13] Installing..."
make install
popd >/dev/null

if [[ ! -x "$PREFIX/bin/mfold" ]]; then
  echo "[13] ERROR: $PREFIX/bin/mfold not produced by install." >&2
  exit 1
fi

echo "[13] mfold version:"
"$PREFIX/bin/mfold" -v 2>&1 | head -2 || true
echo "[13] Done."
