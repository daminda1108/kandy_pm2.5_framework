"""station_count_curve.py -- is TWO sensors the right number, or just Kandy's number?

THE QUESTION, AND WHY IT IS A FAIR ONE. The ladder's first ground rung adds exactly two
stations, and the budget spec says why in as many words: SENSOR_PAIR is defined as "<= 2 local
low-cost sensors (the Kandy budget)" and Bud1's own note reads "two elevation-gradient sensors.
The deployed Kandy budget." So the rung was sized to match the demonstration city.

That is a defensible design choice, because the point of the ladder is to price the tier Kandy
actually occupies. But it means the headline "the first two sensors buy 17.8 per cent" has never
been checked against the alternative counts, and two quite different worlds produce it:

  (a) SATURATION AT ONE. A single station buys most of the 17.8 per cent and the second adds
      little. Then the emphasis on "two" is misleading and the finding is about the FIRST
      station.
  (b) A REAL STEP AT TWO. One station buys much less than two. Then two is meaningful, and the
      reason would be worth stating, since a pair spans a gradient where a single point cannot.

Nothing in the project distinguishes these. This sweeps the count from 1 to 8 on the same frame,
the same sensorless rung and the same seed, so only the number of stations varies.

⚠ A SECOND THING THIS CHECKS, found while reading the code. `ladder()` sets
`b2 = pool[:min(6, len(pool))]`, so the second ground rung uses SIX stations and the step from
Bud1 adds stations three through SIX. The thesis describes that step as "monitors three to
eight" in several places. The curve below reports the true counts, so the prose can be corrected
against it.

Usage: python scripts/station_count_curve.py [--max-k 8]
Out:   data/processed/modular/station_count_curve.csv
       data/processed/modular/station_count_curve.json
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
from src.modular import shrinkage as sh                          # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "station_count_curve.csv"
OUT_JSON = MOD / "station_count_curve.json"
SEED = 20260823          # the seed ladder_revalidated.csv was fitted under


def fit_bud0c(pool: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
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


def curve_for_city(city, st, b0c, seed, max_k):
    """RMSE against held-out stations as the fitting set grows one station at a time.

    Identical to ladder(): same shuffle, same held-out third, same affine rescaling of the
    sensorless prediction, same shrinkage toward the tier below. Only k varies.
    """
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(st.station_id.unique()))
    rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    held, pool = ids[:n_hold], ids[n_hold:]
    if len(pool) < 1:
        return None

    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    target = daily(held).rename("obs")
    p0 = b0c.set_index("date").bud0
    fr = pd.concat([p0, target], axis=1).dropna()
    if len(fr) < 120:
        return None

    obs = fr.obs.to_numpy()
    days = fr.index.astype(str).to_numpy()
    base = fr.bud0.to_numpy()
    rows = [dict(city=city, k=0, n_pool=len(pool), n_held=len(held),
                 rmse=float(np.sqrt(np.mean((base - obs) ** 2))))]

    cur = base
    for k in range(1, min(max_k, len(pool)) + 1):
        j = pd.concat([p0, daily(pool[:k]).rename("fit")], axis=1).dropna()
        if len(j) < 30:
            continue
        a, b = _affine(j.fit.to_numpy(), j.bud0.to_numpy())
        pred = a + b * base
        # shrink toward the SENSORLESS rung each time, so every k is scored against the same
        # parent. Chaining k-1 -> k would make the curve path-dependent and not comparable.
        r = sh.optimal_weight(base, pred, obs, groups=days, seed=seed)
        rows.append(dict(city=city, k=k, n_pool=len(pool), n_held=len(held),
                         rmse=float(r.skill_shrunk)))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-k", type=int, default=8)
    a = ap.parse_args()

    print("=== is two the right number of sensors, or just Kandy's number? ===\n")
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
    b0 = fit_bud0c(p, met + geo_f + ["sat_level"])
    print(f"    {b0.city.nunique()} cities on the corrected Bud0c rung")

    rows = []
    for city, s in st.items():
        city = str(city)
        if city not in set(b0.city):
            continue
        try:
            r = curve_for_city(city, s, b0[b0.city == city], SEED, a.max_k)
        except Exception:
            r = None
        if r:
            rows += r
    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)

    base = d[d.k == 0].set_index("city").rmse
    d["gain"] = 100 * (d.city.map(base) - d.rmse) / d.city.map(base)

    print(f"\n=== cumulative gain over the sensorless rung, by station count ===")
    print(f"    {'k':>3}{'cities':>8}{'median gain':>13}{'step from k-1':>15}")
    g = d[d.k > 0].groupby("k").gain.median()
    n = d[d.k > 0].groupby("k").city.nunique()
    prev = 0.0
    steps = {}
    for k in sorted(g.index):
        step = g[k] - prev
        steps[int(k)] = float(step)
        print(f"    {k:>3}{n[k]:>8}{g[k]:>12.2f}%{step:>+14.2f}%")
        prev = g[k]

    one, two = float(g.get(1, np.nan)), float(g.get(2, np.nan))
    print(f"\n=== the question ===")
    print(f"    one station  : {one:.2f}%")
    print(f"    two stations : {two:.2f}%")
    print(f"    the second station adds {two - one:+.2f} percentage points, "
          f"{100 * (two - one) / two:.0f}% of the two-station total")
    if two > 0 and (two - one) / two < 0.15:
        print("    -> SATURATION AT ONE. The headline belongs to the FIRST station, and")
        print("       'the first two sensors' overstates what the pair contributes.")
    else:
        print("    -> the second station earns its place; two is not an arbitrary cut.")

    print(f"\n=== what the second ground rung actually adds ===")
    six = float(g.get(6, np.nan))
    eight = float(g.get(8, np.nan))
    print(f"    stations 3 to 6  (what the code does) : {six - two:+.2f} percentage points")
    if np.isfinite(eight):
        print(f"    stations 3 to 8  (what the prose says): {eight - two:+.2f} percentage points")
        print(f"    -> the prose describes a rung two stations wider than the one that was run")

    # ── BY BAND, because the pooled answer could hide a band where two stations do pay ──────
    #
    # ⚠ THE TRAP THIS SECTION EXISTS TO AVOID. A difference of medians is NOT the median
    # difference, and here they disagree violently: in the temperate band the median gain rises
    # 20.6 -> 33.5 with a second station, which looks like a large effect and is not one. It is
    # produced by ONE city moving 0.0 -> 33.5 while another falls 17.0 -> 0.1, so the city
    # sitting at the median changes. Paired within city the median gain is +0.14. The project's
    # standing rule, median of ratios and never a ratio of medians, is what catches this.
    L = pd.read_csv(MOD / "ladder_revalidated.csv", dtype={"city": str})
    bands = L[L.bottom == "Bud0c"][["city", "band"]].drop_duplicates()
    db = d.merge(bands, on="city", how="left")
    w = db[db.k > 0].pivot_table(index=["band", "city"], columns="k", values="gain")
    rng = np.random.default_rng(0)
    by_band = {}
    print("\n=== does a SECOND station beat one, WITHIN band? paired, 2000 bootstrap ===")
    print(f"    {'band':<15}{'n':>4}{'k=1':>9}{'2nd adds':>11}{'95% interval':>20}  improving")
    for band, sub in w.groupby(level=0):
        s = sub[[1, 2]].dropna()
        if len(s) < 4:
            continue
        v = (s[2] - s[1]).to_numpy()
        idx = rng.integers(0, len(v), (2000, len(v)))
        m = np.median(v[idx], axis=1)
        lo, hi = np.percentile(m, [2.5, 97.5])
        imp = int((v > 0.5).sum())
        by_band[str(band)] = dict(
            n=int(len(v)), k1=round(float(s[1].median()), 2),
            second_adds=round(float(np.median(v)), 2),
            lo=round(float(lo), 2), hi=round(float(hi), 2),
            improving=imp, diff_of_medians=round(float(s[2].median() - s[1].median()), 2))
        print(f"    {band:<15}{len(v):>4}{s[1].median():>8.1f}%{np.median(v):>+10.2f}"
              f"   [{lo:>+6.2f},{hi:>+6.2f}]   {imp}/{len(v)}")
    dt = by_band.get("deep_tropical")
    if dt:
        print(f"\n    Kandy's band: a second station adds {dt['second_adds']:+.2f} points paired "
              f"[{dt['lo']:+.2f}, {dt['hi']:+.2f}], improving {dt['improving']} of {dt['n']}.")
        print(f"    The DIFFERENCE OF MEDIANS is {dt['diff_of_medians']:+.2f}, which is not the "
              f"effect and must not be quoted as one.")
    # ASCII only in printed output: the Windows console is cp1252 (gotcha from the species run).
    print("    No band shows a measurable second-station gain. [!] The temperate interval runs to "
          f"{by_band.get('temperate', {}).get('hi', float('nan')):+.2f} on n="
          f"{by_band.get('temperate', {}).get('n', 0)}, so that band is UNDERPOWERED rather "
          "than null.")

    # Pooled paired bootstrap, computed HERE rather than in a side script. An earlier version
    # patched these keys into the JSON afterwards, and the next run of this script silently
    # dropped them, which is gotcha #70: a correction written to a derived file is discarded by
    # whatever regenerates that file.
    wp = d[d.k > 0].pivot_table(index="city", columns="k", values="gain")
    s1 = wp[[1]].dropna()
    v1 = s1[1].to_numpy()
    i1 = rng.integers(0, len(v1), (2000, len(v1)))
    m1 = np.median(v1[i1], axis=1)
    paired = {}
    best_k, best_d = None, -9.0
    for k in sorted([c for c in wp.columns if c > 1]):
        sk = wp[[1, k]].dropna()
        if len(sk) < 5:
            continue
        vk = (sk[k] - sk[1]).to_numpy()
        ik = rng.integers(0, len(vk), (2000, len(vk)))
        mk = np.median(vk[ik], axis=1)
        paired[int(k)] = dict(median=round(float(np.median(vk)), 2),
                              lo=round(float(np.percentile(mk, 2.5)), 2),
                              hi=round(float(np.percentile(mk, 97.5)), 2), n=int(len(vk)))
        if np.median(vk) > best_d:
            best_k, best_d = int(k), float(np.median(vk))

    summary = dict(
        by_band=by_band,
        k1_gain=round(float(np.median(v1)), 2),
        k1_lo=round(float(np.percentile(m1, 2.5)), 2),
        k1_hi=round(float(np.percentile(m1, 97.5)), 2),
        k1_cities=int(len(v1)),
        paired_vs_one=paired,
        d2_median=paired.get(2, {}).get("median"),
        max_extra_over_one=round(best_d, 2), max_extra_at_k=best_k,
        bud2_stations_in_code=6, prose_said_stations=8,
        cities=int(d[d.k > 0].city.nunique()),
        gain_by_k={int(k): round(float(v), 3) for k, v in g.items()},
        step_by_k={int(k): round(v, 3) for k, v in steps.items()},
        n_by_k={int(k): int(v) for k, v in n.items()},
        one_station=round(one, 2), two_station=round(two, 2),
        second_station_adds=round(two - one, 2),
        second_station_share=round(100 * (two - one) / two, 1) if two else None,
        gain_3to6=round(six - two, 2) if np.isfinite(six) else None,
        gain_3to8=round(eight - two, 2) if np.isfinite(eight) else None,
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
