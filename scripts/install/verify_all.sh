#!/usr/bin/env bash
set -euo pipefail

# Smoke test: run each installed predictor on a tiny RNA sequence and
# report which ones produce a valid dot-bracket. Non-fatal per-tool so
# partial installs still give useful output.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/.envrc"

SEQ="GGGAAACCC"  # 9-nt mini hairpin, folds to (((...)))

pass=0; fail=0
check() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  [PASS] $name"; pass=$((pass+1))
  else
    echo "  [FAIL] $name"; fail=$((fail+1))
  fi
}

echo "=== nap-thermo env ==="
check ViennaRNA  bash -c "echo $SEQ | micromamba run -n nap-thermo RNAfold --noPS"
check NUPACK     micromamba run -n nap-thermo python -c "import nupack"
check RNAstructure [ -x "$REPO_ROOT/tools/rnastructure/exe/Fold" ]
check UNAFold    [ -x "$REPO_ROOT/tools/unafold/install/bin/hybrid-ss-min" ]

echo "=== nap-learning env ==="
check CONTRAfold [ -x "$REPO_ROOT/tools/contrafold/bin/contrafold" ]
check EternaFold [ -x "$REPO_ROOT/tools/eternafold/bin/eternafold" ]
check MC-Fold    [ -x "$REPO_ROOT/tools/mc-fold/bin/mcfold-dp" ]

echo "=== nap-hybrid env ==="
check MXfold2    micromamba run -n nap-hybrid python -c "import mxfold2"
check "Torch+CUDA" micromamba run -n nap-hybrid python -c "import torch; assert torch.cuda.is_available()"
check VFold2D    bash -c "[ -d $REPO_ROOT/tools/vfold2d/src ] || [ -f $REPO_ROOT/scripts/predictors/vfold2d.py ]"

echo
echo "Passed: $pass  Failed: $fail"
exit $(( fail > 0 ? 1 : 0 ))
