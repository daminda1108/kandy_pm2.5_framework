"""kandy_interval_coverage.py — empirical coverage of the SHIPPED field's 90%
interval at Kandy (2026-08-06).

WHAT HAS AND HAS NOT BEEN MEASURED
----------------------------------
The project reports several coverage numbers and they refer to different objects:

  0.865   Stage A v3 pooled LOMO coverage of the hourly ANCHOR (60 folds) — properly
          out-of-sample in time, and the number usually quoted
  0.707   the SENSORLESS daily anchor's coverage against the local record — the honest
          out-of-regime figure, and the basis for the forecast's 1.35x widening
  ?       the coverage of the interval the webapp and the paper actually SHIP, which is
          [q05, q95] of the assembled field after amplitude sharpening and additive
          propagation

The third has never been computed. It is the one a reader is looking at. This script
computes it, at the only place Kandy has observations: the two FECT sensor pixels.

THE CIRCULARITY, STATED UP FRONT
--------------------------------
T(t) is trained on the FECT residual target AND amplitude-sharpened to the observed FECT
climatology. Scoring its intervals against FECT is therefore **in-sample** and the result
is an OPTIMISTIC bound, not a validation (gotcha #68). That is exactly why it is worth
computing: if coverage falls short of nominal even in-sample, the shipped intervals are
too narrow and the finding is unambiguous. If it meets nominal, the honest reading is
"meets nominal where it was fitted", which bounds nothing about an unmonitored pixel.

Reported by year, by season and by tier (anchored 2019-2023 vs extension 2024+), because
the extension years carry a wider stated uncertainty and should be checked separately.

Run:  .venv/Scripts/python.exe scripts/kandy_interval_coverage.py
Out:  data/processed/decomp/kandy_interval_coverage.{csv,json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
OUT_CSV = DEC / "kandy_interval_coverage.csv"
OUT_JSON = DEC / "kandy_interval_coverage.json"

EXT_YEARS = (2024, 2025, 2026)
NOMINAL = 0.90
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}


def field_path(y: int) -> Path:
    s = "_drv" if y in EXT_YEARS else ""
    return DEC / f"kandy_decomp_predictions_{y}_additive_v3{s}.parquet"


def nearest_pixel(df: pd.DataFrame, lat: float, lon: float):
    pts = df[["lat", "lon"]].drop_duplicates()
    d = (pts.lat - lat) ** 2 + (pts.lon - lon) ** 2
    r = pts.loc[d.idxmin()]
    return float(r.lat), float(r.lon)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== coverage of the SHIPPED 90% interval at the FECT pixels ===")
    obs = pd.read_parquet(STG / "dataset_v3_hourly.parquet",
                          columns=["datetime_utc", "sensor_id", "sensor_name",
                                   "lat", "lon", "pm25_observed"])
    obs["h"] = pd.to_datetime(obs.datetime_utc, utc=True)
    obs = obs.dropna(subset=["pm25_observed"])
    print(f"  {len(obs):,} sensor-hours from {obs.sensor_id.nunique()} FECT sensors")

    rows = []
    for y in sorted(obs.h.dt.year.unique()):
        fp = field_path(int(y))
        if not fp.exists():
            continue
        fld = pd.read_parquet(fp, columns=["time", "lat", "lon",
                                           "pm25_q05", "pm25_q50", "pm25_q95"])
        fld["h"] = pd.to_datetime(fld.time, utc=True)
        oy = obs[obs.h.dt.year == y]
        for sid, g in oy.groupby("sensor_id"):
            la, lo = float(g.lat.iloc[0]), float(g.lon.iloc[0])
            pla, plo = nearest_pixel(fld, la, lo)
            km = np.hypot((pla - la) * 110.6, (plo - lo) * 110.6 * np.cos(np.radians(la)))
            px = fld[(fld.lat == pla) & (fld.lon == plo)][
                ["h", "pm25_q05", "pm25_q50", "pm25_q95"]]
            j = g[["h", "pm25_observed"]].merge(px, on="h", how="inner")
            if len(j) < 50:
                continue
            # the model's convention is a physical floor at 0 (gotcha #57); the shipped
            # display clamps, so the interval is compared as displayed
            lo_, hi_ = j.pm25_q05.clip(lower=0), j.pm25_q95.clip(lower=0)
            inside = ((j.pm25_observed >= lo_) & (j.pm25_observed <= hi_))
            rows.append({"year": int(y), "sensor": str(sid),
                         "name": str(g.sensor_name.iloc[0])[:18],
                         "pixel_offset_km": round(float(km), 2),
                         "n": int(len(j)), "coverage": float(inside.mean()),
                         "mean_width": float((hi_ - lo_).mean()),
                         "below": float((j.pm25_observed < lo_).mean()),
                         "above": float((j.pm25_observed > hi_).mean()),
                         "tier": "extension" if y in EXT_YEARS else "anchored",
                         "season_cov": {s: float(inside[j.h.dt.month.map(SEASON) == s].mean())
                                        for s in ("DJF", "MAM", "JJA", "SON")
                                        if (j.h.dt.month.map(SEASON) == s).sum() >= 30}})
    if not rows:
        raise SystemExit("no overlapping field/observation hours found")
    R = pd.DataFrame(rows)

    print("\n  year  sensor              n     off(km)  coverage   width   below  above")
    for _, r in R.iterrows():
        print(f"  {r.year}  {r['name']:<18}{r.n:>6}{r.pixel_offset_km:>8.2f}"
              f"{100 * r.coverage:>9.1f}%{r.mean_width:>8.1f}"
              f"{100 * r.below:>7.1f}%{100 * r.above:>6.1f}%")

    tot_n = R.n.sum()
    pooled = float((R.coverage * R.n).sum() / tot_n)
    print(f"\n  POOLED coverage: {100 * pooled:.1f}%  (nominal {100 * NOMINAL:.0f}%, "
          f"n={tot_n:,})")
    for tier in ("anchored", "extension"):
        t = R[R.tier == tier]
        if len(t):
            c = float((t.coverage * t.n).sum() / t.n.sum())
            print(f"    {tier:<10} {100 * c:5.1f}%   (n={t.n.sum():,})")

    seas = {}
    for s in ("DJF", "MAM", "JJA", "SON"):
        vals = [(r["season_cov"][s], r["n"]) for _, r in R.iterrows()
                if s in r["season_cov"] and np.isfinite(r["season_cov"][s])]
        if vals:
            w = sum(v[1] for v in vals)
            seas[s] = sum(v[0] * v[1] for v in vals) / w
    if seas:
        print("  by season: " + "  ".join(f"{k} {100 * v:.1f}%" for k, v in seas.items()))

    verdict = ("BELOW NOMINAL even in-sample -- the shipped intervals are too narrow and "
               "this is unambiguous" if pooled < NOMINAL - 0.02 else
               "at or above nominal WHERE IT WAS FITTED; this bounds nothing about an "
               "unmonitored pixel and must not be quoted as validated coverage")
    print(f"\n  VERDICT: {verdict}")

    res = {"nominal": NOMINAL, "pooled_coverage": round(pooled, 4),
           "n_hours": int(tot_n),
           "by_tier": {t: round(float((R[R.tier == t].coverage * R[R.tier == t].n).sum()
                                      / R[R.tier == t].n.sum()), 4)
                       for t in R.tier.unique()},
           "by_season": {k: round(v, 4) for k, v in seas.items()},
           "verdict": verdict,
           "circularity_warning": (
               "T(t) is trained on the FECT residual target AND amplitude-sharpened to the "
               "observed FECT climatology, so this is an IN-SAMPLE coverage estimate and an "
               "optimistic bound (gotcha #68). The out-of-regime figure measured on the "
               "sensorless anchor is 0.707, and the forecast tier widens by 1.35x on that "
               "basis; the historical field currently does not."),
           "other_coverage_numbers": {
               "stage_a_v3_LOMO_anchor": 0.865,
               "sensorless_daily_anchor": 0.707,
               "forecast_after_widening": 0.903}}
    R.drop(columns=["season_cov"]).to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT_CSV.name} + {OUT_JSON.name}")


if __name__ == "__main__":
    main()
