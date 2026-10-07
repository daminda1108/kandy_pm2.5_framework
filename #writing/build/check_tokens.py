"""check_tokens.py -- resolve every {{claim:}}, {{tbl:}}, {{fig:}}, {{dia:}} and {{ref:}} token in the given files
without assembling the thesis (safe to run concurrently; read-only).

Usage: python build/check_tokens.py pool/ch07_making_sure/*.md theses/a/results_lead.md
Exit 1 if anything does not resolve.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
from visuals import VISUALS  # noqa: E402

CLAIMS = json.load(open(Path("D:/ProjectCD/kandy_pm25/data/processed/modular/claims.json"), encoding="utf-8"))["claims"]
TABLES = ROOT / "thesis" / "tables"
LABELS = set()
for p in list((ROOT / "pool").rglob("*.md")) + list((ROOT / "theses").rglob("*.md")):
    LABELS |= set(re.findall(r"\{#([\w-]+)\}", io.open(p, encoding="utf-8").read()))


def main(paths: list[str]) -> int:
    bad = 0
    for a in paths:
        t = io.open(a, encoding="utf-8").read()
        for kind, tag in re.findall(r"\{\{(claim|tbl|fig|dia|ref|this|This):([^}\s]+)[^}]*\}\}", t):
            ok = {"claim": lambda: tag in CLAIMS,
                  "tbl": lambda: (TABLES / f"{tag}.md").exists() or bool(list(TABLES.glob(f"{tag}*.md"))),
                  "fig": lambda: tag in VISUALS, "dia": lambda: tag in VISUALS,
                  "ref": lambda: tag in LABELS, "this": lambda: tag in LABELS, "This": lambda: tag in LABELS}[kind]()
            if not ok:
                bad += 1
                print(f"UNRESOLVED {a}: {{{{{kind}:{tag}}}}}")
    print("all tokens resolve" if not bad else f"{bad} unresolved")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
