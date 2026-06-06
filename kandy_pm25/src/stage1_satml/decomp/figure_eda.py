"""
figure_eda.py — EDA panels that justify the decomposition design decisions.

  (a) FECT hourly-observation coverage by sensor × year  → why lag-free T(t)
      (2024 is 30.5% Akurana-only; no observations to lag from)
  (b) Van Donkelaar reads ~25% low over Kandy → bias factor β=KOALA_2019/VanD_2019
  (c) VanD level vs MAIAC AOD don't track inter-annually (r=0.19) → no defensible
      substitute level for a no-VanD year → calibrated product limited to 2019–2023

Output: results/figures/kandy_decomp/pub/eda.png
"""
from __future__ import annotations

import glob
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

PROC = HERE / "data" / "processed" / "stage1_v3"
OUT = HERE / "results" / "figures" / "kandy_decomp" / "pub"
TEAL = "#2A9D8F"; CORAL = "#E76F51"; GREEN = "#5B8C5A"; SLATE = "#374151"


def main():
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4), constrained_layout=True)

    # (a) FECT coverage by sensor × year
    d = pd.read_parquet(PROC / "dataset_v3_hourly.parquet",
                        columns=["sensor_id", "datetime_utc"])
    d["yr"] = pd.to_datetime(d["datetime_utc"], utc=True).dt.year
    cov = d.groupby(["sensor_id", "yr"]).size().unstack(fill_value=0)
    yrs = list(range(2019, 2025)); w = 0.38
    ak = [cov.loc[12451].get(y, 0) for y in yrs]
    ha = [cov.loc[33495].get(y, 0) if 33495 in cov.index else 0 for y in yrs]
    x = np.arange(len(yrs))
    ax[0].bar(x - w / 2, ak, w, color=TEAL, label="Akurana")
    ax[0].bar(x + w / 2, ha, w, color=CORAL, label="Hantana")
    ax[0].set_xticks(x); ax[0].set_xticklabels(yrs)
    ax[0].set_ylabel("hourly observations"); ax[0].legend(fontsize=8)
    ax[0].set_title("(a) FECT coverage is sparse + intermittent\n→ lag-free T(t) "
                    "(2024 = Akurana-only, 30.5%)", fontsize=9)
    ax[0].annotate("2024:\nAkurana\nonly", (5 - w / 2, ak[-1]), (4.3, max(ak) * 0.7),
                   fontsize=7, color=SLATE, arrowprops=dict(arrowstyle="->", color=SLATE))

    # (b) VanD bias correction
    v = pd.read_csv(PROC / "vandonkelaar_kandy_annual.csv")
    v = v[v.year.between(2019, 2023)]
    xb = np.arange(len(v))
    ax[1].bar(xb, v.basin_mean, 0.5, color=TEAL, label="VanD basin = AREA level (β≡1)")
    ax[1].axhline(24.52, color=CORAL, ls="--", lw=1.2, label="KOALA = valley FLOOR (24.5)")
    ax[1].axhline(10.5, color=SLATE, ls=":", lw=1.2, label="FECT-Hantana = RIDGE (10.5)")
    ax[1].set_xticks(xb); ax[1].set_xticklabels(v.year.astype(int))
    ax[1].set_ylabel("PM₂.₅ (µg m⁻³)"); ax[1].legend(fontsize=7)
    ax[1].set_title("(b) Area-vs-floor: basin AREA mean ~17–21 sits BELOW the\n"
                    "KOALA floor (24.5) and ABOVE the Hantana ridge (10.5)", fontsize=9)

    # (c) inter-annual product disagreement
    rows = {}
    for f in sorted(glob.glob(str(HERE / "data/external/tier_c/maiac/maiac_aod_*.csv"))):
        y = int(f.split("_")[-1][:4]); dd = pd.read_csv(f)
        c = [c for c in dd.columns if "aod" in c.lower()][0]
        rows[y] = float(dd[c].mean(skipna=True))
    maiac = pd.Series(rows)
    yy = list(range(2019, 2024))
    L = [float(v.set_index("year").L_corrected[y]) for y in yy]
    M = [maiac[y] for y in yy]
    a2 = ax[2]; a2b = a2.twinx()
    a2.plot(yy, L, "-o", color=TEAL, label="VanD level (µg m⁻³)")
    a2b.plot(yy, M, "-s", color=CORAL, label="MAIAC AOD")
    a2.set_xticks(yy); a2.set_ylabel("VanD level (µg m⁻³)", color=TEAL)
    a2b.set_ylabel("MAIAC AOD", color=CORAL)
    a2.set_title("(c) VanD level vs MAIAC AOD don't track (r=0.19)\n→ no substitute "
                 "level for 2024 → product = 2019–2023", fontsize=9)
    a2.tick_params(axis="y", colors=TEAL); a2b.tick_params(axis="y", colors=CORAL)

    fig.suptitle("Exploratory data analysis — justifying the decomposition design choices",
                 fontsize=12)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"eda.{ext}", dpi=220, bbox_inches="tight")
    print("Wrote", OUT / "eda.png")


if __name__ == "__main__":
    main()
