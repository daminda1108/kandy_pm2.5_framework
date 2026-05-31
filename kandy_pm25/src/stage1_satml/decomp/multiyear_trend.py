"""
multiyear_trend.py — continuous monthly Kandy PM2.5 reconstruction 2019–2024
from the decomposition (basin spatial-mean per month). Shows the model recovers
real inter-annual signal (2021 COVID dip) on observation-grounded VanD levels.

Output: results/figures/kandy_decomp/multiyear_trend.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
try:
    from src.utils.plot_style import apply_style
    apply_style("ieee")
except Exception:
    pass

DECOMP = HERE / "data" / "processed" / "decomp"
OUT = HERE / "results" / "figures" / "kandy_decomp"
YEARS = range(2019, 2025)


def main():
    rows = []
    ann = {}
    for y in YEARS:
        f = DECOMP / f"kandy_decomp_predictions_{y}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(f, columns=["time", "pm25_q50"])
        d["time"] = pd.to_datetime(d["time"], utc=True)
        d["ym"] = d["time"].dt.to_period("M")
        m = d.groupby("ym")["pm25_q50"].mean()
        for ym, v in m.items():
            rows.append({"date": ym.to_timestamp(), "pm25": float(v)})
        ann[y] = float(d["pm25_q50"].mean())
    ts = pd.DataFrame(rows).sort_values("date")

    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(ts["date"], ts["pm25"], "-", color="#1864ab", lw=1.3)
    ax.fill_between(ts["date"], ts["pm25"], alpha=0.12, color="#1864ab")
    for y, a in ann.items():
        x = pd.Timestamp(f"{y}-07-01")
        ax.annotate(f"{a:.1f}", (x, a), ha="center", fontsize=8, color="#c92a2a")
        ax.axhline(a, xmin=(y - 2019) / 6, xmax=(y - 2018) / 6, color="#c92a2a",
                   lw=0.8, ls="--", alpha=0.6)
    ax.axhline(24.52, color="#666", lw=0.7, ls=":", label="KOALA 2019 anchor (24.5)")
    ax.set_ylabel("PM₂.₅ (µg m⁻³)")
    ax.set_title("Kandy basin-mean PM₂.₅ reconstruction 2019–2024 (decomposition; "
                 "red = annual mean, VanD-anchored)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"multiyear_trend.{ext}", dpi=200, bbox_inches="tight")
    print("annual means:", {y: round(a, 1) for y, a in ann.items()})
    print(f"Wrote {OUT / 'multiyear_trend.png'}")


if __name__ == "__main__":
    main()
