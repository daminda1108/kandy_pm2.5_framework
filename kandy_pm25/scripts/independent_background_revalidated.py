"""independent_background_revalidated.py -- is the Bud3 gain regional air, or the same network?

THE OBJECTION THIS ANSWERS. The `Bud3` background is the 10th percentile of the target city's own
OUTER-RING stations. It is the largest single gain on the ladder, and it is the one rung that
could be an artefact: an outer-ring station shares the city's instruments, calibration, siting
conventions and operator. Some of that gain may be "more of the same network" rather than
regional air. Stated as a headline without this test, "a regional background station is worth X"
is not the claim the experiment supports.

THE TEST. Rebuild the background from a DIFFERENT CITY, 30-300 km away, whose stations the target
never sees, and run it through an IDENTICAL Bud0c -> Bud1 -> Bud2 -> Bud3 chain. Below 30 km a
donor is really the same urban area; beyond 300 km it is a different air mass. If the independent
background recovers a comparable share of the gain, the rung carries genuine regional
information. If it collapses, the headline is substantially a same-network artefact.

WHY THIS RE-RUN EXISTS. `independent_background.py` ran this on the PRE-F.84 ladder, whose bottom
rung used one of the three streams its budget admits. Both of its arms shared that defect, so its
RECOVERY FRACTION was largely protected -- but its absolute gains were measured against an
artificially weak baseline and are not quotable beside the current ladder. This version fits the
same `Bud0c` bottom rung that `ladder_revalidated.csv` uses, so the two are directly comparable.

WHAT IT CANNOT SETTLE, stated because the result is easy to over-read. Recovery tracks donor
DISTANCE, and the own-network ring sits ~5-15 km out while donors sit at 70-220 km. The gap
therefore conflates "same network" with "much closer". This test bounds the artefact from above;
it does not measure it.

Usage: python scripts/independent_background_revalidated.py [--seed N]
Out:   data/processed/modular/independent_background_revalidated.csv
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
warnings.filterwarnings("ignore")

from modular_validation_all import FEATS, build_frame, ladder  # noqa: E402
import modular_validation_all as mv                            # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "independent_background_revalidated.csv"
D_MIN_KM, D_MAX_KM = 30.0, 300.0
SEED = 20260823          # the seed ladder_revalidated.csv was fitted under
MIN_OVERLAP_DAYS = 120


def haversine(a_lat, a_lon, b_lat, b_lon):
    r = 6371.0
    p1, p2 = np.radians(a_lat), np.radians(b_lat)
    dp, dl = p2 - p1, np.radians(b_lon - a_lon)
    h = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(h))


def fit_bud0c(pool: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    """Leave-one-city-out prediction of the city-daily mean. Identical to revalidate_ladder."""
    out = []
    for city in sorted(pool.city.unique()):
        tr, te = pool[pool.city != city], pool[pool.city == city]
        assert city not in set(tr.city), "LOCO violated"
        if len(tr) < 1000 or len(te) < 100:
            continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, random_state=SEED)
        m.fit(tr[feats], tr.pm25_city)
        out.append(pd.DataFrame({"city": city, "date": te.date.values,
                                 "bud0": m.predict(te[feats])}))
    return pd.concat(out, ignore_index=True)


def donor_pool() -> pd.DataFrame:
    rows = []
    man = pd.read_csv(MOD / "openaq_manifest.csv")
    for r in man[man.status == "OK"].itertuples():
        rows.append(dict(cid=str(int(r.cluster)), src="OpenAQ", lat=r.lat, lon=r.lon))
    cen = pd.read_csv(MOD / "panel_census.csv")
    for r in cen.itertuples():
        if pd.notna(r.lat):
            rows.append(dict(cid=str(r.slug), src="CNEMC", lat=r.lat, lon=r.lon))
    return pd.DataFrame(rows).drop_duplicates("cid")


def donor_daily(cid: str, src: str) -> pd.Series | None:
    """Daily 10th percentile across the donor city's stations."""
    try:
        s = mv.stations_openaq(int(cid)) if src == "OpenAQ" else mv.stations_cnemc(cid)
    except Exception:
        return None
    if s.empty or s.station_id.nunique() < 3:
        return None
    return s.groupby("date").pm25.quantile(0.10)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()

    print("=== independent background, re-run on the CORRECTED (Bud0c) bottom rung ===\n")

    print("[1] frame")
    sample = pd.read_csv(MOD / "validation_sample.csv")
    manifest = pd.read_csv(MOD / "openaq_manifest.csv")
    st, pool = build_frame(sample, manifest)
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    met = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=met + ["pm25_city"])
    pool["city"] = pool.city.astype(str)

    geo = pd.read_csv(MOD / "bud0_static_geo.csv")
    geo["city"] = geo.city.astype(str)
    sat = pd.read_csv(MOD / "bud0_satellite_level.csv")
    sat["city"] = sat.city.astype(str)
    geo_f = [c for c in geo.columns if c not in ("city", "geo_n_stations")]
    p = pool.merge(geo, on="city", how="left").merge(sat, on="city", how="left")
    feats = met + geo_f + ["sat_level"]
    print(f"    {len(p)} city-days, {p.city.nunique()} cities, {len(feats)} Bud0c predictors")

    print("\n[2] fitting Bud0c, leave-one-city-out")
    b0 = fit_bud0c(p, feats)
    print(f"    {b0.city.nunique()} cities scored")

    print("\n[3] pairing each target with an independent donor")
    dpool = donor_pool()
    sample["cid"] = np.where(sample.src == "OpenAQ",
                             sample.cluster.fillna(-1).astype(int).astype(str),
                             sample.slug.astype(str))
    uniq = sample.drop_duplicates("cid").set_index("cid")
    coords = uniq[["lat", "lon"]]
    src_of = uniq["src"]
    band_of = uniq["band"] if "band" in uniq.columns else None

    rows = []
    for cid in sorted(b0.city.unique()):
        if cid not in coords.index:
            continue
        band = str(band_of.get(cid, "unknown")) if band_of is not None else "unknown"
        tlat, tlon = coords.loc[cid, "lat"], coords.loc[cid, "lon"]
        q = dpool[dpool.cid != cid].copy()
        q["d"] = haversine(tlat, tlon, q.lat.values, q.lon.values)
        cand = q[(q.d >= D_MIN_KM) & (q.d <= D_MAX_KM)].sort_values("d")
        if cand.empty:
            rows.append(dict(city=cid, band=band, status="no donor in range"))
            continue

        try:
            s = (mv.stations_openaq(int(cid)) if src_of.get(cid) == "OpenAQ"
                 else mv.stations_cnemc(cid))
        except Exception:
            rows.append(dict(city=cid, band=band, status="target unreadable"))
            continue

        # the held-out target series, reproduced exactly as ladder() splits it
        rng = np.random.default_rng(a.seed)
        ids = np.array(sorted(s.station_id.unique()))
        rng.shuffle(ids)
        n_hold = max(3, len(ids) // 3)
        obs_s = s[s.station_id.isin(ids[:n_hold])].groupby("date").pm25.mean().rename("obs")

        got = None
        for c in cand.itertuples():
            bg = donor_daily(c.cid, c.src)
            if bg is None:
                continue
            j = pd.concat([obs_s, bg.rename("bg")], axis=1).dropna()
            if len(j) >= MIN_OVERLAP_DAYS:
                got = (c.cid, float(c.d), j)
                break
        if got is None:
            rows.append(dict(city=cid, band=band, status="donor has no overlap",
                             d_km=float(cand.iloc[0].d)))
            continue

        dcid, dkm, j = got
        b0c = b0[b0.city == cid]
        base = ladder(cid, s, b0c, a.seed)                       # own outer ring
        alt = ladder(cid, s, b0c, a.seed, bg_override=j.bg)      # independent donor
        if not base or not alt or "rmse_Bud3" not in base or "rmse_Bud3" not in alt:
            rows.append(dict(city=cid, band=band, status="chain incomplete", d_km=round(dkm, 1)))
            continue
        rows.append(dict(city=cid, band=band, status="ok", donor=dcid, d_km=round(dkm, 1),
                         n_days=len(j), rmse_Bud2=base["rmse_Bud2"],
                         rmse_Bud3=base["rmse_Bud3"], rmse_Bud3_indep=alt["rmse_Bud3"],
                         w_own=base.get("w_Bud3"), w_indep=alt.get("w_Bud3")))

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"\n    {len(out)} targets -> {OUT.name}")
    print(out.status.value_counts().to_string())

    ok = out[out.status == "ok"].copy()
    if not len(ok):
        print("no scored pairs")
        return
    ok["gain_own"] = 100 * (1 - ok.rmse_Bud3 / ok.rmse_Bud2)
    ok["gain_indep"] = 100 * (1 - ok.rmse_Bud3_indep / ok.rmse_Bud2)

    print("\n=== same-network vs INDEPENDENT background (median % RMSE reduction) ===")
    g = ok.groupby("band").agg(n=("city", "size"), d_km=("d_km", "median"),
                               own=("gain_own", "median"),
                               indep=("gain_indep", "median"))
    g["recovered_pct"] = (100 * g.indep / g.own).round(0)
    print(g.round(1).to_string())

    own, ind = ok.gain_own.median(), ok.gain_indep.median()
    print(f"\npooled  n={len(ok)}  own {own:.1f}%  independent {ind:.1f}%  "
          f"recovered {100 * ind / own:.0f}%  | median donor {ok.d_km.median():.0f} km")

    # the confound the recovery fraction cannot separate: distance
    near = ok[ok.d_km <= ok.d_km.median()]
    far = ok[ok.d_km > ok.d_km.median()]
    for lab, sub in (("nearer half", near), ("farther half", far)):
        if len(sub):
            print(f"  {lab:<13} n={len(sub):>2}  median {sub.d_km.median():5.0f} km  "
                  f"recovered {100 * sub.gain_indep.median() / sub.gain_own.median():.0f}%")


if __name__ == "__main__":
    main()
