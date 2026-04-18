#!/usr/bin/env bash
set -euo pipefail

# Vfold2D (Chen Lab) — only the 2D module of VfoldPipeline_standalone.
# We skip the 3D portion (Vfold3DLA + LAMMPS + QRNAS) since this pipeline
# is 2D-only.
#
# Source extracted under tools/VfoldPipeline_standalone/. The Makefile in
# Vfold2D/src/ compiles two binaries into ../bin/:
#   vfold2D_cl.out — non-pseudoknot
#   vfold2D_pk.out — with pseudoknots
# Both need the env var VfoldPipeline to point at the standalone root,
# so the binary can locate Vfold2D/INPUT/.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VF_ROOT="$REPO_ROOT/tools/VfoldPipeline_standalone"
SRC="$VF_ROOT/Vfold2D/src"
BIN_DIR="$VF_ROOT/Vfold2D/bin"

if [[ ! -f "$SRC/Makefile" ]]; then
  echo "[31] ERROR: $SRC/Makefile not found." >&2
  exit 1
fi

mkdir -p "$BIN_DIR"

echo "[31] Building Vfold2D (non-PK + PK)..."
make -C "$SRC" -j"$(nproc)"

for b in vfold2D_cl.out vfold2D_pk.out; do
  if [[ ! -x "$BIN_DIR/$b" ]]; then
    echo "[31] ERROR: $BIN_DIR/$b not produced." >&2
    exit 1
  fi
done

echo "[31] Binaries:"
ls -1 "$BIN_DIR"
echo "[31] Wrapper sets VfoldPipeline=$VF_ROOT at runtime."
echo "[31] Done."
