"""C1/S3 -- is a satellite stream measuring satellite information, or recycled information?

Registered at https://osf.io/bkpyr/ section 1, BEFORE this ran.

THE FINDING THAT OPENED IT. `SATELLITE_LEVEL` is GHAP, and GHAP is not a satellite observation.
It is a fused ML product (Wei et al., Nat Commun 14:8349) trained on ~9,500 ground stations
INCLUDING OpenAQ and CNEMC -- the two networks supplying this study's entire panel -- and
predicted from a feature set that substantially overlaps the tier's other two streams: all seven
of our reanalysis drivers, plus NDVI, night lights, population and elevation from our static
geography, plus GEOS-CF, CAMS, humidity, pressure, precipitation and evaporation which we do not
carry. So the 7.6% attributed to "a satellite level" is a MIXTURE: genuine AOD information,
drivers we lack, a non-linear recombination of information already in the tier, and indirect
monitor leakage.

MAIAC `Optical_Depth_055` is an actual radiometric retrieval -- not trained on monitors, not
containing our drivers. Comparing the two measures how much of a fused product's apparent value
at a monitored city is recycled rather than new observation.

⚠ THE TWO STREAMS DIFFER IN TIME AS WELL AS PROVENANCE. GHAP enters as one annual scalar per
city; MAIAC enters as a daily series. That is not a flaw in the comparison, it IS the comparison
-- we are asking what an honest satellite stream is worth, not holding temporal resolution fixed.
Reported explicitly so the difference is never read as provenance alone.

⚠ MAIAC has cloud gaps. Missing days are left missing (HistGBM takes NaN natively) rather than
gap-filled, because filling a satellite stream with a model is how it stops being a satellite
stream. Per-city coverage is reported.

Usage:  .venv/Scripts/python.exe scripts/c1_satellite_stream_ladder.py
Out:    data/processed/modular/c1_satellite_ladder.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from modular_validation_all import FEATS, build_frame, ladder   # noqa: E402
from src.modular.budgets import get                              # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "c1_satellite_ladder.csv"
SEED = 20260823          # identical to the re-validated ladder


def fit_rung(pool, feats, label):
    """Leave-one-city-out prediction of the city-daily mean. Same as revalidate_ladder."""
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
    d = pd.concat(out, ignore_index=True)
    print(f"    {label:<16} {d.city.nunique()} cities, {len(feats)} features")
    return d


def rung_rmse(b0, st):
    """City RMSE of the bottom rung against held-out stations, via the shared ladder harness."""
    rows = []
    for city, s in st.items():
        city = str(city)
        sub = b0[b0.city == city]
        if not len(sub):
            continue
        try:
            r = ladder(city, s, sub, SEED)
        except Exception:
            r = None
        if r:
            rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    print("=== C1/S3: fused vs raw satellite stream (osf.io/bkpyr) ===\n")

    sample = pd.read_csv(MOD / "validation_sample.csv")
    manifest = pd.read_csv(MOD / "openaq_manifest.csv")
    st, pool = build_frame(sample, manifest)
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    met = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=met + ["pm25_city"]).copy()
    pool["city"] = pool.city.astype(str)

    geo = pd.read_csv(MOD / "bud0_static_geo.csv"); geo["city"] = geo.city.astype(str)
    sat = pd.read_csv(MOD / "bud0_satellite_level.csv"); sat["city"] = sat.city.astype(str)
    geo_f = [c for c in geo.columns if c not in ("city", "geo_n_stations")]
    p = pool.merge(geo, on="city", how="left").merge(sat, on="city", how="left")

    aod = pd.read_csv(MOD / "bud0_maiac_aod.csv")
    aod["city"] = aod.city.astype(str)
    aod["date"] = pd.to_datetime(aod.date)
    p["date"] = pd.to_datetime(p.date)
    p = p.merge(aod[["city", "date", "aod"]], on=["city", "date"], how="left")

    # C7: per-unit stream coverage. Restrict to cities that actually carry geography and the
    # fused level, so the three rungs are scored on one identical frame.
    ok_cities = set(geo.city) & set(sat.city)
    p = p[p.city.isin(ok_cities)].copy()
    b0 = get("Bud0")
    cov = {c: [s for s, present in
               (("static_geo", g[geo_f[0]].notna().any()),
                ("satellite_level", g.sat_level.notna().any()),
                ("drivers_reanalysis", True)) if present]
           for c, g in p.groupby("city")}
    b0.require_covers_units(cov)
    print(f"    frame: {len(p):,} city-days, {p.city.nunique()} cities "
          f"(per-city stream coverage asserted)\n")

    n_aod = p.groupby("city").aod.apply(lambda s: s.notna().mean())
    print(f"    MAIAC day coverage: median {n_aod.median():.1%}, "
          f"p10 {n_aod.quantile(.1):.1%}, min {n_aod.min():.1%}")
    print("    (cloud gaps left as gaps -- filling them would stop it being a satellite stream)\n")

    print("[fitting the three rungs, identical frame / learner / seed / folds]")
    variants = {
        "Bud0b": met + geo_f,
        "Bud0c-raw": met + geo_f + ["aod"],
        "Bud0c-fused": met + geo_f + ["sat_level"],
    }
    res = {}
    for lab, feats in variants.items():
        L = rung_rmse(fit_rung(p, feats, lab), st)
        res[lab] = L.set_index("city").rmse_Bud0
        print(f"    {lab:<16} median RMSE {res[lab].median():6.2f}   ({len(L)} cities scored)")

    common = set.intersection(*[set(v.index) for v in res.values()])
    print(f"\n    scored on {len(common)} cities common to all three variants")
    R = pd.DataFrame({k: v[sorted(common)] for k, v in res.items()})

    def gain(a, b):
        return (100.0 * (R[a] - R[b]) / R[a]).median()

    g_raw = gain("Bud0b", "Bud0c-raw")
    g_fused = gain("Bud0b", "Bud0c-fused")
    print(f"\n=== step gains from Bud0b (median of per-city ratios) ===")
    print(f"  + raw MAIAC AOD      {g_raw:+6.2f}%")
    print(f"  + fused GHAP level   {g_fused:+6.2f}%")
    print(f"  excess of fused      {g_fused - g_raw:+6.2f} pp")

    # P4: does the fused excess scale with monitor density?
    ns = pd.read_csv(MOD / "bud0_static_geo.csv")[["city", "geo_n_stations"]]
    ns["city"] = ns.city.astype(str)
    per = pd.DataFrame({"city": R.index,
                        "excess": (100 * (R["Bud0c-raw"] - R["Bud0c-fused"]) / R["Bud0c-raw"]).values})
    per = per.merge(ns, on="city", how="left").dropna()
    rho, pval = spearmanr(per.geo_n_stations, per.excess)
    print(f"\n  P4: fused excess vs station count  rho={rho:+.3f}  p={pval:.3f}  n={len(per)}")

    geo_step = 10.8   # Bud0a->Bud0b, from the re-validated ladder (claims.json step.geography)
    P = {
        "P1": (g_raw < 7.6, f"raw AOD ({g_raw:.2f}%) buys less than the 7.6% attributed to GHAP"),
        "P2": (g_raw > 0, f"raw AOD is nonetheless > 0 ({g_raw:.2f}%)"),
        "P3": (g_fused > g_raw, f"fused beats raw by {g_fused - g_raw:+.2f} pp"),
        "P4": (rho > 0 and pval < 0.05, f"fused excess larger where more monitors "
                                        f"(rho={rho:+.3f}, p={pval:.3f})"),
        "P5": (geo_step > g_raw, f"geography ({geo_step}%) still exceeds raw AOD ({g_raw:.2f}%)"),
    }
    print("\n=== REGISTERED PREDICTIONS (osf.io/bkpyr) ===")
    rows = []
    for k, (ok, txt) in P.items():
        print(f"  {k}  {'HELD    ' if ok else 'REFUTED '}  {txt}")
        rows.append(dict(kind="prediction", label=k, value=int(ok), note=txt))

    for lab in variants:
        rows.append(dict(kind="rung", label=lab, value=round(float(R[lab].median()), 3)))
    rows += [dict(kind="step", label="raw_aod", value=round(float(g_raw), 3)),
             dict(kind="step", label="fused_ghap", value=round(float(g_fused), 3)),
             dict(kind="step", label="fused_excess_pp", value=round(float(g_fused - g_raw), 3)),
             dict(kind="p4", label="rho_excess_vs_stations", value=round(float(rho), 3),
                  note=f"p={pval:.3f}, n={len(per)}")]
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
