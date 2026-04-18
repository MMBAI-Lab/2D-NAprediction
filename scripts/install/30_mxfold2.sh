#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/.envrc"

ENV_NAME="nap-hybrid"
YML="$REPO_ROOT/envs/nap-hybrid.yml"

if micromamba env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "[30] Env $ENV_NAME exists, updating..."
  micromamba env update -n "$ENV_NAME" -f "$YML" -y
else
  echo "[30] Creating env $ENV_NAME (torch + CUDA 12.1)..."
  micromamba create -n "$ENV_NAME" -f "$YML" -y
fi

echo "[30] Verifying CUDA..."
micromamba run -n "$ENV_NAME" python -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"

echo "[30] MXfold2 ships default parameters internally; nothing to download."

echo "[30] Verifying mxfold2 import..."
micromamba run -n "$ENV_NAME" python -c "import mxfold2; print('mxfold2', mxfold2.__version__ if hasattr(mxfold2,'__version__') else 'OK')"
echo "[30] Done."
