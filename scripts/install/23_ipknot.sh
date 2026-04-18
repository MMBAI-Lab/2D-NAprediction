#!/usr/bin/env bash
set -euo pipefail

# IPknot — RNA secondary-structure prediction with pseudoknots via
# integer programming. Source extracted under tools/ipknot-master/.
#
# Dependencies (system):
#   - cmake >= 3.8            (apt: cmake)
#   - pkg-config              (apt: pkg-config)
#   - libglpk-dev             (apt: libglpk-dev)
#   - ViennaRNA + RNAlib2.pc  (from nap-thermo conda env)
#
# ViennaRNA is looked up via pkg-config. We point PKG_CONFIG_PATH at
# nap-thermo's lib/pkgconfig so CMake finds RNAlib2.pc.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IPK_SRC="$REPO_ROOT/tools/ipknot-master"
BUILD="$IPK_SRC/build"
VIENNA_PC="$REPO_ROOT/tools/envs/envs/nap-thermo/lib/pkgconfig"

if [[ ! -f "$IPK_SRC/CMakeLists.txt" ]]; then
  echo "[23] ERROR: $IPK_SRC/CMakeLists.txt not found." >&2
  exit 1
fi
if [[ ! -f "$VIENNA_PC/RNAlib2.pc" ]]; then
  echo "[23] ERROR: $VIENNA_PC/RNAlib2.pc not found. Install nap-thermo first." >&2
  exit 1
fi
if ! dpkg -l libglpk-dev >/dev/null 2>&1; then
  echo "[23] ERROR: libglpk-dev missing. Run: sudo apt install libglpk-dev" >&2
  exit 1
fi

rm -rf "$BUILD"
mkdir -p "$BUILD"

echo "[23] Configuring IPknot..."
PKG_CONFIG_PATH="$VIENNA_PC:${PKG_CONFIG_PATH:-}" \
  cmake -S "$IPK_SRC" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release

echo "[23] Building..."
cmake --build "$BUILD" -j"$(nproc)"

BIN="$BUILD/ipknot"
if [[ ! -x "$BIN" ]]; then
  echo "[23] ERROR: $BIN not produced." >&2
  exit 1
fi

echo "[23] ipknot version (-h):"
"$BIN" -h 2>&1 | head -6 || true

# Ensure runtime can find the conda ViennaRNA shared lib.
echo "[23] Runtime note: wrapper sets LD_LIBRARY_PATH to $REPO_ROOT/tools/envs/envs/nap-thermo/lib"
echo "[23] Done."
