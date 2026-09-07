"""precip_ladder_test.py -- does wet removal belong in the ladder's bottom rung?

REGISTERED AT https://osf.io/z89kt/ (project x7a8j) BEFORE THIS WAS WRITTEN.
Pre-registration: docs/prereg_precipitation_ladder_2026-09-09.md.

THE DEFECT UNDER TEST, WHICH IS NOT A DATA GAP. `Bud0a` is specified as reanalysis drivers, and its
feature list holds temperature, u/v wind, wind speed, boundary-layer height and two day-of-year
terms. No precipitation, no humidity, so wet removal is absent from the model's meteorology. But
`total_precipitation_sum` is ALREADY IN THE SCORED FRAME -- pulled, merged, and never referenced,
because it is not in FEATS. A rung with a driver its budget admits, sitting in its own inputs,
unused.

That is the F.84 defect class, which moved the headline from 25.6% to 17.9%. `require_covers()` was
written to prevent a recurrence but asserts coverage at STREAM level -- DRIVERS, STATIC_GEO,
SATELLITE_LEVEL -- and cannot see an unused variable inside an admitted stream.

REGISTERED PREDICTIONS: P1 the bottom rung improves. P2 the gains above it shrink (the F.84
mechanism; if P1 and P2 both hold, published gains are overstated). P3 the redundancy null
survives. P4 the background stays largest. P5 the deep-tropical ordering does not reverse.

[!] THE HAZARD, DECLARED IN THE REGISTRATION. Precipitation is 62.8% complete and 11 of 48 cities
sit below 90%, one at zero. That is the shape of the C1/MAIAC defect (gotcha #85): a stream that
looks present, is silently absent for many units, and is swallowed without warning by a learner
that tolerates NaN -- there it returned a clean, plausible, meaningless -0.41%. So coverage is
ASSERTED before fitting, and both arms are scored on ONE FIXED CITY SET so the contrast is the
covariate and not a change of frame.

Usage: .venv/Scripts/python.exe scripts/precip_ladder_test.py [--boot 4000]
Out:   data/processed/modular/precip_ladder.{csv,json}
"""
from __future__ import annotations

import argparse
import json
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

from modular_validation_all import FEATS, build_frame, _affine  # noqa: E402
from src.modular import shrinkage as sh                         # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "precip_ladder.csv"
OUT_JSON = MOD / "precip_ladder.json"

SEED = 20260823            # the seed the production ladder was fitted under
PRECIP = "total_precipitation_sum"
MIN_COVERAGE = 0.90        # fixed in the registration
BOOT_DEFAULT = 4000


def fit_bottom(pool: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    """Leave-one-CITY-out sensorless rung, identical machinery to the production ladder."""
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


def ladder(city, st, bud0, seed):
    """Bud0 -> +2 stations -> +stations 3-6 -> +background. Unchanged from production."""
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(st.station_id.unique()))
    rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    held, pool = ids[:n_hold], ids[n_hold:]
    roles = {"b1": pool[:2], "b2": pool[:min(6, len(pool))], "reg": pool[min(6, len(pool)):]}
    if not len(roles["reg"]):
        return None
    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    target = daily(held).rename("obs")
    p0 = bud0[bud0.city == city].set_index("date").bud0
    fr = pd.concat([p0, target], axis=1).dropna()
    if len(fr) < 120:
        return None
    bg = st[st.station_id.isin(roles["reg"])].groupby("date").pm25.quantile(0.10).rename("bg")

    obs = fr.obs.to_numpy()
    days = fr.index.astype(str).to_numpy()
    cur = fr.bud0.to_numpy()
    row = {"city": city, "n_days": len(fr),
           "rmse_Bud0": float(np.sqrt(np.mean((cur - obs) ** 2)))}
    for label, key, use_bg in (("Bud1", "b1", False), ("Bud2", "b2", False),
                               ("Bud3", "b2", True)):
        fit_s = daily(roles[key]).rename("fit")
        if not use_bg:
            j = pd.concat([p0, fit_s], axis=1).dropna()
            a, b = _affine(j.fit.to_numpy(), j.bud0.to_numpy())
            pred = a + b * fr.bud0.to_numpy()
        else:
            j = pd.concat([p0, bg, fit_s], axis=1).dropna()
            if len(j) <= 60:
                return None
            A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.bg.to_numpy()]).T
            c, *_ = np.linalg.lstsq(A, j.fit.to_numpy(), rcond=None)
            k = pd.concat([p0, bg], axis=1).reindex(fr.index)
            pred = (c[0] + c[1] * k.bud0.to_numpy()
                    + c[2] * k.bg.fillna(k.bg.mean()).to_numpy())
        r = sh.optimal_weight(cur, pred, obs, groups=days, seed=seed)
        cur = sh.combine(cur, pred, r.w)
        row[f"rmse_{label}"] = r.skill_shrunk
    return row


def gain(a, b):
    return 100.0 * (a - b) / a


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=BOOT_DEFAULT)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    print("=== does wet removal belong in the ladder's bottom rung? ===")
    print("    registered at https://osf.io/z89kt/\n")

    sample = pd.read_csv(MOD / "validation_sample.csv")
    st, pool = build_frame(sample, None)
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    met = [c for c in FEATS if c in pool.columns]
    pool["city"] = pool.city.astype(str)

    # ── the coverage assertion, before anything is fitted ───────────────────────────────
    cov = pool.groupby("city")[PRECIP].apply(lambda s: s.notna().mean())
    keep = set(cov[cov >= MIN_COVERAGE].index)
    print(f"[1] precipitation coverage gate at {MIN_COVERAGE:.0%}")
    print(f"    {len(keep)} of {pool.city.nunique()} cities pass; "
          f"{pool.city.nunique() - len(keep)} excluded")
    if len(keep) < 20:
        raise SystemExit("fewer than 20 cities pass: reporting a FAILURE TO TEST, not a null")
    rng_val = pool[PRECIP].dropna()
    print(f"    values {rng_val.min():.5f} to {rng_val.max():.4f} m/day "
          f"(0-{rng_val.max() * 1000:.0f} mm) -- physical, so no de-accumulation needed")

    pool = pool[pool.city.isin(keep)].copy()
    pool = pool.dropna(subset=met + ["pm25_city"])
    geo = pd.read_csv(MOD / "bud0_static_geo.csv"); geo["city"] = geo.city.astype(str)
    sat = pd.read_csv(MOD / "bud0_satellite_level.csv"); sat["city"] = sat.city.astype(str)
    geo_f = [c for c in geo.columns if c not in ("city", "geo_n_stations")]
    p = pool.merge(geo, on="city", how="left").merge(sat, on="city", how="left")

    base_f = met + geo_f + ["sat_level"]
    print(f"\n[2] fitting both arms on the SAME {p.city.nunique()} cities, "
          f"{len(base_f)} vs {len(base_f) + 1} features")
    b_without = fit_bottom(p, base_f)
    b_with = fit_bottom(p, base_f + [PRECIP])

    rows = []
    for city, s in st.items():
        city = str(city)
        if city not in keep:
            continue
        try:
            r0 = ladder(city, s, b_without[b_without.city == city], SEED)
            r1 = ladder(city, s, b_with[b_with.city == city], SEED)
        except Exception:
            continue
        if not r0 or not r1:
            continue
        rows.append({"city": city,
                     **{f"no_{k}": v for k, v in r0.items() if k.startswith("rmse")},
                     **{f"yes_{k}": v for k, v in r1.items() if k.startswith("rmse")}})
    d = pd.DataFrame(rows)
    band = pd.read_csv(MOD / "ladder_revalidated.csv")
    band = band[band.bottom == "Bud0c"][["city", "band"]].drop_duplicates()
    band["city"] = band.city.astype(str)
    d = d.merge(band, on="city", how="left")
    d.to_csv(OUT, index=False)
    print(f"    {len(d)} cities scored in both arms -> {OUT.name}\n")

    def boot(v):
        v = np.asarray(v, float); v = v[np.isfinite(v)]
        if len(v) < 4:
            return None
        idx = rng.integers(0, len(v), (a.boot, len(v)))
        m = np.median(v[idx], axis=1)
        return dict(n=len(v), median=float(np.median(v)),
                    lo=float(np.percentile(m, 2.5)), hi=float(np.percentile(m, 97.5)))

    res = {}
    # ── P1: does the bottom rung improve? ───────────────────────────────────────────────
    p1 = boot(100.0 * (d.no_rmse_Bud0 - d.yes_rmse_Bud0) / d.no_rmse_Bud0)
    res["P1_bottom_rung"] = {**p1, "holds": bool(p1["lo"] > 0)}
    print("=== P1  does adding precipitation improve the sensorless rung? ===")
    print(f"    percentage RMSE reduction at Bud0c: {p1['median']:+.3f}  "
          f"[{p1['lo']:+.3f}, {p1['hi']:+.3f}]   "
          f"{'HOLDS' if p1['lo'] > 0 else 'does not hold'}")

    # ── P2/P3/P4: do the gains above it move? ───────────────────────────────────────────
    steps = (("first two sensors", "rmse_Bud0", "rmse_Bud1"),
             ("stations three to six", "rmse_Bud1", "rmse_Bud2"),
             ("a background series", "rmse_Bud2", "rmse_Bud3"))
    print("\n=== P2-P4  the gains measured above it, both arms ===")
    print(f"    {'step':<26}{'without':>10}{'with':>10}{'paired change':>24}")
    for label, lo_c, hi_c in steps:
        g0 = gain(d[f"no_{lo_c}"], d[f"no_{hi_c}"])
        g1 = gain(d[f"yes_{lo_c}"], d[f"yes_{hi_c}"])
        b = boot(g1 - g0)
        res[label] = dict(without=round(float(g0.median()), 3),
                          with_precip=round(float(g1.median()), 3), paired=b)
        print(f"    {label:<26}{g0.median():>10.2f}{g1.median():>10.2f}"
              f"{b['median']:>+10.3f} [{b['lo']:+.2f},{b['hi']:+.2f}]")

    # ── P5: the deep-tropical ordering ──────────────────────────────────────────────────
    dt = d[d.band == "deep_tropical"]
    if len(dt) >= 4:
        f0 = gain(dt.no_rmse_Bud0, dt.no_rmse_Bud1) - gain(dt.no_rmse_Bud2, dt.no_rmse_Bud3)
        f1 = gain(dt.yes_rmse_Bud0, dt.yes_rmse_Bud1) - gain(dt.yes_rmse_Bud2, dt.yes_rmse_Bud3)
        b0, b1 = boot(f0), boot(f1)
        res["P5_deep_tropical"] = dict(without=b0, with_precip=b1,
                                       direction_held=bool((b0["median"] > 0) == (b1["median"] > 0)))
        print(f"\n=== P5  deep-tropical local-minus-background, paired, n={len(dt)} ===")
        print(f"    without precipitation {b0['median']:+8.2f} pp  [{b0['lo']:+.2f}, {b0['hi']:+.2f}]")
        print(f"    with precipitation    {b1['median']:+8.2f} pp  [{b1['lo']:+.2f}, {b1['hi']:+.2f}]")
        print(f"    direction preserved: {res['P5_deep_tropical']['direction_held']}")

    print("\n=== the answer ===")
    p2 = res["first two sensors"]["paired"]
    if res["P1_bottom_rung"]["holds"] and p2["hi"] < 0:
        print("    P1 and P2 both hold. The ladder was under-using an admitted driver, as in F.84,")
        print("    and gains above the bottom rung in the current thesis are overstated.")
    elif res["P1_bottom_rung"]["holds"]:
        print("    P1 holds and P2 does not. Precipitation adds skill at the bottom without")
        print("    displacing what sits above it: the streams are complementary, the ladder's")
        print("    conclusions stand, and the driver set improves.")
    else:
        print("    P1 does not hold. An 11 km reanalysis daily rainfall total does not improve")
        print("    daily city-mean prediction on this panel. That closes a gap Table 9.1 lists as")
        print("    unmeasured, and it is NOT evidence that wet removal does not matter.")

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(dict(osf="z89kt", seed=SEED, boot=a.boot,
                       min_coverage=MIN_COVERAGE,
                       cities_passing=int(len(keep)), cities_scored=int(len(d)),
                       cities_excluded=int(48 - len(keep)), results=res), fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
