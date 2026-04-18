#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EF_DIR="$REPO_ROOT/tools/eternafold"
mkdir -p "$EF_DIR"

if [[ -x "$EF_DIR/bin/eternafold" ]]; then
  echo "[21] EternaFold already built at $EF_DIR/bin/eternafold"
  exit 0
fi

REPO_URL="https://github.com/eternagame/EternaFold.git"
SRC="$EF_DIR/src"

if [[ ! -d "$SRC/.git" ]]; then
  echo "[21] Cloning $REPO_URL ..."
  git clone "$REPO_URL" "$SRC"
else
  echo "[21] Source already present: $SRC"
fi

pushd "$SRC/src" >/dev/null
echo "[21] Building EternaFold (inside nap-learning env for Boost)..."
source "$REPO_ROOT/.envrc"
CONDA_PREFIX="$REPO_ROOT/tools/envs/envs/nap-learning"
export CPPFLAGS="-I$CONDA_PREFIX/include"
export LDFLAGS="-L$CONDA_PREFIX/lib"
export LIBRARY_PATH="$CONDA_PREFIX/lib"
make clean || true
make all
popd >/dev/null

mkdir -p "$EF_DIR/bin" "$EF_DIR/parameters"
cp "$SRC/src/contrafold" "$EF_DIR/bin/eternafold"
# The trained parameter file ships with the repo; copy the default.
if [[ -d "$SRC/parameters" ]]; then
  cp -r "$SRC/parameters/." "$EF_DIR/parameters/"
fi
echo "[21] Binary: $EF_DIR/bin/eternafold"
echo "[21] Parameters: $EF_DIR/parameters/"
ls "$EF_DIR/parameters/" | head -5
echo "[21] Done."
