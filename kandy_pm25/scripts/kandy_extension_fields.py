"""kandy_extension_fields.py — Phase 5.1 stage 2: additive fields for 2024-2025.

Assembles the extension-year fields from
  * T(t)  : the driver-anchored tier  (T_kandy_hourly_{y}_drv.parquet, Phase 5.1)
  * B(t)  : its background            (B_background_hourly_{y}_v2_drv.parquet)
  * P_local: the (month x hour) CLIMATOLOGY of the locked 2019-2023 pattern

WHY a climatological pattern (and why that is honest here):
  The locked chain derives P_local per hour from a terrain solve driven by that
  hour's winds/BLH. Re-running it for the extension years is possible but the
  extension's value is the LEVEL+TIMING, not new spatial information — and Kandy's
  P_local is physics-imposed and near-static (gentle 184 m relief; spatial rho is the
  documented weak, information-limited component). Using the month x hour climatology
  therefore loses almost nothing while making the claim explicit and identical to the
  convention already planned for forecast maps: "level and timing are modelled;
  the street-scale pattern is climatological."  The webapp labels the tier as such.

  The increment-SPLIT form is preserved exactly, so the basin mean still equals T(t)
  (T-lock) hour by hour, and the pattern only structures accumulation above B.

Out: data/processed/decomp/kandy_decomp_predictions_{y}_additive_v2_drv.parquet
     results/figures/kandy_extension/extension_fields_report.txt
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data/processed/decomp"
TANC = REPO / "data/processed/stage1_v3/T_anchor"
OUT = REPO / "results/figures/kandy_extension"
BASE_YEARS = (2019, 2020, 2021, 2022, 2023)
TZ = "Asia/Colombo"
DEGEN = 0.5              # |T-B| below this -> pattern undefined; treat as flat


def pattern_climatology():
    """(month, hour) -> P_local vector (256,), from the locked additive_v2 fields.

    P is recovered on ACCUMULATION hours only (T>B+DEGEN), where
    PM = B + (T-B)*P  =>  P = (PM - B) / (T - B),  then averaged per (month, hour).
    """
    acc = {}
    grid = None
    for y in BASE_YEARS:
        f = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive_v2.parquet",
                            columns=["time", "lat", "lon", "pm25_q50"])
        f["time"] = pd.to_datetime(f.time, utc=True)
        f = f.sort_values(["time", "lat", "lon"])
        times = pd.DatetimeIndex(f.time.unique())
        if grid is None:
            grid = (np.sort(f.lat.unique()), np.sort(f.lon.unique()))
        npx = len(grid[0]) * len(grid[1])
        F = f.pm25_q50.to_numpy().reshape(len(times), npx)
        b = pd.read_parquet(DEC / f"B_background_hourly_{y}_v2.parquet")
        b["t"] = pd.to_datetime(b.datetime_utc, utc=True)
        B = b.set_index("t").B.reindex(times).to_numpy()
        T = F.mean(axis=1)                        # T-lock: basin mean == T(t)
        inc = T - B
        ok = inc > DEGEN
        P = (F[ok] - B[ok, None]) / inc[ok, None]
        lt = times[ok].tz_convert(TZ)
        for mo, hr, row in zip(lt.month, lt.hour, P):
            acc.setdefault((int(mo), int(hr)), []).append(row)
    clim = {k: np.mean(v, axis=0) for k, v in acc.items()}
    # normalise each to mean 1 (T-lock safety) and report contrast
    for k in clim:
        clim[k] = clim[k] / clim[k].mean()
    allP = np.stack(list(clim.values()))
    print(f"P climatology: {len(clim)} (month,hour) cells | "
          f"pattern range {allP.min():.3f}-{allP.max():.3f} | "
          f"mean core/edge spread {allP.std():.3f}")
    return clim, grid


def build_year(year, clim, grid):
    tf = TANC / f"T_kandy_hourly_{year}_drv.parquet"
    bf = DEC / f"B_background_hourly_{year}_v2_drv.parquet"
    if not (tf.exists() and bf.exists()):
        print(f"  {year}: SKIP (missing {tf.name} or {bf.name})")
        return None
    T = pd.read_parquet(tf)
    T["t"] = pd.to_datetime(T.datetime_utc, utc=True)
    B = pd.read_parquet(bf)
    B["t"] = pd.to_datetime(B.datetime_utc, utc=True)
    d = T.merge(B[["t", "B", "B_lo", "B_hi"]], on="t", how="inner").sort_values("t")
    lats, lons = grid
    npx = len(lats) * len(lons)
    lt = pd.DatetimeIndex(d.t).tz_convert(TZ)
    fallback = np.mean(np.stack(list(clim.values())), axis=0)
    Pm = np.stack([clim.get((int(m), int(h)), fallback) for m, h in zip(lt.month, lt.hour)])

    def split(Tq, Bq):
        inc = (Tq - Bq).to_numpy()[:, None]
        return Bq.to_numpy()[:, None] + np.maximum(inc, 0.0) * Pm + np.minimum(inc, 0.0)

    q50 = split(d.T_q50, d.B); q05 = split(d.T_q05, d.B); q95 = split(d.T_q95, d.B)
    blo = split(d.T_q50, d.B_hi); bhi = split(d.T_q50, d.B_lo)
    nt = len(d)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    out = pd.DataFrame({
        "time": np.repeat(d.t.to_numpy(), npx),
        "lat": np.tile(LA.ravel(), nt), "lon": np.tile(LO.ravel(), nt),
        "pm25_q50": q50.ravel().astype("f4"),
        "pm25_q05": np.clip(q05, 0, None).ravel().astype("f4"),
        "pm25_q95": q95.ravel().astype("f4"),
        "pm25_blo": blo.ravel().astype("f4"),
        "pm25_bhi": bhi.ravel().astype("f4")})
    fp = DEC / f"kandy_decomp_predictions_{year}_additive_v2_drv.parquet"
    out.to_parquet(fp, index=False)
    # T-lock check: hourly basin mean must equal T_q50 exactly
    basin = q50.mean(axis=1)
    g1 = float(np.abs(basin - d.T_q50.to_numpy()).max())
    ce = None
    cc = out.groupby(["lat", "lon"]).pm25_q50.mean()
    Z = cc.unstack("lon").values
    dd = np.hypot(LA - 7.2906, LO - 80.6337)
    ce = float(Z[dd <= np.percentile(dd, 20)].mean() / Z[dd >= np.percentile(dd, 80)].mean())
    line = (f"  {year}: {nt:,} h  basin {float(q50.mean()):.2f}  core/edge {ce:.2f}x  "
            f"T-lock max|Δ| {g1:.6f} {'OK' if g1 < 1e-3 else 'CHECK'}  -> {fp.name}")
    print(line)
    return line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)
    clim, grid = pattern_climatology()
    lines = [ln for y in a.years if (ln := build_year(y, clim, grid))]
    rep = ["Kandy extension fields (Phase 5.1 stage 2)",
           "T(t) = driver-anchored tier; B(t) = its background;",
           "P_local = (month x hour) climatology of the locked 2019-2023 pattern.",
           "Increment-split form preserved -> basin mean == T(t) exactly (T-lock).",
           "Honest label for the webapp: level and timing are modelled for these years;",
           "  the street-scale pattern is climatological (Kandy's pattern is",
           "  physics-imposed and near-static, so this loses little - but say it).",
           ""] + lines
    (OUT / "extension_fields_report.txt").write_text("\n".join(rep), encoding="utf-8")
    print(f"\nWrote {len(lines)} extension field(s) + {OUT/'extension_fields_report.txt'}")


if __name__ == "__main__":
    main()
