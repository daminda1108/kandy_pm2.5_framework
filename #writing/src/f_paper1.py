"""f_paper1.py -- thesis copies of the Paper 1 figures that replace the superseded ladder figures (2026-10-07).

The old thesis ladder figures (F2_ladder, F7_losses, F7_station_count, F9_1_acquisition) read ladder-v1 / discovery
files that F.115-F.117 and F.124 superseded. The replacements are built by
`papers/paper1_information_budget/figures/build_figures.py` from the registered and review result files; this script
rebuilds them there and copies them into `thesis/figures/` under thesis names, so the thesis never draws its own
copy of a ladder number. Captions live in `build/visuals.py`.

Usage: python src/f_paper1.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P1 = Path("D:/ProjectCD/papers/paper1_information_budget/figures")
OUT = ROOT / "thesis" / "figures"
PY = Path("D:/ProjectCD/kandy_pm25/.venv/Scripts/python.exe")

# Paper 1 stem -> thesis stem
MAP = {
    "fig3_confirmation": "FA_confirmation",
    "fig4_robustness": "FA_robustness",
    "fig3b_like_for_like": "FA_like_for_like",
    "figS1_station_count": "FA_station_count_daily",
    "fig7b_spatial_noise": "FB_spatial_noise",
    "fig7_spatial_curve": "FB_spatial_curve",
}
BUILD = "3,4,3b,S1,7,7b"


def main() -> int:
    r = subprocess.run([str(PY), str(P1 / "build_figures.py"), "--figs", BUILD], capture_output=True, text=True,
                       env={**__import__("os").environ, "PYTHONUTF8": "1"})
    if r.returncode != 0:
        print(r.stdout[-800:], r.stderr[-800:])
        return 1
    for src, dst in MAP.items():
        for ext in ("png", "pdf"):
            shutil.copyfile(P1 / f"{src}.{ext}", OUT / f"{dst}.{ext}")
        print(f"  {src} -> thesis/figures/{dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
