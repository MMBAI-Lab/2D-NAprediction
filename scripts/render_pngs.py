#!/usr/bin/env python3
"""Render fornac secondary-structure previews as PNG images.

Reads a predictions.csv produced by run_all.py plus the input FASTA, and
for every (seq_id, tool) row with a dot-bracket it writes a PNG under
<csv_dir>/pngs/<seq_id>__<tool>.png. Each render opens a minimal
single-FornaContainer HTML in headless Chromium (via Playwright), waits
for the force-directed layout to stabilize, and screenshots the SVG.

Usage:
    python scripts/render_pngs.py <predictions.csv> --fasta <input.fa>
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.config import FORNAC_CSS, FORNAC_D3, FORNAC_JS
from scripts.visualize import parse_fasta


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="file://{css_path}">
<style>
  html, body {{ margin: 0; padding: 0; background: white; }}
  #rna {{ width: {w}px; height: {h}px; background: white; }}
</style>
</head>
<body>
<div id="rna"></div>
<script src="file://{d3_path}"></script>
<script src="file://{js_path}"></script>
<script>
window.__RENDERED = false;
window.addEventListener('load', () => {{
  if (typeof fornac === 'undefined' || !fornac.FornaContainer) {{
    window.__RENDER_ERROR = 'fornac.FornaContainer not found';
    return;
  }}
  try {{
    const c = new fornac.FornaContainer('#rna', {{
      'animation': false,
      'applyForce': true,
      'allowPanningAndZooming': false,
      'initialSize': [{w}, {h}]
    }});
    c.addRNA({db_json}, {{ 'sequence': {seq_json}, 'structure': {db_json} }});
    // Give d3's force simulation a chance to settle before the screenshot.
    setTimeout(() => {{ window.__RENDERED = true; }}, {settle_ms});
  }} catch (e) {{
    window.__RENDER_ERROR = String(e);
  }}
}});
</script>
</body>
</html>
"""


_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(s: str) -> str:
    """Filesystem-safe version of an id/tool name."""
    return _UNSAFE.sub("_", s).strip("_") or "unnamed"


def _build_html(tmp_path: Path, seq: str, db: str, width: int, height: int,
                settle_ms: int) -> None:
    tmp_path.write_text(HTML_TEMPLATE.format(
        css_path=str(FORNAC_CSS.resolve()),
        d3_path=str(FORNAC_D3.resolve()),
        js_path=str(FORNAC_JS.resolve()),
        seq_json=json.dumps(seq),
        db_json=json.dumps(db),
        w=width, h=height,
        settle_ms=settle_ms,
    ))


def render(csv_path: Path, fasta_path: Path,
           out_dir: Path | None = None,
           width: int = 640, height: int = 520,
           settle_ms: int = 2500) -> Path:
    """Render each predicted structure in a CSV to a PNG.

    Returns the output directory containing the PNGs.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    if not fasta_path.exists():
        raise FileNotFoundError(f"FASTA not found: {fasta_path}")
    for f in (FORNAC_JS, FORNAC_CSS, FORNAC_D3):
        if not f.exists():
            raise FileNotFoundError(
                f"fornac asset missing: {f}. Run scripts/install/40_fornac.sh first."
            )

    from playwright.sync_api import sync_playwright

    sequences = parse_fasta(fasta_path)
    out_dir = out_dir or (csv_path.parent / "pngs")
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": width, "height": height},
                                      device_scale_factor=2)
        page = context.new_page()

        rendered = 0
        skipped = 0
        errored: list[tuple[str, str]] = []

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with csv_path.open() as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    seq_id = row["seq_id"]
                    tool = row["tool"]
                    db = (row.get("dot_bracket") or "").strip()
                    seq = sequences.get(seq_id)
                    if seq is None:
                        print(f"[warn] seq_id {seq_id!r} not in FASTA — skipping",
                              file=sys.stderr)
                        skipped += 1
                        continue
                    if not db or not set(db) <= set(".()[]{}<>"):
                        skipped += 1
                        continue

                    # fornac renders RNA; transcribe DNA inputs.
                    render_seq = seq.upper().replace("T", "U")
                    png_path = out_dir / f"{_slug(seq_id)}__{_slug(tool)}.png"

                    html_path = td / f"{_slug(seq_id)}__{_slug(tool)}.html"
                    _build_html(html_path, render_seq, db, width, height, settle_ms)

                    try:
                        page.goto(html_path.resolve().as_uri())
                        page.wait_for_function(
                            "() => window.__RENDERED === true || window.__RENDER_ERROR",
                            timeout=settle_ms + 8000,
                        )
                        err = page.evaluate("window.__RENDER_ERROR || null")
                        if err:
                            errored.append((png_path.name, err))
                            continue
                        svg = page.locator("#rna svg")
                        svg.screenshot(path=str(png_path))
                        rendered += 1
                        print(f"  {png_path.name}")
                    except Exception as e:
                        errored.append((png_path.name, repr(e)))

        browser.close()

    print(f"\nWrote {rendered} PNG(s) to {out_dir}")
    if skipped:
        print(f"Skipped {skipped} row(s) (no dot-bracket or missing seq).")
    if errored:
        print(f"Errors in {len(errored)} render(s):")
        for name, msg in errored:
            print(f"  {name}: {msg}")
    return out_dir


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", type=Path, help="predictions.csv from run_all.py")
    ap.add_argument("--fasta", type=Path, required=True,
                    help="Input FASTA used to produce the CSV")
    ap.add_argument("-o", "--output-dir", type=Path, default=None,
                    help="Output dir for PNGs (default: <csv_dir>/pngs)")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=520)
    ap.add_argument("--settle-ms", type=int, default=2500,
                    help="Milliseconds to wait for the force-directed layout "
                         "to settle before screenshotting (default: 2500)")
    args = ap.parse_args()
    try:
        render(args.csv, args.fasta, args.output_dir,
               args.width, args.height, args.settle_ms)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
