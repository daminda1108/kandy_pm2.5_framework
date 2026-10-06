"""ladder_v2_rich.py -- does the confirmed ladder survive a RICHER sensorless baseline? (registered test)

Registration draft: docs/prereg_rich_baseline_2026-09-28_DRAFT.md. The frozen ladder v2 estimator
(`ladder_v2.run`, unchanged) is run twice on the SAME frame, the discovery + confirmation union
(`ladder_v2_confirm.union`):

  base   Bud0c as confirmed: drivers + urban-centre geography + MAIAC AOD
  rich   Bud0R = Bud0c + 13 features from five global streams (rich_streams_pull.py):
           cams_pm25 (CAMS NRT surface PM2.5), no2_trop (TROPOMI), precip_mm (IMERG),
           fire_n100, fire_n300, fire3_n300 (FIRMS; the last a 3-day trailing sum), dow (day of week),
           elev_m, relief_10, relief_30, slope_10, floor_rel_30, enclosure (Copernicus GLO-30)

Same splits, seeds, weights rule, completeness rule and bootstrap as the confirmation. The base run
must reproduce the registered confirmation per-city effects exactly (parity assert) before anything
from the rich run is written.

Coverage rule (admissibility, both directions): a city enters only if terrain is complete and CAMS,
IMERG and FIRMS each cover >= 90 % of its frame days; NO2 and AOD may be missing on any day (left
missing, as AOD always was). Every new feature must be used (asserted), none may be all-missing.

  --dry-run   replaces every PM2.5 value with a SYNTHETIC series independent of all predictors
              (seeded AR(1) lognormal per city + station noise), so the code path is exercised end to
              end with no real outcome computed. Allowed before registration.
  --score     the registered run; refuses unless rich/REGISTERED.json names an OSF id.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
RS = MOD / "rich_streams"
OUTD = MOD / "ladder_v2"
RICH = ["cams_pm25", "no2_trop", "precip_mm", "fire_n100", "fire_n300", "fire3_n300", "dow",
        "elev_m", "relief_10", "relief_30", "slope_10", "floor_rel_30", "enclosure"]
TERRAIN = ["elev_m", "relief_10", "relief_30", "slope_10", "floor_rel_30", "enclosure"]
MUST = {"cams_pm25": 0.90, "precip_mm": 0.90, "fire_n300": 0.90}


def _stream(name, cols):
    fs = sorted((RS / name).glob("*.csv"))
    if not fs:
        raise SystemExit(f"no {name} files")
    d = pd.concat([pd.read_csv(f).assign(city=f.stem.rsplit("_", 1)[0]) for f in fs], ignore_index=True)
    d["date"] = pd.to_datetime(d.date)
    return d[["city", "date", *cols]].drop_duplicates(["city", "date"])


def add_rich(p: pd.DataFrame):
    fire = _stream("firms", ["fire_n100", "fire_n300"]).sort_values(["city", "date"])
    fire["fire3_n300"] = (fire.groupby("city").fire_n300
                          .transform(lambda s: s.rolling(3, min_periods=1).sum()))
    parts = [_stream("cams", ["cams_pm25"]), _stream("no2", ["no2_trop"]),
             _stream("imerg", ["precip_mm"]), fire]
    q = p.copy()
    q["city"] = q.city.astype(str)
    for d in parts:
        q = q.merge(d, on=["city", "date"], how="left")
    t = pd.read_csv(RS / "terrain.csv", dtype={"city": str})
    q = q.merge(t[["city", *TERRAIN]], on="city", how="left")
    q["dow"] = q.date.dt.dayofweek.astype(float)
    cov = q.groupby("city")[list(MUST)].apply(lambda g: g.notna().mean())
    bad_stream = cov[(cov < pd.Series(MUST)).any(axis=1)].index.tolist()
    bad_terr = q.groupby("city")[TERRAIN].apply(lambda g: g.isna().any().any())
    drop = sorted(set(bad_stream) | set(bad_terr[bad_terr].index))
    for f in RICH:
        assert q[f].notna().any(), f"{f} is all missing"
    return q, drop, cov


def synthetic(st: dict, p: pd.DataFrame, seed: int = 20260928):
    """Outcome replaced by noise independent of every predictor (dry run only)."""
    rng = np.random.default_rng(seed)
    st2, city_rows = {}, []
    for c, s in st.items():
        days = np.sort(s.date.unique())
        z = np.zeros(len(days))
        for i in range(1, len(days)):
            z[i] = 0.7 * z[i - 1] + rng.normal(0, 0.4)
        base = pd.Series(np.exp(2.8 + z), index=days)
        s2 = s.copy()
        s2["pm25"] = base.reindex(s2.date).to_numpy() * np.exp(rng.normal(0, 0.25, len(s2)))
        st2[c] = s2
        city_rows.append(s2.groupby("date").pm25.mean().rename("syn").reset_index().assign(city=c))
    cm = pd.concat(city_rows, ignore_index=True)
    cm["date"] = pd.to_datetime(cm.date); cm["city"] = cm.city.astype(str)
    q = p.merge(cm, on=["city", "date"], how="left")
    q["pm25_city"] = q.pop("syn")
    return st2, q.dropna(subset=["pm25_city"])


def _require_registered():
    f = MOD / "rich" / "REGISTERED.json"
    if not f.exists() or not json.loads(f.read_text(encoding="utf-8")).get("osf"):
        raise SystemExit("REFUSED: the rich-baseline scoring runs only after its registration is lodged "
                         "(rich/REGISTERED.json with an OSF id)")


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--score", action="store_true")
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--bag", type=int, default=5)
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    if a.score:
        _require_registered()
    import ladder_v2_confirm as lvc
    from ladder_v2 import run
    (st, p, met, geo_f, sat), meta, conf, dropped = lvc.union("maiac")
    disc = sorted(set(st) - set(conf))
    if a.dry_run:
        st, p = synthetic(st, p)
    q, drop, cov = add_rich(p)
    print(f"coverage rule drops {len(drop)}: {drop}")
    keep = [c for c in st if c not in set(drop)]
    st = {c: st[c] for c in keep}
    q = q[q.city.isin(keep)]
    tag = "rich_dryrun" if a.dry_run else "rich_REGISTERED"
    out = {"config": dict(splits=a.splits, bag=a.bag, boot=a.boot, dropped_coverage=drop,
                          dropped_confirmation_rules=dropped, cities=len(keep), rich_features=RICH)}
    res = {}
    for arm, feats in (("base", sat), ("rich", sat + RICH)):
        assert set(RICH) <= set(q.columns)
        if arm == "rich":
            assert all(f in feats for f in RICH), "require_covers: a rich stream is unused"
        S, percity, r = run("maiac", a.splits, a.bag, "crossfit", True, "grid", a.boot, True,
                            frame=(st, q, met, geo_f, feats), meta=meta, score_cities=keep)
        res[arm] = (S, percity)
        S.to_csv(OUTD / f"{tag}_{arm}_splits.csv", index=False)
        for k, C in percity.items():
            C.to_csv(OUTD / f"{tag}_{arm}_percity_{k}.csv")
    if not a.dry_run:                                                     # parity with the registered run
        R = pd.read_csv(OUTD / "confirm_REGISTERED_percity_reconstruction.csv", index_col=0)
        B = res["base"][1]["reconstruction"]
        common = [c for c in R.index if c in B.index]
        cols = [c for c in R.columns if c.split("_")[0] in ("first2", "s36", "bg", "bgm2")]
        diff = (B.loc[common, cols] - R.loc[common, cols]).abs().max().max()
        out["parity_confirmation_base_max_abs_diff"] = float(diff)
        assert len(common) == len(R) or len(common) >= len(R) - len(drop), "confirmation cities lost"
        assert diff < 1e-9, f"base run does not reproduce the registered confirmation ({diff})"
    from ladder_v2 import boot_city, boot_cluster
    rng = np.random.default_rng(20260928)

    def summ(v, grp):
        v, grp = np.asarray(v, float), np.asarray(grp)
        k = ~np.isnan(v); v, grp = v[k], grp[k]
        bc, bk = boot_city(v, rng, a.boot), boot_cluster(v, grp, rng, a.boot)
        return dict(n=int(len(v)), median=float(np.median(v)),
                    city=[float(np.percentile(bc, 2.5)), float(np.percentile(bc, 97.5))],
                    cluster=[float(np.percentile(bk, 2.5)), float(np.percentile(bk, 97.5))])

    for armname in ("reconstruction", "prospective"):
        Sb, Sr = res["base"][0], res["rich"][0]
        sb, sr = Sb[Sb.arm == armname], Sr[Sr.arm == armname]
        m = sb.merge(sr, on=["city", "seed"], suffixes=("_b", "_r"))
        m["r1_rich_over_base"] = 100 * (m.Bud0_rmse_b - m.Bud0_rmse_r) / m.Bud0_rmse_b
        eff = ["first2_rmse", "s36_rmse", "bg_rmse", "bgm2_rmse", "bgm2_exceed", "bgm2_tail",
               "first2_tail", "first2_exceed"]
        for e in eff:
            m[f"d_{e}"] = m[f"{e}_r"] - m[f"{e}_b"]
        C = m.groupby("city")[["r1_rich_over_base", *[f"{e}_r" for e in eff],
                               *[f"d_{e}" for e in eff]]].median()
        C = C.join(meta[["cluster"]])
        C.to_csv(OUTD / f"{tag}_paired_percity_{armname}.csv")
        for panel, cs in (("confirmation", conf), ("discovery", disc), ("pooled", list(C.index))):
            sub = C[C.index.isin(set(cs))]
            for col in [c for c in C.columns if c != "cluster"]:
                out[f"{armname}.{panel}.{col}"] = summ(sub[col], sub.cluster)
    jp = OUTD / f"{tag}_summary.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, jp)
    if a.dry_run:
        print("dry run complete: synthetic target, nothing real computed ->", jp)
    else:
        for k in ("r1_rich_over_base", "first2_rmse_r", "d_first2_rmse", "s36_rmse_r", "bg_rmse_r",
                  "bgm2_rmse_r", "d_bgm2_rmse", "bgm2_exceed_r"):
            v = out[f"reconstruction.confirmation.{k}"]
            print(f"  {k:<22} n={v['n']:>3} {v['median']:+7.2f} cluster [{v['cluster'][0]:+.2f}, "
                  f"{v['cluster'][1]:+.2f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
