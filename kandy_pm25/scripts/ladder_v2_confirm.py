"""ladder_v2_confirm.py -- ingest and score the registered confirmation panel with ladder v2.

Nothing here may touch confirmation PM2.5 before the registration is lodged: --ingest and --score
REFUSE unless data/processed/modular/confirmation/REGISTERED.json exists and names an OSF id
(written by hand after lodging). --dry-run uses NO confirmation data: it relabels K discovery cities
as pseudo-confirmation cities, so every code path (union frame, meta, subset summaries) is exercised
before the freeze.

Rules identical to discovery:
  OpenAQ ingest   ingest_openaq_sample.ingest_city (<= 12 locations by record span, the city's last
                  two calendar years), output redirected to confirmation/openaq/
  CNEMC           modular_validation_all.stations_cnemc (all stations, (0, 1000) QC)
  city kept if    >= 10 stations with data and >= 200 days matched to drivers (build_frame's rules)
  daily values    station-day valid with >= 18 h, equal weight per station (E5)
  predictors      confirmation/drivers (fixed pull_city), confirmation/aod, confirmation/static_geo_grid.csv
  estimator       ladder_v2.run over the discovery + confirmation union; summaries over confirmation only

Usage:
  python scripts/ladder_v2_confirm.py --dry-run 8
  python scripts/ladder_v2_confirm.py --ingest          # after lodging only
  python scripts/ladder_v2_confirm.py --score           # after lodging only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
CD = MOD / "confirmation"
OUTD = MOD / "ladder_v2"


def _require_registered():
    f = CD / "REGISTERED.json"
    if not f.exists():
        raise SystemExit("REFUSED: confirmation data may be touched only after the registration is "
                         "lodged; confirmation/REGISTERED.json is missing")
    j = json.loads(f.read_text(encoding="utf-8"))
    if not j.get("osf"):
        raise SystemExit("REFUSED: REGISTERED.json names no OSF id")
    return j


def band(lat):
    a = abs(lat)
    return ("deep_tropical" if a < 15 else "tropical" if a < 23.5
            else "subtropical" if a < 35 else "temperate")


# ── ingest (post-registration only) ───────────────────────────────────────────────────────
def ingest():
    _require_registered()
    import ingest_openaq_sample as ios
    ios.OUT = CD / "openaq"                                   # redirect; the rule is unchanged
    M = pd.read_csv(CD / "confirmation_members.csv")
    g = pd.read_csv(REPO / "data/external/openaq/discovery/global_locations.csv", low_memory=False)
    g = g.rename(columns={"id": "location_id"})
    rows = []
    for cid, m in M.groupby("cid"):
        f = ios.OUT / f"{cid}.parquet"
        if f.exists():
            continue
        locs = m.merge(g[["location_id", "first", "last"]], on="location_id", how="left")
        locs = pd.DataFrame({"loc_id": locs.location_id, "dt_first": locs["first"],
                             "dt_last": locs["last"], "lat": locs.lat, "lon": locs.lon,
                             "provider": np.nan, "is_monitor": locs.is_monitor})
        r = ios.ingest_city(cid, locs)
        rows.append(r)
        print(f"  {cid:<16} {r['status']} stations={r['stations']} rows={r['rows']}", flush=True)
    if rows:
        man = CD / "ingest_manifest.csv"
        old = pd.read_csv(man) if man.exists() else pd.DataFrame()
        pd.concat([old, pd.DataFrame(rows)], ignore_index=True).to_csv(man, index=False)


# ── the confirmation part of the frame ────────────────────────────────────────────────────
def confirmation_frame(stream, met, geo_f, sat_feats):
    from ladder_v2 import complete_station_days
    from modular_validation_all import stations_cnemc
    from src.modular.schemas import AOD_RANGE, validate_ladder_frame
    P = pd.read_csv(CD / "confirmation_panel.csv")
    G = pd.read_csv(CD / "static_geo_grid.csv"); G["city"] = G.city.astype(str)
    st, parts, meta, dropped = {}, [], [], []
    for r in P.itertuples():
        cid = str(r.cid)
        if r.src == "CNEMC":
            s = stations_cnemc(cid)
        else:
            f = CD / "openaq" / f"{cid}.parquet"
            if not f.exists():
                dropped.append((cid, "no OpenAQ data ingested")); continue
            s = pd.read_parquet(f)
            s["date"] = pd.to_datetime(s.datetime_utc).dt.floor("D")
            s = s[["station_id", "date", "pm25", "is_monitor"]]
        if s.empty or s.station_id.nunique() < 10:
            dropped.append((cid, f"{s.station_id.nunique() if len(s) else 0} stations < 10")); continue
        frac_ref = (1.0 if r.src == "CNEMC"
                    else float(s.drop_duplicates("station_id").is_monitor.astype(float).mean()))
        sd = complete_station_days(s[["station_id", "date", "pm25"]])
        city = sd.groupby("date").pm25.mean().rename("pm25_city").reset_index()
        drv = pd.read_csv(CD / "drivers" / f"{cid}.csv"); drv["date"] = pd.to_datetime(drv.date)
        m = city.merge(drv, on="date", how="inner")
        if len(m) < 200:
            dropped.append((cid, f"{len(m)} driver-matched days < 200")); continue
        m["city"] = cid
        doy = m.date.dt.dayofyear
        m["doy_sin"] = np.sin(2 * np.pi * doy / 365.25); m["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
        g = G[G.city == cid]
        if g.empty:
            dropped.append((cid, "no grid geography")); continue
        for c in geo_f:
            m[c] = float(g[c].iloc[0])
        if stream == "maiac":
            a = pd.read_csv(CD / "aod" / f"{cid}.csv"); a["date"] = pd.to_datetime(a.date)
            m = m.merge(a[["date", "aod"]], on="date", how="left")
        else:
            raise SystemExit("confirmation is registered on MAIAC only")
        m = m.dropna(subset=met + ["pm25_city"])
        st[cid] = sd
        parts.append(m)
        meta.append(dict(city=cid, band=band(r.lat), cluster=("CNEMC" if r.src == "CNEMC" else r.country),
                         frac_reference=frac_ref, lat=r.lat, src=r.src))
    p = pd.concat(parts, ignore_index=True)
    p = validate_ladder_frame(p, met=met, static=geo_f, daily={"aod": AOD_RANGE},
                              allow_null={"dist_major_km": "censored: no major road in query"})
    return st, p, pd.DataFrame(meta).set_index("city"), dropped


def union(stream="maiac", dry_run=0, seed=20260927):
    from ladder_v2 import load
    from src.modular.city_meta import city_meta
    st, p, met, geo_f, sat_feats = load(stream, True, "grid", "v2")
    dm = city_meta(list(st)).set_index("city")[["band", "cluster", "frac_reference", "lat"]]
    if dry_run:
        rng = np.random.default_rng(seed)
        score = sorted(rng.choice(sorted(st), dry_run, replace=False).tolist())
        return (st, p, met, geo_f, sat_feats), dm, score, []
    _require_registered()
    cst, cp, cm, dropped = confirmation_frame(stream, met, geo_f, sat_feats)
    cols = list(p.columns)
    p2 = pd.concat([p, cp[[c for c in cols if c in cp.columns]]], ignore_index=True)
    st2 = {**st, **cst}
    meta = pd.concat([dm, cm[["band", "cluster", "frac_reference", "lat"]]])
    return (st2, p2, met, geo_f, sat_feats), meta, list(cst), dropped


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", type=int, metavar="K")
    g.add_argument("--ingest", action="store_true")
    g.add_argument("--score", action="store_true")
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--bag", type=int, default=5)
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    if a.ingest:
        return ingest()
    from ladder_v2 import run
    frame, meta, score, dropped = union("maiac", dry_run=a.dry_run or 0)
    print(f"union: {len(frame[0])} cities; scoring {len(score)}; dropped {len(dropped)}: {dropped}")
    S, percity, res = run("maiac", a.splits, a.bag, "crossfit", True, "grid", a.boot, True,
                          frame=frame, meta=meta, score_cities=score)
    res["dropped"] = dropped
    tag = f"confirm_{'dryrun' + str(a.dry_run) if a.dry_run else 'REGISTERED'}"
    OUTD.mkdir(parents=True, exist_ok=True)
    S.to_csv(OUTD / f"{tag}_splits.csv", index=False)
    for arm, C in percity.items():
        C.to_csv(OUTD / f"{tag}_percity_{arm}.csv")
    jp = OUTD / f"{tag}_summary.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, indent=2), encoding="utf-8"); os.replace(tmp, jp)
    for k, v in res["reconstruction"].items():
        if k.startswith("pooled.") and k.endswith("_rmse"):
            print(f"  {k:<22} n={v['n']:>3} {v['median']:+7.2f}  cluster [{v['cluster'][0]:+.2f}, "
                  f"{v['cluster'][1]:+.2f}]")
    m = res["reconstruction"]["moderator.bgm2_rmse"]
    print(f"  M1 |lat| slope {m['abs_lat']['est']:+.3f} [{m['abs_lat']['lo']:+.3f}, {m['abs_lat']['hi']:+.3f}]")
    print(f"-> {jp}")


if __name__ == "__main__":
    main()
