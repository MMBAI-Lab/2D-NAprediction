#!/usr/bin/env bash
set -euo pipefail

# System deps required to compile CONTRAfold/EternaFold (Boost),
# MC-Fold (GSL) and UNAFold (libgd for PostScript output).
# This is the ONLY step that needs sudo.

PKGS=(
  build-essential
  pkg-config
  autoconf
  libtool
  libboost-dev
  libboost-program-options-dev
  libgsl-dev
  libgd-dev
  libxml2-dev
)

echo "[01] About to install: ${PKGS[*]}"
echo "[01] sudo will prompt for password..."
sudo apt update
sudo apt install -y "${PKGS[@]}"
echo "[01] Done."
