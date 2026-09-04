"""One place for a figure script to publish the numbers it computed.

A figure and the sentence next to it must not compute the same quantity twice. Every figure
script that produces a number the manuscript quotes writes it here; `build_claims.py` reads
these files and turns them into claim tokens, so the figure and the prose resolve to the same
value by construction and the build fails if they ever diverge.

    from figdata import emit
    emit("F11_uncertainty", pooled=0.7239, below=0.2571)

Writes data/processed/paper_figures/F11_uncertainty.json.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "data" / "processed" / "paper_figures"


def emit(stem: str, **values) -> Path:
    DIR.mkdir(parents=True, exist_ok=True)
    p = DIR / f"{stem}.json"
    # write to a temp file and replace, so a crash mid-encode cannot truncate a good file
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(values, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(p)
    print(f"    figdata -> {p.name}  ({len(values)} values)")
    return p


def load(stem: str) -> dict | None:
    p = DIR / f"{stem}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
