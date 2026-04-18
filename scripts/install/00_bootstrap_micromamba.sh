#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MM_DIR="$REPO_ROOT/tools/micromamba"
MM_BIN="$MM_DIR/bin/micromamba"
MM_ROOT="$REPO_ROOT/tools/envs"

mkdir -p "$MM_DIR/bin" "$MM_ROOT"

if [[ -x "$MM_BIN" ]]; then
  echo "[00] micromamba already present: $($MM_BIN --version)"
else
  echo "[00] Downloading micromamba (linux-64 latest)..."
  curl -fsSL https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xj -C "$MM_DIR" bin/micromamba
  chmod +x "$MM_BIN"
  echo "[00] Installed: $($MM_BIN --version)"
fi

cat > "$REPO_ROOT/.envrc" <<EOF
export MAMBA_ROOT_PREFIX="$MM_ROOT"
export MAMBA_EXE="$MM_BIN"
eval "\$($MM_BIN shell hook -s bash)"
EOF

echo "[00] Wrote $REPO_ROOT/.envrc — source it to get micromamba in PATH:"
echo "     source .envrc"
