"""
transport_overlay_demo.py — transport-overlay scenario across three real
FECT-backed 2019 wind regimes (rows: v1 smooth vs v1.1 transport; columns:
the three regimes). Each column on its own scale (magnitudes span ~3→90 µg m⁻³).

  1. Stagnant + inversion   2019-02-18 19:30 LT  E 0.5 m/s  BLH 97   FECT ~90
     → valley-bowl accumulation; strong city-core hotspot
  2. Moderate NE transport  2019-01-05 09:30 LT  NE 2.0 m/s BLH 529  FECT ~77
     → continental/transboundary air advected; downwind plume from the core
  3. SW monsoon (clean)     2019-08-08 10:30 LT  SW 4.5 m/s BLH 1109 FECT ~3
     → clean marine air, deep mixing; dispersed, swept NE

MAIAC (column AOD) cannot resolve the near-surface core hotspot in regime 1 — the
overlay is a physical SCENARIO awaiting a city-centre surface sensor to confirm.

Output: results/figures/kandy_decomp/pub/transport_demo_regimes.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
from src.stage1_satml.decomp.terrain_transport import solve_terrain, load_grids
from src.stage1_satml.decomp.figures_pub import _draw

DECOMP = HERE / "data" / "processed" / "decomp"
OUT = HERE / "results" / "figures" / "kandy_decomp" / "pub"
DATA = pd.read_parquet(HERE / "data/processed/stage1_v3/dataset_v3_hourly.parquet")
DATA["tutc"] = pd.to_datetime(DATA.datetime_utc, utc=True)
PRED = pd.read_parquet(DECOMP / "kandy_decomp_predictions_2019.parquet")
PRED["time"] = pd.to_datetime(PRED["time"], utc=True)

SCEN = [
    ("Stagnant + inversion", pd.Timestamp("2019-02-18 14:00", tz="UTC")),
    ("Moderate NE transport", pd.Timestamp("2019-01-05 04:00", tz="UTC")),
    ("SW monsoon (clean)", pd.Timestamp("2019-08-08 05:00", tz="UTC")),
]
_LATS, _LONS, _Z, _S, _DX = load_grids()


def build(t_utc):
    row = DATA.loc[(DATA["tutc"] - t_utc).abs().idxmin()]
    wdir, wspd, blh = float(row.wind_dir_10m), float(row.wind_speed_10m), float(row.blh_m)
    fect = float(DATA.loc[(DATA["tutc"] == row["tutc"]) & (DATA.sensor_id == 12451), "pm25_observed"].mean())
    if np.isnan(fect):
        fect = float(DATA.loc[(DATA["tutc"] == row["tutc"]), "pm25_observed"].mean())
    # met wind dir FROM wdir → vector points TO (wdir+180)
    ux = -wspd * np.sin(np.radians(wdir)); uy = -wspd * np.cos(np.radians(wdir))
    # TERRAIN-AWARE transport (channeling + drainage + ridge confinement); BLH carries
    # the stagnation dependence (shallow → strong drainage/pooling; deep → mixed)
    _, _, _, _, C = solve_terrain(ux, uy, blh, _LATS, _LONS, _Z, _S, _DX)
    shape = np.clip(C / (C.mean() + 1e-9), 0.4, 4.0)   # terrain-channeled SHAPE
    rgi = RegularGridInterpolator((_LATS, _LONS), shape)
    hr = PRED[PRED.time == t_utc]
    lats = np.sort(hr.lat.unique()); lons = np.sort(hr.lon.unique())
    V1 = hr.pivot(index="lat", columns="lon", values="pm25_q50").values
    LA, LO = np.meshgrid(np.clip(lats, _LATS.min(), _LATS.max()),
                         np.clip(lons, _LONS.min(), _LONS.max()), indexing="ij")
    A16 = rgi(np.stack([LA.ravel(), LO.ravel()], 1)).reshape(16, 16); A16 /= A16.mean()
    # Ventilation amplitude: the local enhancement scales ~1/(wind·BLH) (box model)
    # → strong when stagnant + shallow BLH, collapses when well-ventilated (monsoon).
    amp = float(np.clip(18.0 / (max(wspd, 0.3) * blh), 0.0, 0.5))
    A16 = np.clip(1.0 + amp * (A16 - 1.0), 0.5, 2.8)
    return dict(V1=V1, V11=V1 * A16, lats=lats, lons=lons, wdir=wdir, wspd=wspd,
                blh=blh, fect=fect, ux=ux, uy=uy, amp=amp)


def main():
    cols = [build(t) for _, t in SCEN]
    fig, ax = plt.subplots(2, 3, figsize=(14, 9), constrained_layout=True)
    for j, (c, (label, t)) in enumerate(zip(cols, SCEN)):
        lats, lons = c["lats"], c["lons"]
        vmax = float(np.ceil(max(c["V1"].max(), c["V11"].max()) / 5) * 5)
        vmin = float(np.floor(min(c["V1"].min(), c["V11"].min()) / 5) * 5)
        for r, (Z, tag) in enumerate([(c["V1"], "v1  T·S·M"), (c["V11"], "v1.1  ·transport")]):
            a = ax[r, j]
            im = _draw(a, Z, lats, lons, "turbo", show_marks=False, vmin=vmin, vmax=vmax)
            a.plot(80.6337, 7.2906, "o", mfc="white", mec="k", mew=1.0, ms=6)
            # wind arrow (length ∝ speed, points downwind)
            sc = 0.012 * min(c["wspd"], 5) / 5 + 0.004
            a.annotate("", xy=(80.60 + sc * np.sign(c["ux"] + 1e-9) * 3, 7.348 + sc * np.sign(c["uy"]) * 3),
                       xytext=(80.60, 7.348), arrowprops=dict(arrowstyle="-|>", color="k", lw=1.8))
            a.set_xticks([]); a.set_yticks([])
            cb = fig.colorbar(im, ax=a, shrink=0.8)
            a.set_ylabel(tag, fontsize=10, fontweight="bold") if j == 0 else None
        ax[0, j].set_title(f"{label}\n{t.tz_convert('Asia/Colombo'):%Y-%m-%d %H:%M} LT  ·  "
                           f"wind {c['wspd']:.1f} m/s  ·  BLH {c['blh']:.0f} m\n"
                           f"FECT {c['fect']:.0f} µg m⁻³  ·  basin {c['V1'].mean():.0f}  →  "
                           f"core {c['V11'][np.argmin(abs(lats-7.2906)), np.argmin(abs(lons-80.6337))]:.0f}",
                           fontsize=8.5)
    fig.suptitle("Transport-overlay scenario across Kandy's wind regimes (2019, FECT-backed) — "
                 "stagnant core accumulation → transboundary plume → monsoon dispersal", fontsize=12)
    fig.text(0.5, -0.015, "v1.1 is a physically-plausible SCENARIO: MAIAC column-AOD cannot confirm the near-surface "
             "core hotspot in the stagnant regime — a city-centre surface sensor would.", ha="center",
             fontsize=8.5, style="italic", color="#555")
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"transport_demo_regimes.{ext}", dpi=200, bbox_inches="tight")
    for (label, t), c in zip(SCEN, cols):
        print(f"  {label:<24} {t} wind {c['wdir']:.0f}°/{c['wspd']:.1f}  FECT {c['fect']:.0f}  "
              f"basin {c['V1'].mean():.0f} → core {c['V11'].max():.0f}")
    print(f"Wrote {OUT / 'transport_demo_regimes.png'}")


if __name__ == "__main__":
    main()
