"""
build_additive_background.py — Phase 0 of the additive background+increment reframe
(plan docs/additive_background_increment_plan_2026-06-04.md; 2026-06-05).

Constructs B(t), the seasonal/transboundary REGIONAL BACKGROUND that uniformly
affects every Kandy pixel, for the additive Lenschow (2001) model

    PM(x,y,t) = B(t) + [ T(t) - B(t) ] * P_local(x,y,t).

Two pieces:

  1. LEVEL  B_annual(year) = rural Van Donkelaar background.
     The 15-km basin mean is the TOTAL (= T-level); the background is the
     concentration the surrounding *rural* hill country sits in (regional natural
     + transboundary, minus the local Kandy urban increment). We read the Asia
     VanD 0.01-deg tile over a WIDE box around Kandy (+-0.45 deg ~ 100 km, inland
     central highlands — does not reach Colombo/coast) and take a robust rural
     low-percentile of the field as the background floor. Reported with a bracket
     (P10..P25..P50, plus ridge-obs 10.5 as the hard lower anchor) -> propagated
     to UQ downstream.

  2. SHAPE  geoscf_daily_shape(year, t) = GEOS-CF daily-mean / GEOS-CF annual mean.
     GEOS-CF is 0.25 deg (~25 km), hourly, 2018+ (decision #2, revised 2026-06-05):
     it CANNOT resolve the 1-km urban core, so its Kandy-cell series already IS a
     regional/transboundary estimator. We use its SEASONAL + SYNOPTIC (day-to-day)
     variation but hold it DIURNALLY FLAT: the diurnal morning-accumulation peak is
     a local emission+confinement effect and must live in the increment, not the
     uniform background. Hence daily resolution for B.

  B(t) = B_annual(year) * geoscf_daily_shape(year, t),  broadcast to hourly.

GATE (blocking): B(t)'s monthly climatology must match GHAP (independent) — March
peak, August trough, ~1.9x seasonal swing. Printed at the end.

Out:
  data/processed/decomp/background_b_annual.csv         (per-year level + bracket)
  data/processed/decomp/B_background_hourly_{year}.parquet  (datetime_utc, B_lo/B/B_hi)
"""
from __future__ import annotations
import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from config import KANDY_CENTRE_LAT, KANDY_CENTRE_LON

VAND_DIR = REPO / "data" / "raw" / "van_donkelaar"
GEOS_DIR = REPO / "data" / "raw" / "geos_cf"
DEC = REPO / "data" / "processed" / "decomp"
GHAP = DEC / "ghap_kandy_monthly_2019_2022.parquet"
TANCHOR = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"

YEARS = list(range(2019, 2024))
WIDE_HALF = 0.45                     # +-0.45 deg ~ +-50 km regional box (inland)
RIDGE_OBS = 10.5                     # FECT-Hantana ridge obs -> hard lower bracket
RURAL_PCTL = 10                      # central rural-background estimator (P10 floor)


def _year_of(path: str) -> int:
    return int(os.path.basename(path).split(".")[4][:4])


def rural_background_levels() -> pd.DataFrame:
    """Per-year rural VanD background over the wide regional box."""
    import xarray as xr
    la0, lo0 = KANDY_CENTRE_LAT, KANDY_CENTRE_LON
    rows = []
    for f in sorted(glob.glob(str(VAND_DIR / "V6GL02*.nc"))):
        y = _year_of(f)
        if y not in YEARS:
            continue
        ds = xr.open_dataset(f)
        da = ds["PM25"]
        sl = dict(lat=slice(la0 - WIDE_HALF, la0 + WIDE_HALF),
                  lon=slice(lo0 - WIDE_HALF, lo0 + WIDE_HALF))
        sub = da.sel(**sl)
        if sub.size == 0:            # latitude descending
            sl["lat"] = slice(la0 + WIDE_HALF, la0 - WIDE_HALF)
            sub = da.sel(**sl)
        v = np.asarray(sub.values, float)
        v = v[np.isfinite(v)]
        rows.append(dict(
            year=y, n_pix=v.size,
            rural_p10=float(np.percentile(v, 10)),
            rural_p25=float(np.percentile(v, 25)),
            rural_p50=float(np.percentile(v, 50)),
            region_mean=float(v.mean()),
        ))
        ds.close()
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def geoscf_daily_shape(year: int) -> pd.DataFrame:
    """GEOS-CF daily-mean normalised to annual mean = 1 (seasonal+synoptic shape,
    diurnally flat). Returns daily series indexed by date."""
    df = pd.read_csv(GEOS_DIR / f"kandy_geos_cf_{year}.csv", parse_dates=["datetime"])
    df = df.rename(columns={"PM25_RH35_GCC": "g"})
    df["date"] = df["datetime"].dt.floor("D")
    daily = df.groupby("date")["g"].mean()
    daily = daily / daily.mean()                      # annual mean -> 1
    return daily.rename("shape")


def build_B_hourly(year: int, b_annual: float, b_lo: float, b_hi: float) -> pd.DataFrame:
    """B(t) hourly on the T_anchor clock = b_annual * daily_shape, broadcast to hours."""
    t = pd.read_parquet(TANCHOR / f"T_kandy_hourly_{year}.parquet",
                         columns=["datetime_utc"])
    t["date"] = pd.to_datetime(t["datetime_utc"]).dt.tz_localize(None).dt.floor("D")
    shape = geoscf_daily_shape(year)
    s = t["date"].map(shape)
    s = s.fillna(s.mean() if np.isfinite(s.mean()) else 1.0)
    # renormalise the realised shape over THIS clock so annual mean(B)=b_annual exactly
    s = s / s.mean()
    out = pd.DataFrame({"datetime_utc": t["datetime_utc"],
                        "B": b_annual * s, "B_lo": b_lo * s, "B_hi": b_hi * s})
    return out


def ghap_monthly_clim() -> pd.Series:
    g = pd.read_parquet(GHAP)
    return g.groupby("month")["ghap_pm25"].mean()


def B_monthly_clim() -> pd.Series:
    """Pooled monthly climatology of the assembled B(t) across years (central)."""
    frames = []
    for y in YEARS:
        p = DEC / f"B_background_hourly_{y}.parquet"
        if p.exists():
            d = pd.read_parquet(p)
            d["month"] = pd.to_datetime(d["datetime_utc"]).dt.month
            frames.append(d[["month", "B"]])
    allm = pd.concat(frames)
    return allm.groupby("month")["B"].mean()


def main():
    DEC.mkdir(parents=True, exist_ok=True)
    vand = pd.read_csv(REPO / "data" / "processed" / "stage1_v3" /
                       "vandonkelaar_kandy_annual.csv").set_index("year")

    rural = rural_background_levels()
    rural["vand_basin"] = rural["year"].map(vand["basin_mean"])
    # central background = rural P10 (cleanest regional pixels = rural floor; user
    # decision 2026-06-05); bracket: [ridge 10.5 .. rural P25] propagated to UQ
    rural["B_central"] = rural["rural_p10"]
    rural["B_lo"] = RIDGE_OBS
    rural["B_hi"] = rural["rural_p25"]
    rural["increment"] = rural["vand_basin"] - rural["B_central"]
    rural["increment_frac_pct"] = (rural["increment"] / rural["vand_basin"] * 100).round(1)
    rural.to_csv(DEC / "background_b_annual.csv", index=False)

    print("=== Phase 0: rural-VanD background level (regional +-0.45deg box) ===")
    print(rural[["year", "rural_p10", "rural_p25", "rural_p50", "region_mean",
                 "vand_basin", "B_central", "increment", "increment_frac_pct"]]
          .round(2).to_string(index=False))
    print(f"\n  central B = rural P{RURAL_PCTL}; bracket [ridge {RIDGE_OBS} .. rural P25]")
    print(f"  mean local-increment fraction: {rural['increment_frac_pct'].mean():.1f}% "
          f"(governing principle: ~20-25% local)")

    # assemble B(t) hourly per year
    for _, r in rural.iterrows():
        b = build_B_hourly(int(r.year), r.B_central, r.B_lo, r.B_hi)
        b.to_parquet(DEC / f"B_background_hourly_{int(r.year)}.parquet", index=False)

    # GATE: B monthly clim vs GHAP
    print("\n=== Phase 0 GATE: B(t) seasonal cycle vs GHAP (independent) ===")
    bm = B_monthly_clim()
    gm = ghap_monthly_clim()
    j = pd.DataFrame({"B": bm, "GHAP": gm}).dropna()
    r = float(np.corrcoef(j["B"], j["GHAP"])[0, 1])
    b_swing = bm.max() / bm.min(); g_swing = gm.max() / gm.min()
    print(f"  month  B(norm)   GHAP")
    for m in range(1, 13):
        bb = bm.get(m, np.nan); gg = gm.get(m, np.nan)
        print(f"   {m:2d}   {bb:6.2f}   {gg:6.2f}")
    print(f"\n  B peak month   = {int(bm.idxmax())}   trough = {int(bm.idxmin())}")
    print(f"  GHAP peak month= {int(gm.idxmax())}   trough = {int(gm.idxmin())}")
    print(f"  seasonal swing : B {b_swing:.2f}x   GHAP {g_swing:.2f}x")
    print(f"  monthly-clim correlation r(B, GHAP) = {r:+.3f}")
    ok = (r >= 0.7) and (bm.idxmax() in (3, 4)) and (bm.idxmin() in (7, 8, 9))
    print(f"\n  GATE {'PASS' if ok else 'REVIEW'}: "
          f"{'Mar/Apr peak + Jul-Sep trough + r>=0.7' if ok else 'check peak/trough/r'}")
    print(f"\nWrote {DEC/'background_b_annual.csv'} + B_background_hourly_{{2019..2023}}.parquet")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
