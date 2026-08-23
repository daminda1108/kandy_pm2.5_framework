"""revalidate_ladder.py -- the budget ladder with a spec-compliant, DECOMPOSED bottom rung.

Pre-registration: docs/prereg_revalidation_2026-08-23.md   OSF: https://osf.io/g6hqb/
Trigger:          ledger F.84

The scored `Bud0` used one of the three streams its budget admits: seven reanalysis
meteorological features, with no satellite level and no static geography. Every gain on a ladder
is measured against the rung below it, so an under-powered bottom rung inflates all of them.

Rather than replace `Bud0`, the registration DECOMPOSES it, so each globally available stream is
measured on the same footing as a ground station:

    Bud0a   reanalysis drivers only                         (= the old, under-powered Bud0)
    Bud0b   + static geography, city-level
    Bud0c   + satellite annual level                        (= the SPEC-COMPLIANT Bud0)
    Bud1    + 2 local stations
    Bud2    + 6 more local stations
    Bud3    + outer-ring stations as regional background

Registered priors (fixed before running): Bud0b->Bud0c is the largest step below the ground
rungs at 25-45%; Bud0c->Bud1 falls to 5-15% from the 24% previously reported; the ladder
FLATTENS. If it does not flatten, local stations carry information no global product does.

Everything is leave-one-city-out. R-G4 requires that nothing be pooled without also being
reported by band, by coastal/inland and by instrument class.

Usage:  python scripts/revalidate_ladder.py
Out:    data/processed/modular/ladder_revalidated.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "ladder_revalidated.csv"

from modular_validation_all import FEATS, build_frame, ladder  # noqa: E402
from src.modular.budgets import (  # noqa: E402
    DRIVERS_REANALYSIS, SATELLITE_LEVEL, STATIC_GEO, get,
)

SEED = 20260823


def coastal_flags() -> pd.DataFrame:
    """Distance to coast, Natural Earth 110 m. Threshold 50 km, fixed in the registration."""
    import cartopy.io.shapereader as shpreader
    import shapely.geometry as sg
    from shapely.ops import unary_union
    coast = unary_union(list(shpreader.Reader(shpreader.natural_earth(
        resolution="110m", category="physical", name="coastline")).geometries()))
    man = pd.read_csv(MOD / "openaq_manifest.csv")
    man = man[man.status == "OK"][["cluster", "lat", "lon"]]
    man["city"] = man.cluster.astype(str)
    smp = pd.read_csv(MOD / "validation_sample.csv")
    cn = smp[smp.src == "CNEMC"][["slug", "lat", "lon"]].rename(columns={"slug": "city"})
    cn["city"] = cn.city.astype(str)
    t = pd.concat([man[["city", "lat", "lon"]], cn], ignore_index=True).drop_duplicates("city")
    t["coast_km"] = [coast.distance(sg.Point(r.lon, r.lat)) * 111.0 for r in t.itertuples()]
    t["coastal"] = t.coast_km < 50
    return t[["city", "coast_km", "coastal"]]


def fit_rung(pool: pd.DataFrame, feats: list[str], label: str) -> pd.DataFrame:
    """Leave-one-city-out prediction of the city-daily mean from `feats`."""
    out = []
    for city in sorted(pool.city.unique()):
        tr, te = pool[pool.city != city], pool[pool.city == city]
        assert city not in set(tr.city), "LOCO violated"
        if len(tr) < 1000 or len(te) < 100:
            continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, random_state=SEED)
        m.fit(tr[feats], tr.pm25_city)
        out.append(pd.DataFrame({"city": city, "date": te.date.values, "bud0": m.predict(te[feats])}))
    d = pd.concat(out, ignore_index=True)
    print(f"    {label}: {d.city.nunique()} cities, {len(feats)} features")
    return d


def main() -> None:
    print("=== re-validated ladder (F.84) -- pre-registered at https://osf.io/g6hqb/ ===\n")

    print("[1] pool")
    sample = pd.read_csv(MOD / "validation_sample.csv")
    manifest = pd.read_csv(MOD / "openaq_manifest.csv")
    st, pool = build_frame(sample, manifest)
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    met = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=met + ["pm25_city"])
    pool["city"] = pool.city.astype(str)
    print(f"    {len(pool)} city-days, {pool.city.nunique()} cities")

    print("\n[2] streams")
    geo = pd.read_csv(MOD / "bud0_static_geo.csv"); geo["city"] = geo.city.astype(str)
    sat = pd.read_csv(MOD / "bud0_satellite_level.csv"); sat["city"] = sat.city.astype(str)
    geo_f = [c for c in geo.columns if c not in ("city", "geo_n_stations")]
    p = pool.merge(geo, on="city", how="left").merge(sat, on="city", how="left")
    print(f"    STATIC_GEO {len(geo_f)} predictors, cities matched "
          f"{p[geo_f[0]].notna().groupby(p.city).any().sum()}")
    print(f"    SATELLITE_LEVEL cities matched {p.sat_level.notna().groupby(p.city).any().sum()}")

    # ── R-G3: admissibility, both directions ──────────────────────────────────────────────
    print("\n[3] R-G3 admissibility (require_covers)")
    b0 = get("Bud0")
    b0.require(DRIVERS_REANALYSIS, SATELLITE_LEVEL, STATIC_GEO)
    b0.require_covers(DRIVERS_REANALYSIS, SATELLITE_LEVEL, STATIC_GEO)
    print("    Bud0c covers all three admitted streams: PASS")
    try:
        b0.require_covers(DRIVERS_REANALYSIS)
        print("    !! Bud0a passed require_covers -- the check is broken")
    except Exception as e:
        print(f"    Bud0a correctly REJECTED as under-powered: {str(e)[:72]}...")

    print("\n[4] fitting the decomposed bottom rung, leave-one-city-out")
    rungs = {
        "Bud0a": fit_rung(p, met, "Bud0a  drivers"),
        "Bud0b": fit_rung(p, met + geo_f, "Bud0b  + static geo"),
        "Bud0c": fit_rung(p, met + geo_f + ["sat_level"], "Bud0c  + satellite level"),
    }

    print("\n[5] scoring the full ladder from each bottom rung")
    rows = []
    for name, b0pred in rungs.items():
        for city, s in st.items():
            city = str(city)
            if city not in set(b0pred.city):
                continue
            try:
                r = ladder(city, s, b0pred[b0pred.city == city], SEED)
            except Exception:
                r = None
            if r:
                r["bottom"] = name
                rows.append(r)
    L = pd.DataFrame(rows)

    cf = coastal_flags()
    man = pd.read_csv(MOD / "openaq_manifest.csv")
    man["city"] = man.cluster.astype(str)
    L = L.merge(cf, on="city", how="left").merge(
        man[["city", "frac_reference", "band"]], on="city", how="left", suffixes=("", "_m"))
    L["cls"] = np.where(L.frac_reference >= 0.5, "reference", "LCS")
    L.to_csv(OUT, index=False)
    print(f"    {len(L)} rows -> {OUT.name}")

    # ── the ladder ────────────────────────────────────────────────────────────────────────
    piv = L.pivot_table(index="city", columns="bottom", values="rmse_Bud0")
    print("\n=== THE DECOMPOSED BOTTOM RUNG (median RMSE across cities) ===")
    for r in ("Bud0a", "Bud0b", "Bud0c"):
        if r in piv:
            print(f"  {r}  {piv[r].median():7.3f}")
    if {"Bud0a", "Bud0b", "Bud0c"} <= set(piv.columns):
        g_ab = 100 * ((piv.Bud0a - piv.Bud0b) / piv.Bud0a).median()
        g_bc = 100 * ((piv.Bud0b - piv.Bud0c) / piv.Bud0b).median()
        print(f"\n  Bud0a -> Bud0b (static geography) : {g_ab:6.2f}%   [prior 5-15%]")
        print(f"  Bud0b -> Bud0c (satellite level)  : {g_bc:6.2f}%   [prior 25-45%]")

    print("\n=== GROUND RUNGS, from each bottom (median % RMSE reduction) ===")
    print(f"  {'bottom':<8}{'n':>4}{'->Bud1':>10}{'->Bud2':>10}{'->Bud3':>10}")
    for name in ("Bud0a", "Bud0b", "Bud0c"):
        s = L[L.bottom == name]
        if s.empty:
            continue
        g1 = 100 * ((s.rmse_Bud0 - s.rmse_Bud1) / s.rmse_Bud0).median()
        g2 = 100 * ((s.rmse_Bud1 - s.rmse_Bud2) / s.rmse_Bud1).median()
        g3 = 100 * ((s.rmse_Bud2 - s.rmse_Bud3) / s.rmse_Bud2).median()
        print(f"  {name:<8}{len(s):>4}{g1:>9.2f}%{g2:>9.2f}%{g3:>9.2f}%")
    print("  [priors from Bud0c: ->Bud1 5-15% (was ~24%), ->Bud2 ~0%, ->Bud3 15-30% (was ~38-40%)]")

    # ── R-G2 monotonicity, on every rung that EXISTS (F.79) ───────────────────────────────
    print("\n=== R-G2 monotonicity (rungs that exist; a missing rung is undefined) ===")
    for name in ("Bud0a", "Bud0b", "Bud0c"):
        s = L[L.bottom == name]
        if s.empty:
            continue
        ok = s.rmse_Bud3.notna()
        m = ((s.rmse_Bud1 <= s.rmse_Bud0 + 1e-9) & (s.rmse_Bud2 <= s.rmse_Bud1 + 1e-9)
             & ((s.rmse_Bud3 <= s.rmse_Bud2 + 1e-9) | ~ok))
        print(f"  {name}: {int(m.sum())}/{len(s)}")

    # ── R-G4 stratification ───────────────────────────────────────────────────────────────
    print("\n=== R-G4: THE COASTAL TEST (does the F.78 diagnosis survive?) ===")
    c = L[L.bottom == "Bud0a"].set_index("city").rmse_Bud0.rename("a")
    z = L[L.bottom == "Bud0c"].set_index("city").rmse_Bud0.rename("c")
    j = pd.concat([c, z, L[L.bottom == "Bud0a"].set_index("city")[["coastal", "band", "cls"]]],
                  axis=1).dropna(subset=["a", "c"])
    j["gain_ac"] = 100 * (j.a - j.c) / j.a
    for lab, g in j.groupby("coastal"):
        nm = "coastal (<50 km)" if lab else "inland"
        print(f"  {nm:<18} n={len(g):>2}  Bud0a RMSE {g.a.median():6.2f}   "
              f"Bud0c RMSE {g.c.median():6.2f}   Bud0a->Bud0c gain {g.gain_ac.median():6.2f}%")
    print("  prior: Bud0a WORSE at coastal cities, and the Bud0a->Bud0c gain LARGER there.")
    print("         If coastal and inland behave alike, the F.78 diagnosis was wrong.")

    for key, lab in (("band", "latitude band"), ("cls", "instrument class")):
        print(f"\n  by {lab}:")
        for k, g in j.groupby(key):
            print(f"    {str(k):<16} n={len(g):>2}  Bud0a {g.a.median():6.2f}  "
                  f"Bud0c {g.c.median():6.2f}  gain {g.gain_ac.median():6.2f}%")


if __name__ == "__main__":
    main()
