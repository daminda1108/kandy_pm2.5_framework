"""
figure_final_deliverable.py — final four-factor deliverable maps (terrain
channelling + emission timing + vertical decoupling embedded in the solver).

Renders from kandy_decomp_predictions_{year}_4factor.parquet:
  annual_2023.png      polished annual-mean map
  multiyear.png        2019-2023 annual grid (per-year VanD level)
  seasonal_2023.png    DJF / MAM / JJA / SON
  day_night.png        mean day vs night spatial fields

WHO-referenced YlOrRd scale, terrain contours, landmarks (figures_pub conventions).
"""
from __future__ import annotations
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.figures_pub import _draw, _scale_bar, _north_arrow, LANDMARKS

DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "results" / "figures" / "monograph" / "final"
OUT.mkdir(parents=True, exist_ok=True)
CEN = (7.2906, 80.6337)
VMN, VMX = 10, 45
TICKS = [10, 15, 25, 35, 45]; TLAB = ["10 IT-4", "15 IT-3", "25 IT-2", "35 IT-1", "45"]


def _load(year):
    df = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_4factor.parquet",
                         columns=["time", "lat", "lon", "pm25_q50"])
    df["loct"] = pd.to_datetime(df.time, utc=True).dt.tz_convert("Asia/Colombo")
    return df


def _grid(df, lats, lons):
    g = df.groupby(["lat", "lon"])["pm25_q50"].mean()
    return g.unstack("lon").reindex(index=lats, columns=lons).values


def _cb(fig, im, axes):
    cb = fig.colorbar(im, ax=axes, label="PM₂.₅ (µg m⁻³)", extend="both",
                      ticks=TICKS, shrink=0.62)
    cb.ax.set_yticklabels(TLAB, fontsize=7)


def annual(year=2023):
    df = _load(year); lats = np.sort(df.lat.unique()); lons = np.sort(df.lon.unique())
    Z = _grid(df, lats, lons)
    fig, ax = plt.subplots(figsize=(6.6, 5.8), constrained_layout=True)
    im = _draw(ax, Z, lats, lons, "YlOrRd", vmin=VMN, vmax=VMX)
    for nm, (la, lo, mk) in LANDMARKS.items():
        ax.annotate(nm, (lo, la), xytext=(4, 4), textcoords="offset points", fontsize=7)
    _scale_bar(ax, lats, lons); _north_arrow(ax, lats, lons)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.set_title(f"Kandy annual-mean PM₂.₅ {year} — four-factor model\n"
                 f"basin {np.nanmean(Z):.1f} µg m⁻³ (all of Kandy exceeds WHO AQG 5)", fontsize=10)
    _cb(fig, im, ax)
    fig.savefig(OUT / f"annual_{year}.png", dpi=240, bbox_inches="tight"); plt.close(fig)


def multiyear():
    fig, axes = plt.subplots(1, 5, figsize=(18, 4.0), constrained_layout=True)
    im = None
    for ax, y in zip(axes, range(2019, 2024)):
        df = _load(y); lats = np.sort(df.lat.unique()); lons = np.sort(df.lon.unique())
        Z = _grid(df, lats, lons)
        im = _draw(ax, Z, lats, lons, "YlOrRd", show_marks=False, vmin=VMN, vmax=VMX)
        ax.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        ax.set_title(f"{y}   basin {np.nanmean(Z):.1f}", fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
    _cb(fig, im, axes)
    fig.suptitle("Kandy annual-mean PM₂.₅ 2019–2023 — four-factor model (per-year Van Donkelaar level)",
                 fontsize=12)
    fig.savefig(OUT / "multiyear.png", dpi=200, bbox_inches="tight"); plt.close(fig)


def seasonal(year=2023):
    """Two rows: top = shared WHO scale (cross-season magnitude); bottom = per-season
    scale (within-season spatial structure, so the monsoon-low JJA is not washed out)."""
    df = _load(year); df["seas"] = df.loct.dt.month % 12 // 3
    names = {0: "DJF", 1: "MAM", 2: "JJA", 3: "SON"}
    lats = np.sort(df.lat.unique()); lons = np.sort(df.lon.unique())
    Zs = [_grid(df[df.seas == s], lats, lons) for s in range(4)]
    fig, axes = plt.subplots(2, 4, figsize=(15, 8.2), constrained_layout=True)
    imu = None
    for s in range(4):
        imu = _draw(axes[0, s], Zs[s], lats, lons, "YlOrRd", show_marks=False, vmin=VMN, vmax=VMX)
        axes[0, s].plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        axes[0, s].set_title(f"{names[s]}   basin {np.nanmean(Zs[s]):.1f}", fontsize=10)
        # per-season scale reveals within-season structure
        vmn, vmx = np.nanpercentile(Zs[s], 5), np.nanpercentile(Zs[s], 97)
        iml = _draw(axes[1, s], Zs[s], lats, lons, "YlOrRd", show_marks=False, vmin=vmn, vmax=vmx)
        axes[1, s].plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        axes[1, s].set_title(f"{names[s]} (own scale {vmn:.0f}–{vmx:.0f})", fontsize=9)
        fig.colorbar(iml, ax=axes[1, s], shrink=0.75)
        for r in (0, 1):
            axes[r, s].set_xticks([]); axes[r, s].set_yticks([])
    _cb(fig, imu, axes[0, :])
    axes[0, 0].set_ylabel("shared WHO scale", fontsize=9)
    axes[1, 0].set_ylabel("per-season scale", fontsize=9)
    fig.suptitle(f"Kandy seasonal-mean PM₂.₅ {year} — top: shared scale (DJF/MAM high, "
                 f"JJA monsoon low); bottom: per-season scale (within-season structure)", fontsize=12)
    fig.savefig(OUT / f"seasonal_{year}.png", dpi=200, bbox_inches="tight"); plt.close(fig)


def day_night(year=2023):
    df = _load(year); h = df.loct.dt.hour
    day = df[(h >= 11) & (h <= 16)]; night = df[(h <= 5) | (h >= 21)]
    lats = np.sort(df.lat.unique()); lons = np.sort(df.lon.unique())
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4), constrained_layout=True)
    im = None
    for ax, sub, tag in [(axes[0], day, "day (11–16 LT, well-mixed)"),
                         (axes[1], night, "night (21–05 LT, trapped)")]:
        Z = _grid(sub, lats, lons)
        LA, LO = np.meshgrid(lats, lons, indexing="ij")
        d = np.hypot(LA - CEN[0], LO - CEN[1])
        ce = Z[d <= np.percentile(d, 20)].mean() / Z[d >= np.percentile(d, 80)].mean()
        im = _draw(ax, Z, lats, lons, "YlOrRd", show_marks=False, vmin=VMN, vmax=VMX)
        ax.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        ax.set_title(f"{tag}\nbasin {np.nanmean(Z):.1f}  core/edge {ce:.2f}×", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    _cb(fig, im, axes)
    fig.suptitle("Kandy day vs night PM₂.₅ 2023 — four-factor model "
                 "(stronger core/ridge contrast at night under the shallow boundary layer)",
                 fontsize=11)
    fig.savefig(OUT / "day_night.png", dpi=200, bbox_inches="tight"); plt.close(fig)


def main():
    annual(2023); multiyear(); seasonal(2023); day_night(2023)
    for f in ["annual_2023", "multiyear", "seasonal_2023", "day_night"]:
        print(f"Wrote {OUT/(f+'.png')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
