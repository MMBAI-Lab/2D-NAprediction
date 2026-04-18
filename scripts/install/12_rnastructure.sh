#!/usr/bin/env bash
set -euo pipefail

# RNAstructure 6.5 — built from the source tree the user extracted at
#   tools/RNAstructure/  (academic license, GPL v2 per ReadMe.txt).
# We just run `make all` and confirm the key binaries exist.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RS_DIR="$REPO_ROOT/tools/RNAstructure"

if [[ ! -f "$RS_DIR/Makefile" ]]; then
  echo "[12] ERROR: $RS_DIR/Makefile not found." >&2
  echo "       Extract RNAstructure source under tools/RNAstructure/ first." >&2
  exit 1
fi

echo "[12] Building RNAstructure (this may take several minutes)..."
make -C "$RS_DIR" -j"$(nproc)" all

EXE="$RS_DIR/exe"
echo "[12] Verifying key binaries..."
for b in Fold ct2dot; do
  if [[ ! -x "$EXE/$b" ]]; then
    echo "[12] ERROR: missing $EXE/$b after build." >&2
    exit 1
  fi
  "$EXE/$b" --version 2>&1 | head -1 || true
done

echo "[12] DATAPATH at runtime: $RS_DIR/data_tables"
echo "[12] Done."
