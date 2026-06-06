"""
figure_variation_showcase.py — PM2.5 variation across every scale, ADDITIVE headline
(2026-06-05). Shows the production additive field PM = B(t) + [T-B]*P_local at:

  showcase_temporal_scales.png  — basin-mean temporal variation, 4 panels + 90% PI:
        (a) INTER-ANNUAL  2019-2023 annual means vs VanD / GHAP, 2021 COVID low
        (b) SEASONAL      12-month climatology (Mar peak / Aug monsoon trough)
        (c) WEEKLY        day-of-week climatology (workday > Sunday; Senarathna)
        (d) DIURNAL       24-h climatology (07 LT morning peak / 14 LT trough)
  showcase_spatial_seasonal.png — annual + 4 seasonal additive maps (cividis, WHO)
  showcase_diurnal_spatial.png  — day vs night additive maps + core/edge diurnal traces
                                  (how the local increment breathes with the boundary layer)

All from data/processed/decomp/kandy_decomp_predictions_{year}_additive.parquet.
Out: results/figures/final_model_suite/showcase_*.png
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
from src.stage1_satml.decomp.figures_pub import _draw
from config import KANDY_CENTRE_LAT, KANDY_CENTRE_LON

DEC = REPO / "data" / "processed" / "decomp"
STG = REPO / "data" / "processed" / "stage1_v3"
from src.stage1_satml.decomp.pubfig import PUB_OUT as OUT  # publication style + folder
OUT.mkdir(parents=True, exist_ok=True)
CMAP, VMN, VMX = "cividis", 12, 30
WHO_T, WHO_L = [15, 20, 25, 30], ["15 IT-3", "20", "25 IT-2", "30"]
CEN = (KANDY_CENTRE_LAT, KANDY_CENTRE_LON)
YEARS = list(range(2019, 2024))
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BAND = "#FCE3B4"; LINE = "#B35806"


def _load_basinmean():
    """basin-mean (over pixels) hourly series with q05/q50/q95, local time, all years."""
    frames = []
    for y in YEARS:
        d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive.parquet",
                            columns=["time", "pm25_q05", "pm25_q50", "pm25_q95"])
        bm = d.groupby("time")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
        frames.append(bm)
    bm = pd.concat(frames)
    bm.index = pd.to_datetime(bm.index, utc=True).tz_convert("Asia/Colombo")
    bm["year"] = bm.index.year; bm["month"] = bm.index.month
    bm["dow"] = bm.index.dayofweek; bm["hour"] = bm.index.hour
    # the UTC->local shift spills a sliver of boundary hours into 2018/2024;
    # keep full local years only so the inter-annual means aren't skewed by fragments
    return bm[bm["year"].between(2019, 2023)]


def _annual_grid(year, col="pm25_q50"):
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_additive.parquet",
                        columns=["time", "lat", "lon", col])
    return d


def _who_cbar(fig, im, ax, shrink=0.8):
    cb = fig.colorbar(im, ax=ax, label="PM₂.₅ (µg m⁻³)", extend="both", ticks=WHO_T, shrink=shrink)
    cb.ax.set_yticklabels(WHO_L, fontsize=7); return cb


# ───────────────────────── 1. temporal across scales ───────────────────────
def temporal_scales(bm):
    fig, ax = plt.subplots(2, 2, figsize=(13.5, 8.2), constrained_layout=True)

    # (a) inter-annual
    ya = bm.groupby("year")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    vand = pd.read_csv(STG / "vandonkelaar_kandy_annual.csv").set_index("year")
    gh = pd.read_parquet(DEC / "ghap_kandy_monthly_2019_2022.parquet").groupby("year").ghap_pm25.mean()
    a = ax[0, 0]
    a.fill_between(ya.index, ya.pm25_q05, ya.pm25_q95, color="#C6DBEF", alpha=0.6, label="90% PI")
    a.plot(ya.index, ya.pm25_q50, "o-", color="#08519C", lw=2.3, label="additive headline")
    a.plot(YEARS, [vand.loc[y, "basin_mean"] for y in YEARS], "s--", color="#41AB5D", label="VanD (area)")
    a.plot(gh.index, gh.values, "^--", color="#CB181D", label="GHAP (independent)")
    a.annotate("2021 COVID low", (2021, ya.loc[2021, "pm25_q50"] - 1.6), fontsize=8, ha="center", color="#08519C")
    a.scatter([2019], [24.52], marker="*", s=150, color="k", zorder=6, label="KOALA 2019 floor")
    a.set_title("(a) inter-annual — basin area mean", fontsize=10); a.set_xticks(YEARS)
    a.set_ylabel("PM₂.₅ (µg m⁻³)"); a.legend(fontsize=7.3, ncol=2); a.grid(alpha=0.25)

    # (b) seasonal (monthly climatology)
    mo = bm.groupby("month")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    a = ax[0, 1]
    a.fill_between(mo.index, mo.pm25_q05, mo.pm25_q95, color=BAND, alpha=0.8, label="90% PI")
    a.plot(mo.index, mo.pm25_q50, "o-", color=LINE, lw=2.3, label="median")
    a.axvspan(5.5, 8.5, color="#9ECAE1", alpha=0.25); a.text(7, mo.pm25_q05.min() + 0.5, "SW monsoon\nwashout", fontsize=7.5, ha="center", color="#2171B5")
    a.annotate("Mar peak", (3, mo.pm25_q50.max()), fontsize=8, ha="center")
    a.set_title("(b) seasonal — monthly climatology", fontsize=10)
    a.set_xticks(range(1, 13)); a.set_xticklabels(["J","F","M","A","M","J","J","A","S","O","N","D"])
    a.set_ylabel("PM₂.₅ (µg m⁻³)"); a.legend(fontsize=7.5); a.grid(alpha=0.25)

    # (c) weekly (day-of-week) — zoomed to reveal the modest workday>weekend signal
    # (standard error of the daily means, not the full PI, which would bury it)
    g = bm.groupby("dow")["pm25_q50"]
    wk = g.mean(); sem = g.sem()
    a = ax[1, 0]
    a.bar(range(7), wk.values, color=["#6BAED6"]*5 + ["#FDAE6B", "#FD8D3C"],
          yerr=sem.values, capsize=3, alpha=0.9)
    a.axhline(wk.mean(), color="grey", ls=":", lw=1, label="weekly mean")
    a.set_title("(c) weekly — day-of-week (mean ± s.e.; workday > weekend)", fontsize=9.5)
    a.set_xticks(range(7)); a.set_xticklabels(DOW)
    a.set_ylabel("PM₂.₅ (µg m⁻³)")
    lo, hi = wk.min(), wk.max(); pad = (hi - lo) * 1.6 + 0.3
    a.set_ylim(lo - pad, hi + pad)
    a.legend(fontsize=7.5); a.grid(axis="y", alpha=0.25)

    # (d) diurnal (hour-of-day)
    hr = bm.groupby("hour")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    a = ax[1, 1]
    a.fill_between(hr.index, hr.pm25_q05, hr.pm25_q95, color=BAND, alpha=0.8, label="90% PI")
    a.plot(hr.index, hr.pm25_q50, "o-", color=LINE, lw=2.3, label="median")
    a.axvline(7, color="grey", ls=":"); a.axvline(14, color="grey", ls=":")
    a.annotate("07 LT peak", (7, hr.pm25_q50.max()), fontsize=8)
    a.annotate("14 LT trough", (14, hr.pm25_q50.min()), fontsize=8, ha="left")
    a.set_title("(d) sub-daily — diurnal cycle", fontsize=10)
    a.set_xlabel("local hour"); a.set_ylabel("PM₂.₅ (µg m⁻³)"); a.set_xticks(range(0, 24, 3))
    a.legend(fontsize=7.5); a.grid(alpha=0.25)

    fig.suptitle("Kandy PM₂.₅ variation across every temporal scale — additive headline, basin area mean (2019–2023)\n"
                 "inter-annual · seasonal (Mar peak / monsoon trough) · weekly (workday > Sunday) · diurnal (07 LT morning peak)",
                 fontsize=11.5)
    fig.savefig(OUT / "showcase_temporal_scales.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote showcase_temporal_scales.png")


# ───────────────────────── 2. spatial annual + seasonal ────────────────────
# Spatial maps use the FOUR-FACTOR SCENARIO field (terrain transport + congestion +
# katabatic drainage): it carries the real urban-core hotspot, whereas the smooth
# additive headline is deliberately flat (and its S_emit*M confinement can even read
# the slightly-raised lake/core BELOW the lower fringes — see §6). Rendered with
# inferno + per-panel adaptive scaling for contrast. Labelled SCENARIO throughout.
SCN_CMAP = "inferno"


def _scn_grid(year):
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_4factor.parquet",
                        columns=["time", "lat", "lon", "pm25_q50"])
    return d


def _stretch(Z, p=(3, 99)):
    return np.nanpercentile(Z, p[0]), np.nanpercentile(Z, p[1])


def spatial_seasonal(year=2023):
    d = _scn_grid(year)
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo")
    d["seas"] = d.loct.dt.month % 12 // 3
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    names = {0: "DJF", 1: "MAM", 2: "JJA", 3: "SON"}
    def grid(sub): return sub.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
    panels = [("ANNUAL", grid(d))] + [(names[s], grid(d[d.seas == s])) for s in range(4)]

    fig, axes = plt.subplots(2, 5, figsize=(19, 8.0), constrained_layout=True)
    # row 1 — shared scale (seasonal magnitude); row 2 — per-panel stretch (structure)
    allv = np.concatenate([Z.ravel() for _, Z in panels])
    svmin, svmax = np.nanpercentile(allv, 3), np.nanpercentile(allv, 99)
    im0 = None
    for c, (ttl, Z) in enumerate(panels):
        im0 = _draw(axes[0, c], Z, lats, lons, SCN_CMAP, show_marks=False, vmin=svmin, vmax=svmax)
        axes[0, c].set_title(f"{ttl}  {np.nanmean(Z):.1f} µg m⁻³", fontsize=10)
        vmn, vmx = _stretch(Z)
        iml = _draw(axes[1, c], Z, lats, lons, SCN_CMAP, show_marks=False, vmin=vmn, vmax=vmx)
        axes[1, c].set_title(f"{ttl} (stretch {vmn:.0f}–{vmx:.0f})", fontsize=8.6)
        fig.colorbar(iml, ax=axes[1, c], shrink=0.62)
    for a in axes.ravel():
        a.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.9, ms=5); a.set_xticks([]); a.set_yticks([])
    cb = fig.colorbar(im0, ax=list(axes[0, :]), shrink=0.6, label="PM₂.₅ (µg m⁻³)")
    axes[0, 0].set_ylabel("shared scale\n(seasonal magnitude)", fontsize=9)
    axes[1, 0].set_ylabel("per-panel stretch\n(within-season structure)", fontsize=9)
    fig.suptitle(f"Kandy PM₂.₅ spatial field {year} — TRANSPORT SCENARIO (4-factor: congestion + terrain "
                 "drainage; core hotspot restored)\nrow 1 shared scale (MAM/DJF high, JJA monsoon low) · "
                 "row 2 per-panel stretch reveals the urban-core structure · amplitude a physical prior", fontsize=11)
    fig.savefig(OUT / "showcase_spatial_seasonal.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote showcase_spatial_seasonal.png")


# ───────────────────────── 3. diurnal × spatial coupling ───────────────────
def diurnal_spatial(year=2023):
    d = _scn_grid(year)                       # 4-factor scenario (core hotspot present)
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo"); d["h"] = d.loct.dt.hour
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    LA, LO = np.meshgrid(lats, lons, indexing="ij"); dist = np.hypot(LA - CEN[0], LO - CEN[1])
    core_m = dist <= np.percentile(dist, 20); edge_m = dist >= np.percentile(dist, 80)
    def grid(sub): return sub.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
    day = grid(d[(d.h >= 11) & (d.h <= 16)]); night = grid(d[(d.h <= 5) | (d.h >= 21)])
    # core/edge diurnal traces — label each row by its pixel's membership
    core_xy = set(zip(LA[core_m], LO[core_m])); edge_xy = set(zip(LA[edge_m], LO[edge_m]))
    key = list(zip(d["lat"], d["lon"]))
    d = d.assign(grp=["core" if k in core_xy else "edge" if k in edge_xy else "mid" for k in key])
    tr = d[d.grp != "mid"].groupby(["h", "grp"]).pm25_q50.mean().unstack("grp")

    fig = plt.figure(figsize=(15.5, 5.0), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.25])
    vmn, vmx = _stretch(np.concatenate([day.ravel(), night.ravel()]))  # shared night/day stretch
    for k, (Z, tag) in enumerate([(day, "(a) day 11–16 LT (well-mixed)"),
                                  (night, "(b) night 21–05 LT (trapped)")]):
        ax = fig.add_subplot(gs[0, k])
        ce = Z[core_m].mean() / Z[edge_m].mean()
        im = _draw(ax, Z, lats, lons, SCN_CMAP, show_marks=False, vmin=vmn, vmax=vmx)
        ax.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.9, ms=5)
        ax.set_title(f"{tag}\ncore/edge {ce:.2f}×", fontsize=9.5); ax.set_xticks([]); ax.set_yticks([])
        if k == 1: fig.colorbar(im, ax=ax, shrink=0.8, label="PM₂.₅ (µg m⁻³)")
    axt = fig.add_subplot(gs[0, 2])
    axt.plot(tr.index, tr["core"], "o-", color="#B2182B", lw=2, label="urban core")
    axt.plot(tr.index, tr["edge"], "s-", color="#2166AC", lw=2, label="rural edge")
    axt.fill_between(tr.index, tr["edge"], tr["core"], color="#FDDBC7", alpha=0.6)
    axt.axvline(7, color="grey", ls=":"); axt.axvline(18, color="grey", ls=":")
    axt.annotate("07 rush", (7, tr["core"].max()), fontsize=7.5); axt.annotate("18 rush", (18, tr["core"].iloc[18]), fontsize=7.5)
    axt.set_xticks(range(0, 24, 3))
    axt.set_title("(c) diurnal core vs edge — the local\nincrement breathes with the boundary layer", fontsize=9.5)
    axt.set_xlabel("local hour"); axt.set_ylabel("PM₂.₅ (µg m⁻³)"); axt.legend(fontsize=8); axt.grid(alpha=0.25)
    fig.suptitle("Sub-daily spatial coupling — TRANSPORT SCENARIO (2023): the urban-core hotspot is strongest at "
                 "night/morning (shallow boundary layer + drainage trap the rush-hour increment) and ventilates by midday",
                 fontsize=10.2)
    fig.savefig(OUT / "showcase_diurnal_spatial.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote showcase_diurnal_spatial.png")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    bm = _load_basinmean()
    temporal_scales(bm)
    spatial_seasonal(2023)
    diurnal_spatial(2023)
    print(f"\nShowcase → {OUT}")


if __name__ == "__main__":
    main()
