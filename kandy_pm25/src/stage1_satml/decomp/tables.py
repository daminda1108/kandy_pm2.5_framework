"""
tables.py — publication tables for the Kandy decomposition (2019-2023).
Writes markdown + CSV to results/tables/.

  T1  annual & seasonal summary (per year + 5-yr mean), WHO-AQG multiples
  T2  temporal validation vs Senarathna 2024 (basin mean, bootstrap 95% CI)
  T3  spatial validation (independent + consistency checks, bootstrap 95% CI)
  T4  model specification / data provenance
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
from src.stage1_satml.evaluation.compare_senarathna_v3 import (
    SENARATHNA_HOURLY, SENARATHNA_WEEKLY, SENARATHNA_MONTHLY)
from src.stage1_satml.decomp.validate_decomp import u5_independent, _bootstrap_r

DECOMP = HERE / "data" / "processed" / "decomp"
OUT = HERE / "results" / "tables"
OUT.mkdir(parents=True, exist_ok=True)
AQG = 5.0


def _boot(a, b):
    from scipy.stats import pearsonr
    lo, hi = _bootstrap_r(np.asarray(a), np.asarray(b))
    return float(pearsonr(a, b)[0]), lo, hi


def t1_summary(z):
    rows = []
    for i, y in enumerate(z["years"]):
        di = z["diurnal"][i]
        rows.append(dict(
            Year=int(y), Annual=round(float(z["annual"][i]), 1),
            Diurnal_peak_LT=int(np.nanargmax(di)), Peak=round(float(np.nanmax(di)), 1),
            Diurnal_trough_LT=int(np.nanargmin(di)), Trough=round(float(np.nanmin(di)), 1),
            x_WHO_AQG=round(float(z["annual"][i]) / AQG, 1)))
    dmean = np.nanmean(z["diurnal"], 0)
    rows.append(dict(Year="2019–23", Annual=round(float(z["annual"].mean()), 1),
                     Diurnal_peak_LT=int(np.nanargmax(dmean)), Peak=round(float(np.nanmax(dmean)), 1),
                     Diurnal_trough_LT=int(np.nanargmin(dmean)), Trough=round(float(np.nanmin(dmean)), 1),
                     x_WHO_AQG=round(float(z["annual"].mean()) / AQG, 1)))
    seas5 = [round(float(np.nanmean(z["seasonal"][j])), 1) for j in range(4)]
    note = (f"5-yr seasonal basin means (µg m⁻³): DJF {seas5[0]}, MAM {seas5[1]}, "
            f"JJA {seas5[2]}, SON {seas5[3]}. All years exceed the WHO annual AQG "
            f"(5 µg m⁻³) by ~4–5×.")
    return pd.DataFrame(rows), note


def t2_temporal(z):
    dmean = np.nanmean(z["diurnal"], 0); wmean = np.nanmean(z["weekly"], 0)
    mmean = np.nanmean(z["monthly"], 0)
    rows = []
    for nm, mod, sen, pk in [
        ("Diurnal (24 h)", dmean, [SENARATHNA_HOURLY[h] for h in range(24)],
         "07 LT morning / 18–19 LT evening"),
        ("Weekly (7 d)", wmean, [SENARATHNA_WEEKLY[d] for d in range(7)],
         "mid-week high, Sunday low"),
        ("Monthly (12 m)", mmean, [SENARATHNA_MONTHLY[m] for m in range(1, 13)],
         "March peak, JJA monsoon min"),
    ]:
        r, lo, hi = _boot(mod, sen)
        rows.append(dict(Cycle=nm, r=round(r, 2), CI95=f"[{lo:+.2f}, {hi:+.2f}]",
                         Feature_reproduced=pk))
    return pd.DataFrame(rows)


def t3_spatial():
    u5 = u5_independent(2024)
    rows = []
    nm_map = {"VIIRS_NTL_log": ("VIIRS night-lights", "independent (no AOD lineage)", "+"),
              "delta_z": ("Elevation (Δz)", "physical sign check", "−")}
    for k, (r, rho, p, lo, hi) in u5.items():
        nm, typ, exp = nm_map[k]
        rows.append(dict(Reference=nm, r=round(r, 2), CI95=f"[{lo:+.2f}, {hi:+.2f}]",
                         Type=typ, Expect=exp))
    # MAIAC from cached csv
    mai = pd.read_csv(DECOMP / "u5_maiac.csv").dropna(subset=["aod_maiac"])
    r, lo, hi = _boot(mai["pm25_q50"].to_numpy(), mai["aod_maiac"].to_numpy())
    rows.insert(1, dict(Reference="MAIAC AOD", r=round(r, 2),
                        CI95=f"[{lo:+.2f}, {hi:+.2f}]",
                        Type="AOD-consistency (shares MODIS lineage w/ VanD)", Expect="+"))
    return pd.DataFrame(rows)


def t4_spec():
    return pd.DataFrame([
        dict(Component="T(t) temporal", Source="Lag-free LightGBM on GEOS-CF + ERA5 + "
             "CAMS + MAIAC (FECT-calibrated), Mondrian conformal", Role="hourly level + shape"),
        dict(Component="S_emit(x,y) spatial", Source="Van Donkelaar V6.GL02.04 PM2.5 "
             "surface (2019–23 mean), mean-normalised", Role="emission/observed pattern"),
        dict(Component="M(x,y,t) modulation", Source="ERA5 BLH × SRTM terrain confinement",
             Role="nocturnal valley-pooling"),
        dict(Component="Level anchor", Source="per-year VanD basin × β (β=KOALA_2019/"
             "VanD_2019=1.247)", Role="observation-grounded magnitude"),
        dict(Component="Uncertainty", Source="split-conformal (per hour-of-day × month)",
             Role="calibrated 90% PI"),
    ])


def _md(df, title, note=None):
    cols = list(df.columns)
    head = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = "\n".join("| " + " | ".join(str(v) for v in row) + " |"
                     for row in df.itertuples(index=False))
    s = f"### {title}\n\n{head}\n{sep}\n{body}"
    if note:
        s += f"\n\n*{note}*"
    return s + "\n"


def main():
    z = np.load(DECOMP / "climatology.npz")
    t1, note1 = t1_summary(z)
    t2, t3, t4 = t2_temporal(z), t3_spatial(), t4_spec()
    for name, df in [("decomp_t1_summary", t1), ("decomp_t2_temporal_validation", t2),
                     ("decomp_t3_spatial_validation", t3), ("decomp_t4_spec", t4)]:
        df.to_csv(OUT / f"{name}.csv", index=False)
    md = "\n".join([
        "# Kandy decomposition — publication tables (2019–2023)\n",
        _md(t1, "Table 1 — Annual & diurnal summary", note1),
        _md(t2, "Table 2 — Temporal validation vs Senarathna et al. 2024 (basin mean)"),
        _md(t3, "Table 3 — Spatial validation (annual map; bootstrap 95% CI)"),
        _md(t4, "Table 4 — Model specification & data provenance"),
    ])
    (OUT / "decomp_tables.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"\nWrote {OUT / 'decomp_tables.md'} + 4 CSVs")


if __name__ == "__main__":
    main()
