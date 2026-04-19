#!/usr/bin/env python3
"""Render secondary-structure predictions as a single fornac-powered HTML.

Reads a predictions.csv produced by run_all.py together with the input
FASTA, and writes structures.html next to the CSV. Each card in the
output is a fornac (force-directed) rendering of one (seq_id, tool)
prediction. Open the file in a browser; the layout runs locally.

Usage:
    python scripts/visualize.py <predictions.csv> --fasta <input.fa>
    python scripts/visualize.py <predictions.csv> --fasta <input.fa> -o custom.html
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.config import FORNAC_CSS, FORNAC_D3, FORNAC_JS


def parse_fasta(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    seq_id, seq = None, []
    with path.open() as fh:
        for line in fh:
            line = line.rstrip()
            if line.startswith(">"):
                if seq_id is not None:
                    out[seq_id] = "".join(seq)
                seq_id = line[1:].split()[0] or "unnamed"
                seq = []
            elif line:
                seq.append(line)
        if seq_id is not None:
            out[seq_id] = "".join(seq)
    return out


def _relpath(target: Path, start: Path) -> str:
    return os.path.relpath(target.resolve(), start=start.resolve().parent)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Structure predictions &mdash; {csv_name}</title>
<link rel="stylesheet" href="{css_href}">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 24px; color: #222;
  }}
  header h1 {{ margin: 0 0 4px 0; font-size: 20px; }}
  header .meta {{ color: #666; font-size: 13px; margin-bottom: 24px; }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: 20px;
  }}
  .card {{
    border: 1px solid #ddd; border-radius: 8px; padding: 12px;
    background: #fafafa;
  }}
  .card-title {{ font-weight: 600; font-size: 14px; margin-bottom: 2px; }}
  .card-sub {{ color: #666; font-size: 12px; margin-bottom: 8px; }}
  .card-seq {{
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 11px; word-break: break-all;
    background: #fff; border: 1px solid #eee; padding: 6px 8px;
    border-radius: 4px; margin-bottom: 8px; line-height: 1.45;
  }}
  .fornac {{ width: 100%; height: 320px; background: #fff; border-radius: 4px; }}
  .card-error {{ color: #b00020; font-size: 12px; font-style: italic; }}
</style>
</head>
<body>
<header>
  <h1>Structure predictions</h1>
  <div class="meta">
    {n_cards} rendering(s) from <code>{csv_name}</code> &middot;
    generated {timestamp}
  </div>
</header>
<div class="grid">
{cards}
</div>
<script src="{d3_href}"></script>
<script src="{js_href}"></script>
<script>
const PREDICTIONS = {predictions_json};

window.addEventListener('load', () => {{
  if (typeof fornac === 'undefined' || !fornac.FornaContainer) {{
    console.error('fornac.FornaContainer not found; check that d3 v3 and fornac.js loaded');
    return;
  }}
  const FornaContainer = fornac.FornaContainer;
  for (const p of PREDICTIONS) {{
    try {{
      const c = new FornaContainer('#' + p.id, {{
        'animation': true,
        'applyForce': true,
        'allowPanningAndZooming': true,
        'initialSize': [360, 300]
      }});
      c.addRNA(p.db, {{ 'sequence': p.seq, 'structure': p.db }});
    }} catch (e) {{
      console.error('Failed to render', p.id, e);
      const el = document.getElementById(p.id);
      if (el) el.innerHTML = '<div class="card-error">render failed: ' + e + '</div>';
    }}
  }}
}});
</script>
</body>
</html>
"""

CARD_TEMPLATE = """  <div class="card">
    <div class="card-title">{title}</div>
    <div class="card-sub">{sub}</div>
    <div class="card-seq">{seq_html}<br>{db_html}</div>
    <div class="fornac" id="{card_id}"></div>
  </div>"""


def _format_card_seq_html(seq: str, db: str) -> tuple[str, str]:
    """Return (seq_html, db_html) where T and U are preserved as-is."""
    return html.escape(seq), html.escape(db)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", type=Path, help="predictions.csv from run_all.py")
    ap.add_argument("--fasta", type=Path, required=True,
                    help="Input FASTA used to produce the CSV")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="Output HTML path (default: <csv_dir>/structures.html)")
    args = ap.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 1
    if not args.fasta.exists():
        print(f"FASTA not found: {args.fasta}", file=sys.stderr)
        return 1
    for f in (FORNAC_JS, FORNAC_CSS, FORNAC_D3):
        if not f.exists():
            print(f"fornac asset missing: {f}\n"
                  f"Run scripts/install/40_fornac.sh first.", file=sys.stderr)
            return 1

    sequences = parse_fasta(args.fasta)
    out_path = args.output or args.csv.parent / "structures.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    predictions: list[dict] = []
    cards: list[str] = []
    with args.csv.open() as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            seq_id = row["seq_id"]
            tool = row["tool"]
            db = (row.get("dot_bracket") or "").strip()
            mfe = (row.get("mfe_kcal_mol") or "").strip()
            err = (row.get("error") or "").strip()
            na = row.get("na_type", "")
            seq = sequences.get(seq_id)
            if seq is None:
                print(f"[warn] seq_id {seq_id!r} not in FASTA — skipping", file=sys.stderr)
                continue

            # fornac wants U, not T (visual alphabet is RNA). Transcribe in
            # the JS payload regardless of na_type so rendering works for
            # DNA inputs too; keep the "raw" seq in the card header below.
            render_seq = seq.upper().replace("T", "U")

            card_id = f"rna_{i}"
            title = f"{seq_id} &middot; {tool}"
            sub_bits: list[str] = [f"na_type={na}"]
            if mfe:
                sub_bits.append(f"MFE={mfe} kcal/mol")
            if err:
                sub_bits.append(f"error: {err}")
            sub = " &middot; ".join(sub_bits)

            seq_html, db_html = _format_card_seq_html(seq, db or "(no structure)")

            if db and set(db) <= set(".()[]{}<>"):
                predictions.append({
                    "id": card_id,
                    "seq": render_seq,
                    "db": db,
                })
                cards.append(CARD_TEMPLATE.format(
                    title=title, sub=sub,
                    seq_html=seq_html, db_html=db_html,
                    card_id=card_id,
                ))
            else:
                cards.append(
                    CARD_TEMPLATE.format(
                        title=title, sub=sub,
                        seq_html=seq_html, db_html=db_html,
                        card_id=card_id,
                    ).replace(
                        f'<div class="fornac" id="{card_id}"></div>',
                        '<div class="card-error">no dot-bracket to render</div>',
                    )
                )

    js_href = _relpath(FORNAC_JS, out_path)
    css_href = _relpath(FORNAC_CSS, out_path)
    d3_href = _relpath(FORNAC_D3, out_path)

    rendered = HTML_TEMPLATE.format(
        csv_name=html.escape(str(args.csv.name)),
        n_cards=len(predictions),
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        d3_href=html.escape(d3_href),
        js_href=html.escape(js_href),
        css_href=html.escape(css_href),
        cards="\n".join(cards),
        predictions_json=json.dumps(predictions),
    )
    out_path.write_text(rendered)
    print(f"Wrote {out_path} ({len(predictions)} rendered, "
          f"{len(cards) - len(predictions)} skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
