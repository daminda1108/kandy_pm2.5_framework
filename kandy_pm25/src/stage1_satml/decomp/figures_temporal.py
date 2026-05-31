"""
figures_temporal.py — publication temporal-variation figure for the Kandy
decomposition (basin spatial-mean, 2019-2023), following AQ-paper conventions
(Senarathna 2024 style): inter-annual / annual(monthly) / weekly / diurnal,
with WHO reference levels and the Senarathna-2019 reference overlaid for shape.

Output: results/figures/kandy_decomp/pub/temporal_variation.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
try:
    from src.utils.plot_style import apply_style
    apply_style("ieee")
except Exception:
    pass
from src.stage1_satml.evaluation.compare_senarathna_v3 import (
    SENARATHNA_HOURLY, SENARATHNA_WEEKLY, SENARATHNA_MONTHLY)

DECOMP = HERE / "data" / "processed" / "decomp"
OUT = HERE / "results" / "figures" / "kandy_decomp" / "pub"
OUT.mkdir(parents=True, exist_ok=True)
MODEL = "#1864ab"; SEN = "#c92a2a"
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MON = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def _r(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def _who_lines(ax):
    for lvl, lab in [(5, "WHO AQG"), (15, "IT-3"), (25, "IT-2"), (35, "IT-1")]:
        ax.axhline(lvl, color="#999", lw=0.6, ls=":", zorder=0)
        ax.text(0.995, lvl, f" {lab} {lvl}", transform=ax.get_yaxis_transform(),
                ha="right", va="bottom", fontsize=5.5, color="#999")


def main():
    z = np.load(DECOMP / "climatology.npz")
    years = z["years"]
    fig, ax = plt.subplots(2, 2, figsize=(11, 7.6), constrained_layout=True)

    # A — inter-annual
    a = ax[0, 0]
    a.bar(years, z["annual"], color=MODEL, width=0.6, alpha=0.85)
    for x, v in zip(years, z["annual"]):
        a.text(x, v + 0.3, f"{v:.1f}", ha="center", fontsize=8)
    _who_lines(a)
    a.set_ylim(0, 30); a.set_xticks(years)
    a.set_ylabel("PM₂.₅ (µg m⁻³)")
    a.set_title("(a) Inter-annual — basin annual mean (per-year VanD level)", fontsize=9)

    # B — annual cycle (monthly)
    b = ax[0, 1]
    mo = z["monthly"]; mmean = np.nanmean(mo, 0)
    b.fill_between(range(1, 13), np.nanmin(mo, 0), np.nanmax(mo, 0),
                   color=MODEL, alpha=0.15, label="2019–23 range")
    b.plot(range(1, 13), mmean, "-o", color=MODEL, ms=3, label="model (5-yr mean)")
    sen = [SENARATHNA_MONTHLY[m] for m in range(1, 13)]
    b.plot(range(1, 13), sen, "--s", color=SEN, ms=3, label="Senarathna 2019 (NIFS)")
    _who_lines(b)
    b.set_xticks(range(1, 13)); b.set_xticklabels(MON)
    b.set_title(f"(b) Annual cycle — monthly  (r={_r(mmean, sen):+.2f})", fontsize=9)
    b.legend(fontsize=6.5, loc="upper right")

    # C — weekly
    c = ax[1, 0]
    wk = z["weekly"]; wmean = np.nanmean(wk, 0)
    c.fill_between(range(7), np.nanmin(wk, 0), np.nanmax(wk, 0), color=MODEL, alpha=0.15)
    c.plot(range(7), wmean, "-o", color=MODEL, ms=3, label="model (5-yr mean)")
    senw = [SENARATHNA_WEEKLY[d] for d in range(7)]
    c.plot(range(7), senw, "--s", color=SEN, ms=3, label="Senarathna 2019")
    c.set_xticks(range(7)); c.set_xticklabels(DOW)
    c.set_ylabel("PM₂.₅ (µg m⁻³)")
    c.set_title(f"(c) Weekly — day-of-week  (r={_r(wmean, senw):+.2f})", fontsize=9)
    c.legend(fontsize=6.5)

    # D — diurnal
    d = ax[1, 1]
    di = z["diurnal"]; dmean = np.nanmean(di, 0)
    d.fill_between(range(24), np.nanmin(di, 0), np.nanmax(di, 0), color=MODEL, alpha=0.15)
    d.plot(range(24), dmean, "-o", color=MODEL, ms=3, label="model (5-yr mean)")
    send = [SENARATHNA_HOURLY[h] for h in range(24)]
    d.plot(range(24), send, "--s", color=SEN, ms=3, label="Senarathna 2019")
    d.set_xticks(range(0, 24, 3))
    d.set_xlabel("Hour (LT)")
    d.set_title(f"(d) Diurnal — hour-of-day  (r={_r(dmean, send):+.2f})", fontsize=9)
    d.legend(fontsize=6.5)

    fig.suptitle("Kandy PM₂.₅ temporal variation — decomposition basin mean 2019–2023 "
                 "(vs Senarathna et al. 2024)", fontsize=12)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"temporal_variation.{ext}", dpi=220, bbox_inches="tight")
    print("annual:", {int(y): round(float(v), 1) for y, v in zip(years, z["annual"])})
    print(f"diurnal r={_r(dmean, send):+.3f}  weekly r={_r(wmean, senw):+.3f}  "
          f"monthly r={_r(mmean, sen):+.3f}")
    print(f"Wrote {OUT / 'temporal_variation.png'}")


if __name__ == "__main__":
    main()
