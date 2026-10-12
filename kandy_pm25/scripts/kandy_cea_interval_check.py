"""kandy_cea_interval_check.py -- coverage of the shipped 90 % interval at the CEA Kandy regulatory station
(2026-10-12; spec docs/interval_background_checks_spec_2026-10-12.md, committed before this ran).

The only earlier coverage figure (kandy_interval_coverage.py) is at the FECT sensors the anchor was fitted to, so it is
in-sample. The CEA station is the first record the field was not fitted to, apart from the level factor beta (fitted on
2019-01 -> 2021-06). Object: [q05, q95] of the delivered field at the station cell, clipped at 0 as displayed.
Out: data/processed/decomp/kandy_cea_interval_check.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
CEA = REPO / "data" / "external" / "cea"
SLAT, SLON = 7.2906, 80.6337
TZ = "Asia/Colombo"
CAL_END = pd.Timestamp("2021-07-01")
BANDS = {"night_00_05": range(0, 6), "morning_06_09": range(6, 10), "midday_11_15": range(11, 16),
         "evening_17_20": range(17, 21)}
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM", 6: "JJA", 7: "JJA", 8: "JJA",
          9: "SON", 10: "SON", 11: "SON"}


def cell(years, suffix):
    parts = []
    for y in years:
        p = DEC / f"kandy_decomp_predictions_{y}_additive_v3{suffix}.parquet"
        if not p.exists():
            continue
        f = pd.read_parquet(p, columns=["time", "lat", "lon", "pm25_q05", "pm25_q50", "pm25_q95"])
        lats, lons = np.sort(f.lat.unique()), np.sort(f.lon.unique())
        plat, plon = lats[np.abs(lats - SLAT).argmin()], lons[np.abs(lons - SLON).argmin()]
        c = f[(f.lat == plat) & (f.lon == plon)].copy()
        # field hours fall at hh:30 local (UTC + 05:30); floor to the station's hourly stamp, as the reference check does
        c["t"] = pd.to_datetime(c.time, utc=True).dt.tz_convert(TZ).dt.tz_localize(None).dt.floor("h")
        parts.append(c.set_index("t")[["pm25_q05", "pm25_q50", "pm25_q95"]])
    return pd.concat(parts).groupby(level=0).mean()


def score(j):
    if len(j) < 30:
        return None
    lo, hi, o = j.pm25_q05.clip(lower=0), j.pm25_q95.clip(lower=0), j.obs
    inside = (o >= lo) & (o <= hi)
    off = float((j.pm25_q50 - o).median())
    inside_c = (o >= lo - off) & (o <= hi - off)
    # width needed for 90 %: scale the half-widths about q50 until 90 % of hours are inside
    q50 = j.pm25_q50
    dl, du = (q50 - lo).clip(lower=1e-6), (hi - q50).clip(lower=1e-6)
    k = np.where(o < q50, (q50 - o) / dl, (o - q50) / du)
    return dict(n=int(len(j)), coverage=float(inside.mean()), below=float((o < lo).mean()), above=float((o > hi).mean()),
                mean_width=float((hi - lo).mean()), obs_mean=float(o.mean()), q50_mean=float(q50.mean()),
                median_offset=off, coverage_recentred=float(inside_c.mean()),
                width_factor_for_90=float(np.quantile(k, 0.90)))


def reading(s):
    if s is None:
        return None
    if s["coverage"] >= 0.85:
        return "consistent with nominal"
    lo_t, hi_t = s["below"], s["above"]
    one_sided = max(lo_t, hi_t) >= 3 * max(min(lo_t, hi_t), 1e-9)
    if one_sided and s["coverage_recentred"] >= 0.85:
        return "centring error, width adequate"
    return f"too narrow: width would need x{s['width_factor_for_90']:.2f} for 90 %"


def block(j):
    out = {"all": score(j)}
    out["all_reading"] = reading(out["all"])
    out["by_band"] = {b: score(j[j.index.hour.isin(list(h))]) for b, h in BANDS.items()}
    out["by_season"] = {s: score(j[j.index.month.map(SEASON) == s]) for s in ("DJF", "MAM", "JJA", "SON")}
    d = j.groupby(j.index.floor("D")).agg(obs=("obs", "mean"), pm25_q05=("pm25_q05", "mean"),
                                         pm25_q50=("pm25_q50", "mean"), pm25_q95=("pm25_q95", "mean"),
                                         n=("obs", "size"))
    out["daily_approx"] = score(d[d.n >= 18])
    # POST HOC sensitivity (not in the spec): 3-hour centred means of both series, to show how much of the hourly miss
    # could be the instrument's own hour-to-hour noise; same averaging-of-quantiles caveat as the daily row
    r3 = j.asfreq("h").rolling(3, center=True, min_periods=3).mean().dropna()
    out["posthoc_3h_mean"] = score(r3)
    return out


def main():
    h = pd.read_csv(CEA / "kandy_aqms_hourly.csv", parse_dates=["t_local"]).dropna(subset=["pm2_5"])
    h = h[(h.pm2_5 > 0) & (h.pm2_5 < 500)]
    obs = h.groupby(h.t_local.dt.floor("h")).pm2_5.mean().rename("obs")
    res = {"spec": "docs/interval_background_checks_spec_2026-10-12.md",
           "object": "[pm25_q05, pm25_q95] of additive_v3 at the station cell, clipped at 0",
           "fect_in_sample_reference": {"coverage": 0.7729, "recentred": 0.8856, "source": "kandy_interval_coverage.json"}}
    F = cell(range(2019, 2024), "")
    j = F.join(obs, how="inner").dropna()
    res["calibration_2019_2021H1"] = block(j[j.index < CAL_END])
    res["held_out_2021H2_2023"] = block(j[j.index >= CAL_END])
    res["all_2019_2023"] = block(j)
    E = cell(range(2024, 2027), "_drv")
    je = E.join(obs, how="inner").dropna()
    res["extension_2024_2026"] = block(je)
    p = DEC / "kandy_cea_interval_check.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(res, indent=1), encoding="utf-8"); os.replace(tmp, p)
    for k in ("calibration_2019_2021H1", "held_out_2021H2_2023", "all_2019_2023", "extension_2024_2026"):
        a = res[k]["all"]
        print(f"{k:24s} n {a['n']:6d} cov {a['coverage']:.3f} below {a['below']:.3f} above {a['above']:.3f} "
              f"width {a['mean_width']:.1f} off {a['median_offset']:+.2f} recentred {a['coverage_recentred']:.3f} "
              f"k90 {a['width_factor_for_90']:.2f} -> {res[k]['all_reading']}")
        print("   bands:", {b: (round(v['coverage'], 3), round(v['below'], 3), round(v['above'], 3)) for b, v in res[k]['by_band'].items() if v})
        print("   seasons:", {b: round(v['coverage'], 3) for b, v in res[k]['by_season'].items() if v})
        dd = res[k]["daily_approx"]
        if dd:
            print(f"   daily approx: n {dd['n']} cov {dd['coverage']:.3f} below {dd['below']:.3f} above {dd['above']:.3f}")


if __name__ == "__main__":
    main()
