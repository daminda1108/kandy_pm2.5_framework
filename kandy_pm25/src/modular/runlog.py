"""Record every city a scoring loop skips, so that no city leaves a result silently.

Before 2026-09-25 each ladder loop wrapped a city in ``except Exception: continue`` (or
``r = None``) and never said which cities were dropped or why. ``DropLog`` keeps the loop's
tolerance for a genuinely unscoreable city, but names it, gives the reason, writes the log next
to the output and can refuse when an unexpected exception type appears.
"""
from __future__ import annotations

import json
import traceback
from pathlib import Path


class DropLog:
    # Reasons that are a legitimate property of the city (not a code defect).
    EXPECTED = ("too few days", "no pool", "empty", "insufficient")

    def __init__(self, script: str):
        self.script = script
        self.rows: list[dict] = []

    def skip(self, city, reason: str):
        """A city the ladder cannot score by design (e.g. the rung returned None)."""
        self.rows.append({"city": str(city), "kind": "skip", "reason": reason})

    def error(self, city, exc: BaseException):
        """An exception raised while scoring a city."""
        self.rows.append({"city": str(city), "kind": "error",
                          "reason": f"{type(exc).__name__}: {exc}",
                          "trace": traceback.format_exc(limit=3)})

    def report(self, out_path: Path | None = None, strict: bool = True):
        errs = [r for r in self.rows if r["kind"] == "error"]
        skips = [r for r in self.rows if r["kind"] == "skip"]
        print(f"[droplog:{self.script}] {len(skips)} skipped, {len(errs)} errored")
        for r in self.rows:
            print(f"    {r['kind']:<5} {r['city']:<10} {r['reason'][:110]}")
        if out_path is not None:
            out_path = Path(out_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = out_path.with_suffix(out_path.suffix + ".tmp")
            tmp.write_text(json.dumps(self.rows, indent=1), encoding="utf-8")
            tmp.replace(out_path)
        if strict and errs:
            raise SystemExit(f"[droplog:{self.script}] {len(errs)} cities raised; "
                             "fix or declare them before trusting this output")
        return self.rows
