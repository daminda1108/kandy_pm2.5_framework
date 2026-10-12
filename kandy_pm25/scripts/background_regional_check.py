"""background_regional_check.py -- the background's day-to-day signal against the AirShare regional network
(2026-10-12; spec docs/interval_background_checks_spec_2026-10-12.md, committed before this ran).

R(d): calibrated daily median of IQAir units within 150 km of Kandy outside the Colombo area (as local_fraction_e1.py),
>= 2 sites. The network reports from 2024-06, so the delivered 2019-2023 background cannot be scored; scored instead:
  B_method  the delivered background construction (air-mass class level x within-class GEOS-CF daily modulation,
            build_additive_field_v2) applied to 2024-2025, before the coherence cap (scale-free, r only)
  B_ext     the shipped extension-tier background (built as a monthly multiple of the extension anchor)
  GEOS-CF   the raw daily prior
  T_ext     the extension temporal anchor (basin mean); K the CEA Kandy station (comparators)
Daily r and within-month anomaly r, month-block bootstrap.
Out: data/processed/decomp/background_regional_check.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_additive_field_v2 as bv          # noqa: E402
import local_fraction_e1 as e1                # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
CEA = REPO / "data" / "external" / "cea"
TZ = "Asia/Colombo"
NB, SEED = 4000, 20261012


def regional():
    net = pd.read_csv(CEA / "network_daily.csv", parse_dates=["day"])
    net["dist_km"] = e1.km(net.lat, net.lon)
    bat = net[net.name == "Battaramulla"].pivot_table(index="day", columns="equipment_id", values="pm2_5").dropna()
    b, a = np.polyfit(bat[4], bat[1], 1)
    iq = net[(net.equipment_id == 4) & (~net.name.isin(e1.COLOMBO)) & (net.name != "Kandy")].copy()
    iq["pm"] = a + b * iq.pm2_5
    near = iq[iq.dist_km <= e1.RADIUS_KM].pivot_table(index="day", columns="name", values="pm")
    isl = iq.pivot_table(index="day", columns="name", values="pm")
    R = near[near.notna().sum(axis=1) >= 2].median(axis=1)
    Ri = isl[isl.notna().sum(axis=1) >= 2].median(axis=1)
    return R, Ri, sorted(near.columns)


def b_method(years):
    """the delivered construction's daily background signal, uncapped (annual mean scaled to 1)."""
    cls = bv.subdaily_class()
    parts = []
    for y in years:
        g = bv.geos_daily(y).rename("g")
        idx = pd.date_range(f"{y}-01-01", f"{y}-12-31 18:00", freq="6h")
        h = pd.DataFrame({"arrival": idx, "date": idx.floor("D")})
        h = h.merge(cls, on="arrival", how="left").merge(g.reset_index().rename(columns={"index": "date"}), on="date", how="left")
        cover = float(h.g.notna().mean()); ccls = float(h.marine.notna().mean())
        h["marine"] = h.marine.fillna(False).astype(bool)
        h = h[h.g.notna()]
        fm = h.marine.mean()
        # levels as in build_B_v2; the correlations depend on b_annual only through the marine contrast (B_MARINE is
        # fixed), so b_annual is set to the delivered 2019-2023 mean background (7.96, claim partition.B_mean)
        b_ann = 7.96
        b_cont = (b_ann - fm * bv.B_MARINE) / (1 - fm)
        h["level"] = np.where(h.marine, bv.B_MARINE, b_cont)
        h["gz"] = h.groupby("marine").g.transform(lambda s: s / s.mean())
        h["B"] = h.level * h.gz
        parts.append(h.groupby("date").B.mean())
        print(f"  {y}: GEOS-CF cover {cover:.2f}, class cover {ccls:.2f}, marine {fm:.2f}")
    return pd.concat(parts)


def daily_parquet(tpl, col, years, tcol="datetime_utc"):
    parts = []
    for y in years:
        p = Path(str(tpl).format(y=y))
        if p.exists():
            d = pd.read_parquet(p, columns=[tcol, col])
            t = pd.to_datetime(d[tcol], utc=True).dt.tz_convert(TZ).dt.tz_localize(None).dt.floor("D")
            parts.append(pd.Series(d[col].to_numpy(), index=t))
    return pd.concat(parts).groupby(level=0).mean()


def anom(s):
    return s - s.groupby(s.index.to_period("M")).transform("mean")


def rboot(x, y, rng):
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df) < 20:
        return None
    m = df.index.to_period("M"); groups = [df[m == u] for u in m.unique()]
    a = pd.DataFrame({"x": anom(df.x), "y": anom(df.y)})
    ga = [a[m == u] for u in m.unique()]
    bs, ba = [], []
    for _ in range(NB):
        ii = rng.integers(0, len(groups), len(groups))
        d = pd.concat([groups[i] for i in ii]); da = pd.concat([ga[i] for i in ii])
        bs.append(d.x.corr(d.y)); ba.append(da.x.corr(da.y))
    return dict(days=int(len(df)), months=int(len(groups)), r=float(df.x.corr(df.y)),
                r_ci95=[float(v) for v in np.nanpercentile(bs, [2.5, 97.5])],
                anomaly_r=float(a.x.corr(a.y)), anomaly_r_ci95=[float(v) for v in np.nanpercentile(ba, [2.5, 97.5])],
                ratio_means=float(df.x.mean() / df.y.mean()))


def main():
    rng = np.random.default_rng(SEED)
    R, Ri, sites = regional()
    kd = pd.read_csv(CEA / "kandy_aqms_daily.csv", parse_dates=["created_at"]).dropna(subset=["pm2_5"])
    K = kd.groupby(kd.created_at.dt.floor("D")).pm2_5.mean()
    Bm = b_method((2024, 2025))
    g = pd.concat([bv.geos_daily(y) for y in (2024, 2025)])
    Be = daily_parquet(DEC / "B_background_hourly_{y}_v2_drv.parquet", "B", (2024, 2025, 2026))
    Te = daily_parquet(REPO / "data/processed/decomp/kandy_decomp_predictions_{y}_additive_v3_drv.parquet", "pm25_q50",
                       (2024, 2025, 2026), tcol="time")
    arms = {"B_method": Bm, "GEOS_CF": g, "B_ext": Be, "T_ext_basin": Te, "K_station": K}
    out = {"spec": "docs/interval_background_checks_spec_2026-10-12.md", "regional_sites_near": sites,
           "against_regional_near": {}, "against_island_median": {}}
    for k, s in arms.items():
        out["against_regional_near"][k] = rboot(s, R, rng)
        out["against_island_median"][k] = rboot(s, Ri, rng)
    # all arms on the common days (where B_method, K and R all exist), so the comparison is like for like
    common = pd.concat({k: v for k, v in arms.items()}, axis=1).join(R.rename("R"), how="inner").dropna()
    out["common_days"] = {k: rboot(common[k], common.R, rng) for k in arms}
    out["common_days_n"] = int(len(common))
    p = DEC / "background_regional_check.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=1), encoding="utf-8"); os.replace(tmp, p)
    print("near sites:", sites)
    for blk in ("against_regional_near", "common_days", "against_island_median"):
        print(blk)
        for k, v in out[blk].items():
            if v:
                print(f"  {k:12s} days {v['days']:4d} r {v['r']:.2f} [{v['r_ci95'][0]:.2f},{v['r_ci95'][1]:.2f}]  "
                      f"anom {v['anomaly_r']:.2f} [{v['anomaly_r_ci95'][0]:.2f},{v['anomaly_r_ci95'][1]:.2f}]  ratio {v['ratio_means']:.2f}")


if __name__ == "__main__":
    main()
