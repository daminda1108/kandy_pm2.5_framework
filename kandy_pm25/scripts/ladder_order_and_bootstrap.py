"""ladder_order_and_bootstrap.py -- is the ladder's answer a property of the information, or of
the ORDER the streams were added in, and how wide is it over CITIES rather than city-days?

TWO OBJECTIONS, BOTH RAISED BY AN EXTERNAL REVIEWER, BOTH ANSWERABLE WITHOUT NEW DATA.

(1) PATH DEPENDENCE. Every gain on the ladder is marginal at a position in a fixed order, so
    "two sensors are worth 17.8%" is really "worth 17.8% GIVEN drivers, geography and a
    satellite level, and BEFORE a background". Information interacts, so a stream that looks
    redundant late may have been valuable early. The estimand is a path-dependent marginal, and
    the question is whether the ORDERING of the conclusions survives reordering.

    One reordering is impossible by construction and that is itself worth reporting. The
    background enters as a second regressor whose coefficient is fitted against LOCAL station
    data, so a "background before any local station" rung has no target to fit and cannot be
    built. The background is only ever priceable given some local observation. What CAN be
    permuted is where the background sits relative to stations 3-8:

        A (production)   Bud0c -> +2 stn -> +6 stn -> +6 stn & bg
        B (bg early)     Bud0c -> +2 stn -> +2 stn & bg -> +6 stn & bg

    Both end at the same information set, so the endpoints are comparable and only the interior
    order differs. If the background is large in both positions and stations 3-8 are near zero
    in both, the two headline conclusions are order-robust.

(2) CITY-DAYS ARE NOT INDEPENDENT UNITS. 28,930 city-days across 48 cities is not n=28,930;
    days within a city are strongly correlated. The per-city median already avoids letting
    long records dominate, but the UNCERTAINTY on a rung should be expressed over cities. This
    bootstraps cities with replacement and reports percentile intervals, pooled and by band.

Usage: python scripts/ladder_order_and_bootstrap.py [--seed N] [--boot 2000]
Out:   data/processed/modular/ladder_order_variants.csv
       data/processed/modular/ladder_bootstrap.csv
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

from modular_validation_all import FEATS, build_frame, _affine  # noqa: E402
import modular_validation_all as mv                             # noqa: E402
from src.modular import shrinkage as sh                         # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT_ORDER = MOD / "ladder_order_variants.csv"
OUT_BOOT = MOD / "ladder_bootstrap.csv"
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


def ladder_ordered(city, st, bud0, seed, order):
    """Run the chain in a given ORDER. Each step is (label, station_key, use_bg).

    Identical machinery to modular_validation_all.ladder: an affine rescaling of the sensorless
    prediction fitted on the step's stations, plus the background as a second regressor when the
    step admits it, then the same cross-validated shrinkage toward the tier below.
    """
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

    pred = {}
    for label, key, use_bg in order:
        fit_s = daily(roles[key]).rename("fit")
        if not use_bg:
            j = pd.concat([p0, fit_s], axis=1).dropna()
            a, b = _affine(j.fit.to_numpy(), j.bud0.to_numpy())
            pred[label] = a + b * fr.bud0.to_numpy()
        else:
            j = pd.concat([p0, bg, fit_s], axis=1).dropna()
            if len(j) <= 60:
                return None
            A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.bg.to_numpy()]).T
            c, *_ = np.linalg.lstsq(A, j.fit.to_numpy(), rcond=None)
            k = pd.concat([p0, bg], axis=1).reindex(fr.index)
            pred[label] = (c[0] + c[1] * k.bud0.to_numpy()
                           + c[2] * k.bg.fillna(k.bg.mean()).to_numpy())

    obs = fr.obs.to_numpy()
    days = fr.index.astype(str).to_numpy()
    cur = fr.bud0.to_numpy()
    row = {"city": city, "n_days": len(fr),
           "rmse_Bud0": float(np.sqrt(np.mean((cur - obs) ** 2)))}
    for label, _, _ in order:
        r = sh.optimal_weight(cur, pred[label], obs, groups=days, seed=seed)
        cur = sh.combine(cur, pred[label], r.w)
        row[f"rmse_{label}"] = r.skill_shrunk
        row[f"w_{label}"] = r.w
    return row


# A: production.            B: the background moved one step earlier.
ORDER_A = [("s2", "b1", False), ("s8", "b2", False), ("s8bg", "b2", True)]
ORDER_B = [("s2", "b1", False), ("s2bg", "b1", True), ("s8bg", "b2", True)]


def gain(a: pd.Series, b: pd.Series) -> pd.Series:
    return 100.0 * (a - b) / a


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()

    print("=== ladder order sensitivity and city-level bootstrap ===\n")
    print("[1] frame and Bud0c")
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
    print(f"    {b0.city.nunique()} cities")

    print("\n[2] running both orderings")
    rows = []
    for city, s in st.items():
        city = str(city)
        if city not in set(b0.city):
            continue
        b0c = b0[b0.city == city]
        try:
            ra = ladder_ordered(city, s, b0c, a.seed, ORDER_A)
            rb = ladder_ordered(city, s, b0c, a.seed, ORDER_B)
        except Exception:
            continue
        if not ra or not rb:
            continue
        rows.append({"city": city, "n_days": ra["n_days"],
                     "rmse_Bud0": ra["rmse_Bud0"],
                     "A_s2": ra["rmse_s2"], "A_s8": ra["rmse_s8"], "A_s8bg": ra["rmse_s8bg"],
                     "B_s2": rb["rmse_s2"], "B_s2bg": rb["rmse_s2bg"],
                     "B_s8bg": rb["rmse_s8bg"]})
    d = pd.DataFrame(rows)
    band = pd.read_csv(MOD / "ladder_revalidated.csv")
    band = band[band.bottom == "Bud0c"][["city", "band"]].drop_duplicates()
    band["city"] = band.city.astype(str)
    d = d.merge(band, on="city", how="left")
    d.to_csv(OUT_ORDER, index=False)
    print(f"    {len(d)} cities scored in both orderings -> {OUT_ORDER.name}")

    # the two quantities whose ORDER-ROBUSTNESS is the question
    d["bg_after_8stn"] = gain(d.A_s8, d.A_s8bg)     # production position
    d["bg_after_2stn"] = gain(d.B_s2, d.B_s2bg)     # moved one step earlier
    d["stn3to8_no_bg"] = gain(d.A_s2, d.A_s8)       # production position
    d["stn3to8_with_bg"] = gain(d.B_s2bg, d.B_s8bg)  # measured with a background present
    d["first2"] = gain(d.rmse_Bud0, d.A_s2)

    print("\n=== does the ANSWER depend on the ORDER? (median % RMSE reduction) ===")
    print(f"  the background, added AFTER stations 3-8 (production) : "
          f"{d.bg_after_8stn.median():6.2f}%")
    print(f"  the background, added BEFORE stations 3-8             : "
          f"{d.bg_after_2stn.median():6.2f}%")
    print(f"  stations 3-8, with NO background present (production) : "
          f"{d.stn3to8_no_bg.median():6.2f}%")
    print(f"  stations 3-8, with a background already present       : "
          f"{d.stn3to8_with_bg.median():6.2f}%")
    print(f"\n  endpoint check, both orders reach the same information set:")
    print(f"    A final RMSE {d.A_s8bg.median():.4f}   B final RMSE {d.B_s8bg.median():.4f}"
          f"   diff {abs(d.A_s8bg.median() - d.B_s8bg.median()):.2e}")

    # ── [3] bootstrap over CITIES ─────────────────────────────────────────────────────────
    print(f"\n[3] bootstrapping over cities, {a.boot} resamples")
    rng = np.random.default_rng(a.seed)
    L = pd.read_csv(MOD / "ladder_revalidated.csv")
    L = L[L.bottom == "Bud0c"].copy()
    L["g_first2"] = gain(L.rmse_Bud0, L.rmse_Bud1)
    L["g_stn3to8"] = gain(L.rmse_Bud1, L.rmse_Bud2)
    L["g_bg"] = gain(L.rmse_Bud2, L.rmse_Bud3)

    def boot_ci(v: pd.Series):
        v = v.dropna().to_numpy()
        if len(v) < 3:
            return np.nan, np.nan, np.nan, len(v)
        idx = rng.integers(0, len(v), size=(a.boot, len(v)))
        meds = np.median(v[idx], axis=1)
        return (float(np.median(v)), float(np.percentile(meds, 2.5)),
                float(np.percentile(meds, 97.5)), len(v))

    # The MAIAC ladder carries the HEADLINE tropical inversion, so it is bootstrapped too.
    # Bootstrapping only the GHAP ladder would put an interval on one number and leave the
    # number actually quoted in the abstract without one.
    M = pd.read_csv(MOD / "ladder_maiac.csv")
    M = M[M.bottom == "Bud0c"].copy()
    M["g_first2"] = gain(M.rmse_Bud0, M.rmse_Bud1)
    M["g_stn3to8"] = gain(M.rmse_Bud1, M.rmse_Bud2)
    M["g_bg"] = gain(M.rmse_Bud2, M.rmse_Bud3)

    out = []
    for ladder_name, frame in (("ghap", L), ("maiac", M)):
        for label, col in (("first two sensors", "g_first2"),
                           ("sensors three to eight", "g_stn3to8"),
                           ("a background series", "g_bg")):
            m, lo, hi, n = boot_ci(frame[col])
            out.append(dict(ladder=ladder_name, stratum="pooled", step=label, n_cities=n,
                            median=m, lo95=lo, hi95=hi))
            for b, sub in frame.groupby("band"):
                m, lo, hi, n = boot_ci(sub[col])
                out.append(dict(ladder=ladder_name, stratum=b, step=label, n_cities=n,
                                median=m, lo95=lo, hi95=hi))
    bt = pd.DataFrame(out)

    # Does the deep-tropical inversion survive an interval? Paired over cities, since the two
    # gains are measured on the SAME city and a difference of medians would ignore the pairing.
    summary = {
        "order_cities": int(len(d)),
        "order_bg_after_8stn": round(float(d.bg_after_8stn.median()), 2),
        "order_bg_after_2stn": round(float(d.bg_after_2stn.median()), 2),
        "order_stn3to8_no_bg": round(float(d.stn3to8_no_bg.median()), 2),
        "order_stn3to8_with_bg": round(float(d.stn3to8_with_bg.median()), 2),
        "order_endpoint_gap": round(float(abs(d.A_s8bg.median() - d.B_s8bg.median())), 3),
    }
    for ladder_name, frame in (("ghap", L), ("maiac", M)):
        dt = frame[frame.band == "deep_tropical"][["g_first2", "g_bg"]].dropna()
        if len(dt) >= 3:
            v = (dt.g_first2 - dt.g_bg).to_numpy()
            idx = rng.integers(0, len(v), size=(a.boot, len(v)))
            meds = np.median(v[idx], axis=1)
            lo, hi = float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))
            summary[f"inv_{ladder_name}_median"] = round(float(np.median(v)), 2)
            summary[f"inv_{ladder_name}_lo"] = round(lo, 2)
            summary[f"inv_{ladder_name}_hi"] = round(hi, 2)
            summary[f"inv_{ladder_name}_frac_cities"] = int(round(100 * (v > 0).mean()))
            summary[f"inv_{ladder_name}_n"] = int(len(v))
            summary[f"inv_{ladder_name}_excludes_zero"] = bool(lo > 0)
            print(f"\n  deep-tropical inversion, {ladder_name}: paired median advantage of the "
                  f"first two sensors over a background")
            print(f"    {np.median(v):+.2f} pp  [{lo:+.2f}, {hi:+.2f}]  n={len(v)}  "
                  f"| favours sensors in {100 * (v > 0).mean():.0f}% of cities  "
                  f"| excludes zero: {lo > 0}")

    import json as _json
    with open(MOD / "ladder_order_summary.json", "w", encoding="utf-8") as fh:
        _json.dump(summary, fh, indent=2)
    print(f"\n    -> ladder_order_summary.json")
    bt.to_csv(OUT_BOOT, index=False)
    print(f"    -> {OUT_BOOT.name}")
    print("\n=== 95% intervals over CITIES, not city-days ===")
    for ladder_name in ("ghap", "maiac"):
        print(f"\n--- {ladder_name} ladder ---")
        for s in ("pooled", "deep_tropical", "tropical", "subtropical", "temperate"):
            sub = bt[(bt.stratum == s) & (bt.ladder == ladder_name)]
            if sub.empty:
                continue
            print(f"  {s}")
            for r in sub.itertuples():
                print(f"    {r.step:<24} n={r.n_cities:>2}  {r.median:6.2f}%  "
                      f"[{r.lo95:6.2f}, {r.hi95:6.2f}]")


if __name__ == "__main__":
    main()
