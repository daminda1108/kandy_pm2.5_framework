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

from modular_validation_all import ladder  # noqa: E402

SEED = 20260823


def main() -> None:
    import argparse
    import json
    import os
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from ladder_frames import build_bud0_frame
    from ladder_honesty_checks import effects
    sys.path.insert(0, str(REPO))
    from src.modular.city_meta import city_meta
    from src.modular.runlog import DropLog

    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", choices=("maiac", "ghap"), default="maiac")
    a = ap.parse_args()
    tag = "" if a.stream == "maiac" else "_ghap"

    # 2026-09-25: the ONE shared frame builder. The old code dropped every row with ANY missing
    # geography value (removing the censored city 2168 as well as 3147) and could not run on
    # MAIAC, whose daily retrievals are missing on about half the days.
    st, p, met, geo_f, sat_feats = build_bud0_frame(a.stream)
    feats = met + geo_f + sat_feats
    band = city_meta(list(st)).set_index("city").band
    print(f"Bud0c pool: {len(p)} city-days, {p.city.nunique()} cities, {len(feats)} features\n")

    makers = {
        "HistGBM (shipped)": lambda: HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.06, random_state=SEED),
        "HistGBM shallow": lambda: HistGradientBoostingRegressor(
            max_iter=100, learning_rate=0.15, max_depth=3, random_state=SEED),
        # sklearn >= 1.4 random forests accept NaN natively; n_jobs capped for memory
        "RandomForest": lambda: RandomForestRegressor(
            n_estimators=100, min_samples_leaf=10, max_depth=14,
            random_state=SEED, n_jobs=2),
        # a linear model cannot take NaN: median imputation PLUS a missing-value indicator, so
        # "no retrieval today" is information the model can use rather than a silent fill
        "Ridge (linear)": lambda: make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
            Ridge(alpha=1.0)),
    }

    rows, summ = [], {"stream": a.stream}
    rng = np.random.default_rng(SEED)
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
        L, drops = [], DropLog(f"learner_{a.stream}_{name.split()[0]}")
        for city, s in st.items():
            city = str(city)
            if city not in set(b0.city):
                continue
            try:
                r = ladder(city, s, b0[b0.city == city], SEED)
            except Exception as e:
                drops.error(city, e)
                continue
            if r:
                L.append(r)
            else:
                drops.skip(city, "ladder() returned None")
        drops.report(MOD / "verify_2026-09-25" / f"droplog_learner_{a.stream}_{name.split()[0]}.json")
        L = pd.DataFrame(L)
        L["band"] = L.city.map(band)
        e = effects(L, 4000, rng)
        summ[name] = e
        g1, g2, g3 = (e["pooled.first2"]["median"], e["pooled.s36"]["median"],
                      e["pooled.bg"]["median"])
        ok = L.rmse_Bud3.notna()
        mono = (((L.rmse_Bud1 <= L.rmse_Bud0 + 1e-9) & (L.rmse_Bud2 <= L.rmse_Bud1 + 1e-9)
                 & ((L.rmse_Bud3 <= L.rmse_Bud2 + 1e-9) | ~ok))).mean()
        pb, dt = e["pooled.bg_minus_first2"], e["deep_tropical.bg_minus_first2"]
        print(f"  {name:<20} n={len(L):>3}  Bud0c RMSE {L.rmse_Bud0.median():6.2f}   "
              f"gains {g1:5.1f} / {g2:4.2f} / {g3:5.1f}   bg-first2 {pb['median']:+6.1f} "
              f"[{pb['lo']:+.1f},{pb['hi']:+.1f}]   DT {dt['median']:+6.1f} "
              f"[{dt['lo']:+.1f},{dt['hi']:+.1f}]   monotone {100*mono:.0f}%", flush=True)
        rows.append(dict(learner=name, n_cities=len(L), bud0c_rmse=L.rmse_Bud0.median(),
                         gain_0c_1=g1, gain_1_2=g2, gain_2_3=g3, monotone_pct=100 * mono,
                         bg_minus_first2=pb["median"], bg_minus_first2_lo=pb["lo"],
                         bg_minus_first2_hi=pb["hi"], dt_bg_minus_first2=dt["median"],
                         dt_lo=dt["lo"], dt_hi=dt["hi"]))

    df = pd.DataFrame(rows)
    out_csv = OUT.with_name(OUT.stem + tag + OUT.suffix)
    df.to_csv(out_csv, index=False)
    jp = out_csv.with_suffix(".json"); tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(summ, indent=2), encoding="utf-8"); os.replace(tmp, jp)
    print("\n=== SPREAD ACROSS LEARNERS (Bud0c) ===")
    for c, lab in [("bud0c_rmse", "Bud0c RMSE"), ("gain_0c_1", "Bud0c->Bud1"),
                   ("gain_1_2", "Bud1->Bud2"), ("gain_2_3", "Bud2->Bud3"),
                   ("dt_bg_minus_first2", "DT bg-first2")]:
        v = df[c]
        print(f"  {lab:<14} {v.min():7.2f} to {v.max():7.2f}   spread {v.max()-v.min():5.2f}")
    print(f"  wrote {out_csv}")


if __name__ == "__main__":
    main()
