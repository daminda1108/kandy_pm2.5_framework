"""The full budget ladder on the HONEST satellite stream — re-deriving F.92 after C1.

F.95 established that raw MAIAC AOD is worth as much as the fused GHAP product (+5.97% vs
+5.37%), so `SATELLITE_LEVEL` should be an actual radiometric retrieval rather than a model
trained on this panel's own monitors. But C1 only compared BOTTOM-RUNG variants. Every rung
above `Bud0c` -- and therefore every number F.92's acquisition recommendation rests on -- was
still computed on GHAP.

⚠ WHY THE ARGUMENT WAS NOT ENOUGH. It is tempting to reason: C1 showed the satellite stream's
value is not leakage, therefore the deep-tropical background collapse (28.1% -> 8.5%) rests on
honest information, therefore F.92's inversion stands. That is an inference, not a measurement,
and there is a specific reason to distrust it: **GHAP enters as one annual scalar; MAIAC enters
as a daily series.** A daily satellite stream can substitute for a background station far more
effectively than an annual one, which would push the background rung lower still -- or behave
differently above `Bud0c` in ways the bottom rung cannot reveal.

Writes to its OWN file. `ladder_revalidated.csv` is what F.85 and the OSF `g6hqb` registration
rest on and is not overwritten; the C1 pre-registration called for the ladder to be reported
both ways, and this is that.

Usage:  .venv/Scripts/python.exe scripts/ladder_maiac.py
Out:    data/processed/modular/ladder_maiac.csv
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
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from modular_validation_all import FEATS, build_frame, ladder      # noqa: E402
from revalidate_ladder import coastal_flags                        # noqa: E402
from src.modular.budgets import require_stream_coverage            # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "ladder_maiac.csv"
SEED = 20260823          # identical to the GHAP ladder, so the two are comparable


def fit_rung(pool, feats, label):
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
    print(f"    {label:<28} {d.city.nunique()} cities, {len(feats)} features", flush=True)
    return d


def main() -> None:
    print("=== the ladder on raw MAIAC AOD (re-deriving F.92 after F.95) ===\n")

    st, pool = build_frame(pd.read_csv(MOD / "validation_sample.csv"),
                           pd.read_csv(MOD / "openaq_manifest.csv"))
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    met = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=met + ["pm25_city"]).copy()
    pool["city"] = pool.city.astype(str)

    geo = pd.read_csv(MOD / "bud0_static_geo.csv"); geo["city"] = geo.city.astype(str)
    geo_f = [c for c in geo.columns if c not in ("city", "geo_n_stations")]
    p = pool.merge(geo, on="city", how="left")

    aod = pd.read_csv(MOD / "bud0_maiac_aod.csv")
    aod["city"] = aod.city.astype(str); aod["date"] = pd.to_datetime(aod.date)
    p["date"] = pd.to_datetime(p.date)
    p = p.merge(aod[["city", "date", "aod"]], on=["city", "date"], how="left")
    p = p[p.city.isin(set(geo.city))].copy()

    # gotcha #85 -- assert the stream's VALUES before fitting anything on it.
    require_stream_coverage(p, "aod", unit="city", min_unit_fraction=0.10, min_units_covered=0.90)
    cov = p.groupby("city").aod.apply(lambda s: s.notna().mean())
    print(f"    frame {len(p):,} city-days, {p.city.nunique()} cities | "
          f"AOD day coverage median {cov.median():.1%}\n")

    print("[fitting the decomposed bottom rung, leave-one-city-out]")
    rungs = {
        "Bud0a": fit_rung(p, met, "Bud0a  drivers"),
        "Bud0b": fit_rung(p, met + geo_f, "Bud0b  + static geo"),
        "Bud0c": fit_rung(p, met + geo_f + ["aod"], "Bud0c  + MAIAC AOD"),
    }

    print("\n[scoring the full ladder from each bottom rung]")
    rows = []
    for name, b0 in rungs.items():
        for city, s in st.items():
            city = str(city)
            if city not in set(b0.city):
                continue
            try:
                r = ladder(city, s, b0[b0.city == city], SEED)
            except Exception:
                r = None
            if r:
                r["bottom"] = name
                rows.append(r)
    L = pd.DataFrame(rows)
    man = pd.read_csv(MOD / "openaq_manifest.csv"); man["city"] = man.cluster.astype(str)
    L = L.merge(coastal_flags(), on="city", how="left").merge(
        man[["city", "frac_reference", "band"]], on="city", how="left", suffixes=("", "_m"))
    L["cls"] = np.where(L.frac_reference >= 0.5, "reference", "LCS")
    L.to_csv(OUT, index=False)
    print(f"    {len(L)} rows -> {OUT.name}")

    # ── the comparison that matters ───────────────────────────────────────────────────────
    g = pd.read_csv(MOD / "ladder_revalidated.csv")

    def steps(d, lab):
        x = d[d.bottom == "Bud0c"]
        f = lambda a, b: float((100 * (a - b) / a).median())
        return dict(source=lab, n=len(x),
                    first2=round(f(x.rmse_Bud0, x.rmse_Bud1), 1),
                    next6=round(f(x.rmse_Bud1, x.rmse_Bud2), 1),
                    background=round(f(x.rmse_Bud2, x.rmse_Bud3), 1))

    print("\n=== POOLED ladder, GHAP vs MAIAC ===")
    print(f"  {'stream':<16}{'n':>4}{'+2 stns':>10}{'+6 more':>10}{'+background':>13}")
    out_rows = []
    for d, lab in [(g, "GHAP (fused)"), (L, "MAIAC (raw)")]:
        r = steps(d, lab); out_rows.append(r)
        print(f"  {lab:<16}{r['n']:>4}{r['first2']:>9.1f}%{r['next6']:>9.1f}%"
              f"{r['background']:>12.1f}%")

    print("\n=== F.92 RE-DERIVED: the deep-tropical band (Kandy's own) ===")
    print(f"  {'stream':<16}{'n':>4}{'+2 stns':>10}{'+background':>13}   verdict")
    for d, lab in [(g, "GHAP (fused)"), (L, "MAIAC (raw)")]:
        x = d[(d.bottom == "Bud0c") & (d.band == "deep_tropical")]
        f = lambda a, b: float((100 * (a - b) / a).median())
        s1, s3 = f(x.rmse_Bud0, x.rmse_Bud1), f(x.rmse_Bud2, x.rmse_Bud3)
        verdict = "local stations WIN" if s1 > s3 else "background wins"
        print(f"  {lab:<16}{len(x):>4}{s1:>9.1f}%{s3:>12.1f}%   {verdict}")
        out_rows.append(dict(source=lab + " deep_tropical", n=len(x),
                             first2=round(s1, 1), background=round(s3, 1),
                             next6=np.nan))

    pd.DataFrame(out_rows).to_csv(MOD / "ladder_maiac_comparison.csv", index=False)
    print(f"\nwrote {OUT.name} and ladder_maiac_comparison.csv")


if __name__ == "__main__":
    main()
