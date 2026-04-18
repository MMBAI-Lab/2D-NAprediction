#!/usr/bin/env bash
set -euo pipefail

# NUPACK 4.0.0.23 — installed from the rwollman GitHub mirror, since the official
# nupack.org distribution is now behind a paid annual academic plan.
#   Repo:    https://github.com/rwollman/NUPACK
#   License: Caltech NUPACK Software License (academic non-commercial; redistribution OK).
#
# The mirror ships pre-built manylinux2014 wheels for cp36-cp39 only. We use the
# cp39 wheel — nap-thermo is pinned to Python 3.9 in envs/nap-thermo.yml for this reason.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/.envrc"

ENV_NAME="nap-thermo"
NUPACK_DIR="$REPO_ROOT/tools/nupack"
SRC_DIR="$NUPACK_DIR/_source"
MIRROR_URL="https://github.com/rwollman/NUPACK.git"
MIRROR_PIN="master"
WHEEL_REL="src/package/nupack-4.0.0.23-cp39-cp39-manylinux2014_x86_64.whl"

mkdir -p "$NUPACK_DIR"

if [[ ! -d "$SRC_DIR/.git" ]]; then
  echo "[11] Cloning $MIRROR_URL into $SRC_DIR..."
  git clone "$MIRROR_URL" "$SRC_DIR"
else
  echo "[11] $SRC_DIR already cloned, fetching latest..."
  git -C "$SRC_DIR" fetch --tags origin
fi
git -C "$SRC_DIR" checkout "$MIRROR_PIN"

WHEEL="$SRC_DIR/$WHEEL_REL"
if [[ ! -f "$WHEEL" ]]; then
  echo "[11] ERROR: expected wheel not found at $WHEEL" >&2
  echo "       The rwollman mirror layout may have changed." >&2
  exit 1
fi

PY_VER="$(micromamba run -n "$ENV_NAME" python -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
if [[ "$PY_VER" != "3.9" ]]; then
  echo "[11] ERROR: $ENV_NAME is Python $PY_VER, but the NUPACK wheel requires 3.9." >&2
  echo "       Re-run scripts/install/10_viennarna.sh to recreate the env from envs/nap-thermo.yml." >&2
  exit 1
fi

echo "[11] Installing $WHEEL into $ENV_NAME..."
micromamba run -n "$ENV_NAME" pip install --force-reinstall "$WHEEL"

echo "[11] Verifying NUPACK..."
micromamba run -n "$ENV_NAME" python -c "import nupack; print('NUPACK', nupack.__version__)"
echo "[11] Done."
