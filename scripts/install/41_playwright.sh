#!/usr/bin/env bash
set -euo pipefail

# Playwright + headless Chromium — used by scripts/render_pngs.py to
# screenshot fornac secondary-structure renderings as PNG.
#
# Installs the Python package into the nap-thermo env (pip) and the
# Chromium binary into ~/.cache/ms-playwright/ (playwright's default).

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/.envrc"

ENV_NAME="nap-thermo"

echo "[41] Installing playwright into $ENV_NAME ..."
micromamba run -n "$ENV_NAME" pip install --quiet playwright

echo "[41] Downloading headless Chromium ..."
micromamba run -n "$ENV_NAME" playwright install chromium

echo "[41] Verifying ..."
micromamba run -n "$ENV_NAME" python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    print('Chromium launched OK:', browser.version)
    browser.close()
"
echo "[41] Done."
