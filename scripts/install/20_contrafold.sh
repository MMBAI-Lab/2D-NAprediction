#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CF_DIR="$REPO_ROOT/tools/contrafold"
mkdir -p "$CF_DIR"

if [[ -x "$CF_DIR/bin/contrafold" ]]; then
  echo "[20] CONTRAfold already built at $CF_DIR/bin/contrafold"
  exit 0
fi

# Stanford URL 404s often; use the maintained github mirror.
# contrafold-se by csfoo is the same code with modern makefile patches.
REPO_URL="https://github.com/csfoo/contrafold-se.git"

SRC="$CF_DIR/src"
if [[ ! -d "$SRC/.git" ]]; then
  echo "[20] Cloning $REPO_URL ..."
  git clone "$REPO_URL" "$SRC"
else
  echo "[20] Source already present: $SRC"
fi

pushd "$SRC/src" >/dev/null
echo "[20] Building CONTRAfold (inside nap-learning env for Boost)..."
source "$REPO_ROOT/.envrc"
CONDA_PREFIX="$REPO_ROOT/tools/envs/envs/nap-learning"
export CPPFLAGS="-I$CONDA_PREFIX/include"
export LDFLAGS="-L$CONDA_PREFIX/lib"
export LIBRARY_PATH="$CONDA_PREFIX/lib"
make clean || true
make
popd >/dev/null

mkdir -p "$CF_DIR/bin"
cp "$SRC/src/contrafold" "$CF_DIR/bin/contrafold"
echo "[20] Binary: $CF_DIR/bin/contrafold"
"$CF_DIR/bin/contrafold" 2>&1 | head -5 || true
echo "[20] Done."
