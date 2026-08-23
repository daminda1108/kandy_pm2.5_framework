"""learner_sensitivity_bud0c.py -- re-run F.81 against the spec-compliant Bud0c.

F.81 showed the budget ladder does not depend on the estimator: four learners spanning boosting,
bagging and plain linear regression gave step gains within a couple of percentage points, and
Ridge reproduced the gradient-boosting result. That is a strong claim -- it makes the ladder a
property of the INFORMATION rather than of model capacity.

But it was measured on the pre-F.84 `Bud0`, which used one of the three streams its budget
admits. The conclusion must be re-tested rather than assumed to carry over: a richer feature set
(68 features rather than 7) is exactly the setting where a linear model might stop keeping up.

Usage:  python scripts/learner_sensitivity_bud0c.py
Out:    data/processed/modular/learner_sensitivity_bud0c.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "learner_sensitivity_bud0c.csv"

from modular_validation_all import FEATS, build_frame, ladder  # noqa: E402

SEED = 20260823


def main() -> None:
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
    met = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=met + ["pm25_city"])
    pool["city"] = pool.city.astype(str)

    geo = pd.read_csv(MOD / "bud0_static_geo.csv"); geo["city"] = geo.city.astype(str)
    sat = pd.read_csv(MOD / "bud0_satellite_level.csv"); sat["city"] = sat.city.astype(str)
    geo_f = [c for c in geo.columns if c not in ("city", "geo_n_stations")]
    p = pool.merge(geo, on="city", how="left").merge(sat, on="city", how="left")
    p = p.dropna(subset=geo_f + ["sat_level"])
    feats = met + geo_f + ["sat_level"]
    print(f"Bud0c pool: {len(p)} city-days, {p.city.nunique()} cities, {len(feats)} features\n")

    makers = {
        "HistGBM (shipped)": lambda: HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.06, random_state=SEED),
        "HistGBM shallow": lambda: HistGradientBoostingRegressor(
            max_iter=100, learning_rate=0.15, max_depth=3, random_state=SEED),
        # n_jobs=-1 with 68 features x 46 LOCO fits was killed for memory; capped deliberately
        "RandomForest": lambda: RandomForestRegressor(
            n_estimators=100, min_samples_leaf=10, max_depth=14,
            random_state=SEED, n_jobs=2),
        "Ridge (linear)": lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    }

    rows = []
    for name, mk in makers.items():
        out = []
        for city in sorted(p.city.unique()):
            tr, te = p[p.city != city], p[p.city == city]
            if len(tr) < 1000 or len(te) < 100:
                continue
            m = mk(); m.fit(tr[feats], tr.pm25_city)
            out.append(pd.DataFrame({"city": city, "date": te.date.values,
                                     "bud0": m.predict(te[feats])}))
        b0 = pd.concat(out, ignore_index=True)
        L = []
        for city, s in st.items():
            city = str(city)
            if city not in set(b0.city):
                continue
            try:
                r = ladder(city, s, b0[b0.city == city], SEED)
            except Exception:
                r = None
            if r:
                L.append(r)
        L = pd.DataFrame(L)
        if L.empty:
            print(f"  {name:<20} ladder failed"); continue
        g1 = 100 * ((L.rmse_Bud0 - L.rmse_Bud1) / L.rmse_Bud0).median()
        g2 = 100 * ((L.rmse_Bud1 - L.rmse_Bud2) / L.rmse_Bud1).median()
        g3 = 100 * ((L.rmse_Bud2 - L.rmse_Bud3) / L.rmse_Bud2).median()
        ok = L.rmse_Bud3.notna()
        mono = (((L.rmse_Bud1 <= L.rmse_Bud0 + 1e-9) & (L.rmse_Bud2 <= L.rmse_Bud1 + 1e-9)
                 & ((L.rmse_Bud3 <= L.rmse_Bud2 + 1e-9) | ~ok))).mean()
        print(f"  {name:<20} n={len(L):>3}  Bud0c RMSE {L.rmse_Bud0.median():6.2f}   "
              f"gains 0c->1 {g1:5.1f}%  1->2 {g2:4.1f}%  2->3 {g3:5.1f}%   monotone {100*mono:.0f}%")
        rows.append(dict(learner=name, n_cities=len(L), bud0c_rmse=L.rmse_Bud0.median(),
                         gain_0c_1=g1, gain_1_2=g2, gain_2_3=g3, monotone_pct=100 * mono))

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print("\n=== SPREAD ACROSS LEARNERS (Bud0c) ===")
    for c, lab in [("bud0c_rmse", "Bud0c RMSE"), ("gain_0c_1", "Bud0c->Bud1"),
                   ("gain_1_2", "Bud1->Bud2"), ("gain_2_3", "Bud2->Bud3")]:
        v = df[c]
        unit = "" if c == "bud0c_rmse" else " pp"
        print(f"  {lab:<13} {v.min():6.2f} to {v.max():6.2f}   spread {v.max()-v.min():5.2f}{unit}")
    print(f"\n  F.81 on the OLD Bud0 gave spreads of 1.8 / 0.1 / 3.3 pp.")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
