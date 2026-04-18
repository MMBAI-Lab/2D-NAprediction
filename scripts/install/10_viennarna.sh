#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/.envrc"

ENV_NAME="nap-thermo"
YML="$REPO_ROOT/envs/nap-thermo.yml"

if micromamba env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "[10] Env $ENV_NAME exists, updating..."
  micromamba env update -n "$ENV_NAME" -f "$YML" -y
else
  echo "[10] Creating env $ENV_NAME..."
  micromamba create -n "$ENV_NAME" -f "$YML" -y
fi

echo "[10] Verifying ViennaRNA..."
micromamba run -n "$ENV_NAME" RNAfold --version
micromamba run -n "$ENV_NAME" python -c "import RNA; print('ViennaRNA Python binding:', RNA.__version__ if hasattr(RNA,'__version__') else 'OK')"
echo "[10] Done."
