"""build_dashboard_data.py -- datasets for the supervisor review dashboard (2026-10-09).

Every figure on the dashboard (claude.ai artifact "Kandy PM2.5 Evidence Review") comes from one of these CSVs, and
every CSV is computed here from the stored result files, so the dashboard can be rebuilt after any re-run.

Out: data/processed/dashboard/*.csv
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
L2 = MOD / "ladder_v2"
OUT = REPO / "data" / "processed" / "dashboard"
REG = REPO.parent / "#writing" / "registrations.json"


def save(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f"{name}.tmp.csv"
    df.to_csv(tmp, index=False, float_format="%.4g")
    os.replace(tmp, OUT / f"{name}.csv")
    print(f"  {name:<18} {len(df):>4} rows")


def ci(v: dict) -> tuple[float, float, float, int]:
    lo, hi = v.get("cluster", [v.get("lo"), v.get("hi")])[:2]
    return v["median"], lo, hi, v.get("n", v.get("cities"))


def main() -> int:
    # 1. registered confirmation endpoints (as constructed), both arms
    S = json.load(open(L2 / "confirm_REGISTERED_summary.json", encoding="utf-8"))
    lab = {"first2_rmse": ("H1", "First two stations, used only to recalibrate", "% reduction"),
           "s36_rmse": ("H2", "Stations three to six, same recalibration", "points"),
           "bg_rmse": ("H3", "Background series, read on the day", "% reduction"),
           "bgm2_rmse": ("H4", "Background minus first two", "points"),
           "bgm2_exceed": ("H5", "Background minus first two, exceedance days", "points")}
    rows = []
    for arm in ("reconstruction", "prospective"):
        for k, (h, name, unit) in lab.items():
            v = S[arm].get(f"pooled.{k}")
            if v:
                m, lo, hi, n = ci(v)
                rows.append(dict(endpoint=h, label=name, unit=unit, arm=arm, median=m, lo=lo, hi=hi, cities=n))
    save(pd.DataFrame(rows), "endpoints")

    # 2. like-for-like arms (post hoc), union of cities with >= 8 pool stations
    R = json.load(open(L2 / "review_registered_loco_summary.json", encoding="utf-8"))
    reg = R["reconstruction.union.registered_samecities"]
    arms = [("cal_first2", "First two, recalibration only", "registered construction", reg["first2_rmse"]),
            ("reg_background", "Background, read on the day", "registered construction", reg["bg_rmse"])]
    sym = R["reconstruction.union.symmetric"]
    for k, name in (("gL2s_rmse", "First two, read on the day"), ("gBGall_rmse", "Background as registered, read on the day"),
                    ("gBG2_rmse", "Background from two outer stations"), ("gM2_rmse", "Mean of two outer stations")):
        arms.append((k, name, "same-day", sym[k]))
    save(pd.DataFrame([dict(arm=a, label=l, use=u, median=ci(v)[0], lo=ci(v)[1], hi=ci(v)[2], cities=ci(v)[3])
                       for a, l, u, v in arms]), "like_for_like")

    # 3. paired differences between same-day arms, three runs
    runs = [("Registered data", "review_registered_loco_summary.json"),
            ("Full networks", "review_full_loco_summary.json"),
            ("Corrected CNEMC data", "review_registered_loco_clean_summary.json")]
    diffs = []
    for run, f in runs:
        Z = json.load(open(L2 / f, encoding="utf-8"))
        for arm in ("reconstruction", "prospective"):
            blk = Z[f"{arm}.union.symmetric"]
            for k, name in (("BGallmL2s_rmse", "Background minus first two"),
                            ("BG2mL2s_rmse", "Two-station background minus first two"),
                            ("M2mL2s_rmse", "Two other stations minus first two"),
                            ("BGallmL2s_exceed", "Background minus first two, exceedance days")):
                if k in blk:
                    m, lo, hi, n = ci(blk[k])
                    diffs.append(dict(run=run, arm=arm, comparison=name, median=m, lo=lo, hi=hi, cities=n))
    save(pd.DataFrame(diffs), "arm_differences")

    # 4. station-count curve, read daily vs calibration
    K = json.load(open(L2 / "review_k_full_summary.json", encoding="utf-8"))
    sc = []
    for k in range(1, 9):
        for m, use in (("day", "read daily"), ("cal", "calibration only")):
            v = K.get(f"{m}{k}_rmse")
            if v:
                sc.append(dict(stations=k, use=use, median=v["median"], lo=v["cluster"][0], hi=v["cluster"][1],
                               cities=v["n"]))
    save(pd.DataFrame(sc), "station_count")

    # 5. per-city same-day gains (registered data) with network, band, latitude, reference share
    C = pd.read_csv(L2 / "review_registered_loco_percity_symmetric_reconstruction.csv", index_col=0)
    conf = set(pd.read_csv(MOD / "confirmation" / "confirmation_panel.csv").cid.astype(str))
    cities = pd.DataFrame({
        "city": C.index.astype(str),
        "network": C.cluster.astype(str).values,
        "band": C.band.str.replace("_", " ").values,
        "abs_latitude": C.lat.abs().round(1).values,
        "reference_share": (C.frac_reference * 100).round(0).values,
        "panel": ["confirmation" if c in conf else "discovery" for c in C.index.astype(str)],
        "first_two_daily": C.gL2s_rmse.values,
        "background_daily": C.gBGall_rmse.values,
        "background_minus_first_two": C.BGallmL2s_rmse.values,
    }).dropna(subset=["first_two_daily"])
    save(cities, "cities")

    # 6. spatial curve: per-city kriging minus raster at k=3 (full records) and free-surface benchmark
    sp = pd.read_csv(MOD / "spatial_curve_full" / "analysis" / "reanalysis_city.csv")
    sp = sp[(sp.k == 3) & sp.primary].copy()
    se = np.sqrt(sp["var"])
    save(pd.DataFrame({"city": sp.cluster.astype(str), "country": sp.country, "band": sp.band.str.replace("_", " "),
                       "sites": sp.n, "difference_z": sp.d, "lo": sp.d - 1.96 * se, "hi": sp.d + 1.96 * se})
         .sort_values("difference_z"), "spatial_cities")
    sb = json.load(open(MOD / "spatial_curve_full" / "analysis" / "satellite_benchmark.json", encoding="utf-8"))
    rn = json.load(open(MOD / "spatial_curve_full" / "analysis" / "reanalysis.json", encoding="utf-8"))
    bench = []
    for k, name in (("GHAP", "Satellite PM2.5 surface (GHAP)"), ("E1", "Built-up land-cover layer"),
                    ("GHAP_minus_E1", "Satellite surface minus land cover"), ("E3k3_minus_GHAP", "Kriging, 3 stations, minus satellite"),
                    ("E3k5_minus_GHAP", "Kriging, 5 stations, minus satellite"), ("E3k8_minus_GHAP", "Kriging, 8 stations, minus satellite")):
        v = sb[k]
        bench.append(dict(item=k, label=name, median=v["median"], lo=v["lo"], hi=v["hi"], cities=v["cities"]))
    save(pd.DataFrame(bench), "spatial_benchmark")
    h = rn["S4_holm_crossover"]
    het = rn["S3_heterogeneity_by_k"]["3"]
    save(pd.DataFrame([
        dict(metric="cities_crossing_holm", value=h["crossing"], of=h["cities"], note="cities where kriging beats the land-cover layer after a Holm correction"),
        dict(metric="heterogeneity_p_k3", value=het["p_Q"], of=het["cities"], note="Cochran Q p-value, between-city spread at 3 stations"),
        dict(metric="detection_limit", value=rn["S7"]["limit_with_empirical_sd"], of=rn["S7"]["countries"], note="smallest effect the test can detect (rank correlation), with the observed spread"),
    ]), "spatial_summary")

    # 7. registration scoreboard
    reg_ = json.load(open(REG, encoding="utf-8"))["registrations"]
    rr = [dict(osf=r["osf"], name=r.get("label", r["name"]), date=r["date"], predictions=r["predictions"],
               held=r["held"], refuted=r["refuted"], other=r["predictions"] - r["held"] - r["refuted"])
          for r in reg_ if r.get("refuted") is not None]
    save(pd.DataFrame(rr), "registrations")

    # 8. Kandy temporal anchor skill: deployed lag-free vs lagged nowcaster vs persistence
    tr = REPO / "data" / "processed" / "stage1_v3" / "training"
    lf = pd.read_csv(tr / "summary_v3_lgbm_lagfree.csv").iloc[0]
    bl = pd.read_csv(tr / "summary_blend_v3.csv"); bl = bl[bl.model.str.contains("Blender \\(pre", regex=True)].iloc[0]
    d = pd.read_parquet(REPO / "data" / "processed" / "stage1_v3" / "dataset_v3_hourly.parquet",
                        columns=["sensor_id", "datetime_utc", "pm25_observed"]).dropna()
    d["t"] = pd.to_datetime(d.datetime_utc); d = d.sort_values(["sensor_id", "t"])
    d["prev"] = d.groupby("sensor_id").pm25_observed.shift(1)
    x = d[d.groupby("sensor_id").t.diff() == pd.Timedelta(hours=1)]
    r2p = 1 - ((x.pm25_observed - x.prev) ** 2).sum() / ((x.pm25_observed - x.pm25_observed.mean()) ** 2).sum()
    save(pd.DataFrame([
        dict(model="Deployed anchor (no measured inputs)", r2=lf.r2_pooled, rmse=lf.rmse_pooled, hours=int(lf.n_obs)),
        dict(model="Nowcaster using earlier hours' readings", r2=bl.r2, rmse=bl.rmse, hours=int(bl.n)),
        dict(model="Previous hour's reading", r2=r2p, rmse=float(np.sqrt(((x.pm25_observed - x.prev) ** 2).mean())), hours=len(x)),
    ]), "anchor_skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
