#!/usr/bin/env bash
set -euo pipefail

# fornac — browser-side RNA secondary-structure visualizer (force-directed
# layout, the library behind http://rna.tbi.univie.ac.at/forna/). We vendor
# a git clone under tools/fornac/ so the generated HTML reports can load
# dist/fornac.{js,css} via a relative path and work offline.
#
# The upstream repo ships a pre-built dist/ on master, so no npm build is
# required.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FORNAC_DIR="$REPO_ROOT/tools/fornac"
MIRROR_URL="https://github.com/ViennaRNA/fornac.git"
MIRROR_PIN="master"

if [[ ! -d "$FORNAC_DIR/.git" ]]; then
  echo "[40] Cloning $MIRROR_URL into $FORNAC_DIR..."
  git clone --depth 1 "$MIRROR_URL" "$FORNAC_DIR"
else
  echo "[40] $FORNAC_DIR already cloned, fetching latest..."
  git -C "$FORNAC_DIR" fetch --depth 1 origin "$MIRROR_PIN"
fi
git -C "$FORNAC_DIR" checkout "$MIRROR_PIN"

for f in dist/fornac.js dist/fornac.css; do
  if [[ ! -f "$FORNAC_DIR/$f" ]]; then
    echo "[40] ERROR: $FORNAC_DIR/$f missing." >&2
    exit 1
  fi
done

# fornac's UMD bundle treats d3 as an external; it reads `window.d3` at load
# time. fornac 1.2.0's package.json pins d3 to ~3.5.13, so vendor the latest
# 3.5.x minified build next to the fornac dist.
D3_URL="https://d3js.org/d3.v3.min.js"
D3_TARGET="$FORNAC_DIR/dist/d3.v3.min.js"
if [[ ! -f "$D3_TARGET" ]]; then
  echo "[40] Downloading $D3_URL ..."
  curl -sSLf -o "$D3_TARGET" "$D3_URL"
fi
if [[ ! -s "$D3_TARGET" ]]; then
  echo "[40] ERROR: d3 download failed ($D3_TARGET empty)" >&2
  exit 1
fi

echo "[40] fornac ready at $FORNAC_DIR/dist/"
ls -1 "$FORNAC_DIR/dist/"
echo "[40] Done."
