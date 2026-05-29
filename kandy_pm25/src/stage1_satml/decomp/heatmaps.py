"""
heatmaps.py — render the decomposition map PM(x,y,t)=T·S_emit·M (plan 2026-05-29).

Reads data/processed/decomp/kandy_decomp_predictions_{year}.parquet and produces:
  annual_mean.png      — annual-mean PM2.5 + PI-width maps
  seasonal_mean.png    — DJF / MAM / JJA / SON maps
  night_vs_day.png     — nocturnal vs midday maps (shows M's valley-pooling)
  diurnal_trace.png    — city-wide diurnal cycle with 90% PI band
Outputs to results/figures/kandy_decomp/.
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

from src.utils.plot_style import apply_style, PM25_CMAP

DECOMP = HERE / "data" / "processed" / "decomp"
FIG = HERE / "results" / "figures" / "kandy_decomp"
FIG.mkdir(parents=True, exist_ok=True)
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
# Universal PM2.5 colour scale — identical across all panels AND across years so
# any colour means the same µg/m³ everywhere (clean cross-season/-year reading).
PM_VMIN, PM_VMAX = 15.0, 40.0


def _grid(df, col):
    agg = df.groupby(["lat", "lon"])[col].mean().reset_index()
    p = agg.pivot(index="lat", columns="lon", values=col)
    ext = [p.columns.min(), p.columns.max(), p.index.min(), p.index.max()]
    return p.values, ext


def _hm(ax, df, col, vmin, vmax, title, cmap=PM25_CMAP):
    z, ext = _grid(df, col)
    im = ax.imshow(z, origin="lower", extent=ext, cmap=cmap, vmin=vmin, vmax=vmax,
                   aspect="auto")
    ax.scatter([80.6337], [7.2906], s=18, c="k", marker="^")  # Kandy city
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("lon"); ax.set_ylabel("lat")
    return im


def main(year: int = 2024):
    apply_style("ieee")
    fdir = FIG / str(year)
    fdir.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{year}.parquet")
    df["time"] = pd.to_datetime(df["time"], utc=True)
    lt = df["time"].dt.tz_convert("Asia/Colombo")
    df["lt_hour"] = lt.dt.hour
    df["season"] = lt.dt.month.map(SEASON)
    df["pi_width"] = df["pm25_q95"] - df["pm25_q05"]
    print(f"loaded {len(df):,} rows; annual mean {df.pm25_q50.mean():.2f}, "
          f"PI width {df.pi_width.mean():.2f} µg/m³")

    # Fig 1 — annual mean + PI width
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    im0 = _hm(ax[0], df, "pm25_q50", PM_VMIN, PM_VMAX, f"Annual mean PM₂.₅ {year}")
    fig.colorbar(im0, ax=ax[0], label="µg m⁻³")
    piw = df.groupby(["lat", "lon"])["pi_width"].mean()
    im1 = _hm(ax[1], df, "pi_width", float(piw.quantile(0.02)), float(piw.quantile(0.98)),
              "90% PI width", cmap="viridis")
    fig.colorbar(im1, ax=ax[1], label="µg m⁻³")
    fig.savefig(fdir / "annual_mean.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # Fig 2 — seasonal, TWO rows so we get both readings at once:
    #   top    = universal scale (PM_VMIN..PM_VMAX) → compare magnitude ACROSS seasons
    #   bottom = each season on its OWN min..max     → reveal WITHIN-season structure
    fig, ax = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    smean = df.groupby("season")["pm25_q50"].mean().to_dict()
    for j, s in enumerate(["DJF", "MAM", "JJA", "SON"]):
        sub = df[df.season == s]
        sm = sub.groupby(["lat", "lon"])["pm25_q50"].mean()
        imu = _hm(ax[0, j], sub, "pm25_q50", PM_VMIN, PM_VMAX,
                  f"{s}  (mean {smean[s]:.1f})")
        imp = _hm(ax[1, j], sub, "pm25_q50", float(sm.min()), float(sm.max()),
                  f"{s}  range {sm.min():.1f}–{sm.max():.1f}")
        fig.colorbar(imp, ax=ax[1, j], shrink=0.8)
    fig.colorbar(imu, ax=ax[0, :], label="µg m⁻³ (universal)", shrink=0.5)
    ax[0, 0].set_ylabel("UNIVERSAL scale\nlat")
    ax[1, 0].set_ylabel("PER-SEASON scale\nlat")
    fig.suptitle(f"Kandy {year} seasonal mean PM₂.₅ — decomposition", fontsize=12)
    fig.savefig(fdir / "seasonal_mean.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # Fig 3 — night vs day (shows M valley-pooling)
    night = df[df.lt_hour.isin([0, 1, 2, 3, 4, 5, 22, 23])]
    day = df[df.lt_hour.isin([10, 11, 12, 13, 14, 15])]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    im0 = _hm(ax[0], night, "pm25_q50", PM_VMIN, PM_VMAX,
              f"Nocturnal (22–05 LT)  mean {night.pm25_q50.mean():.1f}")
    im1 = _hm(ax[1], day, "pm25_q50", PM_VMIN, PM_VMAX,
              f"Midday (10–15 LT)  mean {day.pm25_q50.mean():.1f}")
    fig.colorbar(im1, ax=ax, label="µg m⁻³", shrink=0.7)
    fig.suptitle("Nocturnal valley-pooling vs midday mixing (M modulation)", fontsize=11)
    fig.savefig(fdir / "night_vs_day.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # Fig 4 — diurnal trace (city-wide) with PI band
    di = df.groupby("lt_hour").agg(q50=("pm25_q50", "mean"),
                                   q05=("pm25_q05", "mean"),
                                   q95=("pm25_q95", "mean")).reset_index()
    fig, a = plt.subplots(figsize=(6, 3.6))
    a.fill_between(di.lt_hour, di.q05, di.q95, alpha=0.2, color="#9c36b5", label="90% PI")
    a.plot(di.lt_hour, di.q50, "o-", color="#9c36b5", ms=4, label="PM₂.₅ q50")
    a.axvline(7, ls=":", c="grey", lw=0.8); a.axvline(18, ls=":", c="grey", lw=0.8)
    a.set_xticks(range(0, 24, 3)); a.set_xlabel("Local hour (UTC+5:30)")
    a.set_ylabel("PM₂.₅ (µg m⁻³)")
    a.set_title(f"Kandy {year} city-wide diurnal cycle (decomposition)", fontsize=9)
    a.legend(fontsize=7); a.grid(axis="y", lw=0.4, alpha=0.5)
    fig.tight_layout(); fig.savefig(fdir / "diurnal_trace.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote 4 figures to {fdir}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024)
    main(ap.parse_args().year)
