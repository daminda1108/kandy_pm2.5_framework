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
import os
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

from modular_validation_all import _affine                        # noqa: E402
from ladder_frames import build_bud0_frame, fit_loco             # noqa: E402
from src.modular.schemas import PRECIP_RANGE, validate_ladder_frame  # noqa: E402
from src.modular.city_meta import attach_meta                   # noqa: E402
from src.modular.runlog import DropLog                          # noqa: E402
from src.modular import shrinkage as sh                         # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "precip_ladder.csv"
OUT_JSON = MOD / "precip_ladder.json"

SEED = 20260823            # the seed the production ladder was fitted under
PRECIP = "total_precipitation_sum"
MIN_COVERAGE = 0.90        # fixed in the registration
BOOT_DEFAULT = 4000


def fit_bottom(pool: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    """Leave-one-CITY-out sensorless rung; the one implementation is ladder_frames.fit_loco."""
    return fit_loco(pool, feats, seed=SEED)


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
    ap.add_argument("--stream", choices=("ghap", "maiac"), default="ghap",
                    help="GHAP is the REGISTERED primary (z89kt fixes the analysis as unchanged "
                         "from the production ladder of 2026-09-09, which ran on GHAP). MAIAC is "
                         "an exploratory robustness run, labelled as such (2026-09-25).")
    a = ap.parse_args()
    tag = "" if a.stream == "ghap" else "_maiac"
    out_csv = OUT.with_name(OUT.stem + tag + OUT.suffix)
    out_json = OUT_JSON.with_name(OUT_JSON.stem + tag + OUT_JSON.suffix)
    drops = DropLog(f"precip_{a.stream}")
    rng = np.random.default_rng(SEED)

    print("=== does wet removal belong in the ladder's bottom rung? ===")
    print("    registered at https://osf.io/z89kt/\n")

    # the one shared builder (2026-09-25); precipitation is a driver column in the frame
    st, p, met, geo_f, sat_feats = build_bud0_frame(a.stream)
    n_frame = p.city.nunique()

    # ── the coverage assertion, before anything is fitted ───────────────────────────────
    # Coverage is measured over the city-days the ladder uses (after the driver dropna).
    cov = p.groupby("city")[PRECIP].apply(lambda s: s.notna().mean())
    keep = set(cov[cov >= MIN_COVERAGE].index)
    print(f"[1] precipitation coverage gate at {MIN_COVERAGE:.0%}")
    print(f"    {len(keep)} of {n_frame} cities pass; {n_frame - len(keep)} excluded: "
          f"{sorted(set(cov.index) - keep)}")
    if len(keep) < 20:
        raise SystemExit("fewer than 20 cities pass: reporting a FAILURE TO TEST, not a null")
    rng_val = p[PRECIP].dropna()
    print(f"    values {rng_val.min():.5f} to {rng_val.max():.4f} m/day "
          f"(0-{rng_val.max() * 1000:.0f} mm) -- physical, so no de-accumulation needed")
    p = p[p.city.isin(keep)].copy()
    p = validate_ladder_frame(p, met=met, static=geo_f, daily={PRECIP: PRECIP_RANGE},
                              allow_null={"dist_major_km": "censored: no major road in query"})

    base_f = met + geo_f + sat_feats
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
        except Exception as e:
            drops.error(city, e)
            continue
        if not r0 or not r1:
            drops.skip(city, "ladder() returned None in an arm (no outer ring or too few days)")
            continue
        rows.append({"city": city,
                     **{f"no_{k}": v for k, v in r0.items() if k.startswith("rmse")},
                     **{f"yes_{k}": v for k, v in r1.items() if k.startswith("rmse")}})
    drops.report(MOD / "verify_2026-09-25" / f"droplog_precip_{a.stream}.json")
    d = attach_meta(pd.DataFrame(rows))        # band/class from the shared metadata, 2026-09-25
    d.to_csv(out_csv, index=False)
    print(f"    {len(d)} cities scored in both arms -> {out_csv.name}\n")

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

    # ── P3 and P4, computed in code (2026-09-25; before this the verdicts were typed) ────
    # P3: stations three to six stay bounded near zero -> the with-precipitation arm's paired
    #     interval for that step's gain contains zero.
    g36 = gain(d.yes_rmse_Bud1, d.yes_rmse_Bud2)
    b36 = boot(g36)
    # The registration says "bounded near zero" and gives NO number. A prediction without a
    # registered bound cannot be adjudicated after seeing the data, so no threshold is invented
    # here: the verdict is "not adjudicable" and the numbers are reported, together with the strict
    # reading (does the interval contain zero?) and the scale (share of the first-two gain).
    g12 = gain(d.yes_rmse_Bud0, d.yes_rmse_Bud1).median()
    res["P3_redundancy"] = {**b36, "holds": None, "verdict": "not adjudicable: no bound registered",
                            "strict_interval_contains_zero": bool(b36["lo"] <= 0 <= b36["hi"]),
                            "share_of_first2_gain_pct": round(100 * b36["median"] / g12, 1)}
    # P4: the background is the largest single gain. The registered estimand is PAIRED within
    #     city, so it is the background gain minus the first-two gain, per city, bootstrapped.
    for arm, pre in (("without", "no_"), ("with_precip", "yes_")):
        v = (gain(d[pre + "rmse_Bud2"], d[pre + "rmse_Bud3"])
             - gain(d[pre + "rmse_Bud0"], d[pre + "rmse_Bud1"]))
        bb = boot(v)
        res.setdefault("P4_background_largest", {})[arm] = {
            **bb, "cities_bg_larger": int((v > 0).sum()), "holds": bool(bb["lo"] > 0)}
    p4 = res["P4_background_largest"]["with_precip"]
    print(f"\n=== P3  stations 3-6 with precipitation: {b36['median']:+.2f} "
          f"[{b36['lo']:+.2f}, {b36['hi']:+.2f}] "
          f"({res['P3_redundancy']['share_of_first2_gain_pct']:.1f} % of the first-two gain; "
          f"interval contains 0: {res['P3_redundancy']['strict_interval_contains_zero']}) -> "
          f"NOT ADJUDICABLE (no bound registered)")
    print(f"=== P4  background minus first two, PAIRED, with precipitation: {p4['median']:+.2f} "
          f"[{p4['lo']:+.2f}, {p4['hi']:+.2f}], background larger in {p4['cities_bg_larger']}/"
          f"{p4['n']} -> {'HOLDS' if p4['holds'] else 'NOT SUPPORTED'}")

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

    tmp = out_json.with_suffix(".json.tmp")               # gotcha #81
    tmp.write_text(json.dumps(dict(
        osf="z89kt", stream=a.stream,
        status="registered primary" if a.stream == "ghap" else "exploratory robustness",
        seed=SEED, boot=a.boot, min_coverage=MIN_COVERAGE,
        cities_in_frame=int(n_frame), cities_passing=int(len(keep)),
        cities_scored=int(len(d)), cities_excluded=int(n_frame - len(keep)),
        results=res), indent=2), encoding="utf-8")
    os.replace(tmp, out_json)
    print(f"\n-> {out_csv.name}, {out_json.name}")


if __name__ == "__main__":
    main()
