"""night_guard.py -- cooperative stop for downloads run by night_window.sh.

Downloaders call `check()` before starting each unit of work (a city, a station-year, a chunk). After the
deadline it raises SystemExit(75), which night_window.sh reads as "resume next night". Outside the runner
(no NIGHT_DEADLINE in the environment) it never stops, so scripts still run by hand.
"""
from __future__ import annotations

import os
import time

COME_BACK_TOMORROW = 75


def deadline() -> float | None:
    v = os.environ.get("NIGHT_DEADLINE")
    return float(v) if v else None


def remaining() -> float:
    d = deadline()
    return float("inf") if d is None else d - time.time()


def check(margin_s: float = 0.0) -> None:
    """Exit 75 if fewer than `margin_s` seconds remain before the deadline."""
    if remaining() <= margin_s:
        print(f"night_guard: deadline reached, stopping cleanly (exit {COME_BACK_TOMORROW})", flush=True)
        raise SystemExit(COME_BACK_TOMORROW)
