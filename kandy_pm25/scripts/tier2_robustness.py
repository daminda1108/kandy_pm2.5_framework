"""tier2_robustness.py -- three loose threads a reviewer will pull.

(1) P2's single violation. Monotone skill under added data holds at 46/47 cities. One city
    breaks it and the violation has never been explained. An unexplained exception to a claimed
    property invites doubt about the other 46.

(2) Bud0 learner sensitivity. The entire budget ladder rests on one HistGradientBoostingRegressor
    with one hyperparameter setting. If the step gains move when the estimator changes, the
    ladder is a property of that learner rather than of the information.

(3) The P1 drift is handled separately (needs the decomp products, not the panel).

Usage:  python scripts/tier2_robustness.py
Out:    data/processed/modular/tier2_robustness.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "tier2_robustness.csv"


def p2_violation() -> None:
    print("=" * 78)
    print("(1) P2 -- the single monotonicity violation")
    print("=" * 78)
    L = pd.read_csv(MOD / "ladder_all.csv")
    r = ["rmse_Bud0", "rmse_Bud1", "rmse_Bud2", "rmse_Bud3"]
    mono = ((L.rmse_Bud1 <= L.rmse_Bud0 + 1e-9) & (L.rmse_Bud2 <= L.rmse_Bud1 + 1e-9)
            & (L.rmse_Bud3.fillna(np.inf) <= L.rmse_Bud2 + 1e-9))
    bad = L[~mono]
    print(f"  monotone: {int(mono.sum())}/{len(L)}   violations: {list(bad.city.astype(str))}")
    for x in bad.itertuples():
        print(f"\n  city {x.city}  band={x.band}  src={x.src}  n_held={x.n_held}  n_days={x.n_days}")
        vals = [getattr(x, c) for c in r]
        print("    RMSE  " + "  ".join(f"{c.replace('rmse_','')}={v:.3f}" if pd.notna(v) else
                                       f"{c.replace('rmse_','')}=NaN" for c, v in zip(r, vals)))
        print("    w     " + "  ".join(f"{k}={getattr(x, 'w_'+k):.3f}"
                                       if pd.notna(getattr(x, "w_" + k)) else f"{k}=NaN"
                                       for k in ("Bud1", "Bud2", "Bud3")))
        for a, b in zip(r[:-1], r[1:]):
            va, vb = getattr(x, a), getattr(x, b)
            if pd.notna(va) and pd.notna(vb) and vb > va + 1e-9:
                print(f"    >>> BREAKS at {a.replace('rmse_','')} -> {b.replace('rmse_','')}: "
                      f"{va:.3f} -> {vb:.3f}  (+{100*(vb-va)/va:.2f}%)")
    # context: how large is the violation relative to the spread of the panel?
    if len(bad):
        d = []
        for x in bad.itertuples():
            for a, b in zip(r[:-1], r[1:]):
                va, vb = getattr(x, a), getattr(x, b)
                if pd.notna(va) and pd.notna(vb) and vb > va:
                    d.append(100 * (vb - va) / va)
        if d:
            print(f"\n  violation magnitude: {max(d):.2f}% of RMSE")
            print(f"  for scale, the median Bud2->Bud3 GAIN across the panel is "
                  f"{100*((L.rmse_Bud2-L.rmse_Bud3)/L.rmse_Bud2).median():.1f}%")
        else:
            print("\n  >>> NO RUNG ACTUALLY REGRESSES.")
            print("      The flag is an artefact of filling a MISSING Bud3 with +inf.")
            print("      P2 is NOT violated at this city -- every rung it has improves.")
            ok = L.rmse_Bud3.notna()
            m = ((L.rmse_Bud1 <= L.rmse_Bud0 + 1e-9) & (L.rmse_Bud2 <= L.rmse_Bud1 + 1e-9)
                 & ((L.rmse_Bud3 <= L.rmse_Bud2 + 1e-9) | ~ok))
            print(f"      CORRECTED P2: {int(m.sum())}/{len(L)} monotone on every rung that exists")


def bud0_sensitivity() -> None:
    print("\n" + "=" * 78)
    print("(2) Bud0 learner sensitivity -- does the ladder depend on the estimator?")
    print("=" * 78)
    from modular_validation_all import FEATS, build_frame, ladder, stations_openaq, stations_cnemc
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    sample = pd.read_csv(MOD / "validation_sample.csv")
    manifest = pd.read_csv(MOD / "openaq_manifest.csv")
    st, pool = build_frame(sample, manifest)
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    feats = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=feats + ["pm25_city"])
    print(f"  pool {len(pool)} city-days, {pool.city.nunique()} cities\n")

    makers = {
        "HistGBM (shipped)": lambda s: HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.06, random_state=s),
        "HistGBM shallow":   lambda s: HistGradientBoostingRegressor(
            max_iter=100, learning_rate=0.15, max_depth=3, random_state=s),
        "RandomForest":      lambda s: RandomForestRegressor(
            n_estimators=200, min_samples_leaf=5, random_state=s, n_jobs=-1),
        "Ridge (linear)":    lambda s: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    }

    rows = []
    for name, mk in makers.items():
        out = []
        for city in sorted(pool.city.unique()):
            tr, te = pool[pool.city != city], pool[pool.city == city]
            if len(tr) < 1000 or len(te) < 100:
                continue
            m = mk(0)
            m.fit(tr[feats], tr.pm25_city)
            out.append(pd.DataFrame({"city": city, "date": te.date.values,
                                     "bud0": m.predict(te[feats])}))
        b0 = pd.concat(out, ignore_index=True)

        L = []
        for city, s in st.items():
            if city not in set(b0.city):
                continue
            try:
                L.append(ladder(city, s, b0[b0.city == city], 0))
            except Exception:
                continue
        L = pd.DataFrame([x for x in L if x is not None])
        if L.empty or "rmse_Bud0" not in L.columns:
            print(f"  {name:<20} ladder failed"); continue
        g1 = 100 * ((L.rmse_Bud0 - L.rmse_Bud1) / L.rmse_Bud0).median()
        g2 = 100 * ((L.rmse_Bud1 - L.rmse_Bud2) / L.rmse_Bud1).median()
        g3 = 100 * ((L.rmse_Bud2 - L.rmse_Bud3) / L.rmse_Bud2).median()
        mono = ((L.rmse_Bud1 <= L.rmse_Bud0 + 1e-9) & (L.rmse_Bud2 <= L.rmse_Bud1 + 1e-9)
                & (L.rmse_Bud3.fillna(np.inf) <= L.rmse_Bud2 + 1e-9)).mean()
        print(f"  {name:<20} n={len(L):>3}  Bud0 median RMSE {L.rmse_Bud0.median():6.2f}   "
              f"gains  0->1 {g1:5.1f}%   1->2 {g2:5.1f}%   2->3 {g3:5.1f}%   monotone {100*mono:.0f}%")
        rows.append(dict(learner=name, n_cities=len(L), bud0_rmse=L.rmse_Bud0.median(),
                         gain_0_1=g1, gain_1_2=g2, gain_2_3=g3, monotone_pct=100 * mono))

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    if len(df) > 1:
        print("\n  SPREAD ACROSS LEARNERS")
        for c, lab in [("gain_0_1", "Bud0->Bud1"), ("gain_1_2", "Bud1->Bud2"),
                       ("gain_2_3", "Bud2->Bud3")]:
            v = df[c]
            print(f"    {lab:<12} {v.min():5.1f}% to {v.max():5.1f}%   spread {v.max()-v.min():4.1f} pp")
    print(f"\n  wrote {OUT}")


if __name__ == "__main__":
    p2_violation()
    bud0_sensitivity()
