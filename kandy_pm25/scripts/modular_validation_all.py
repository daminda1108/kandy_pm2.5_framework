"""modular_validation_all.py — the budget ladder across BOTH arms of the registered sample.

Runs the design registered in `docs/prereg_modular_validation_v2_2026-08-18.md` (option C,
Amendment 2): CNEMC + OpenAQ pooled, latitude band as the stratum, scored against gates V1-V6.

DESIGN POINTS THAT MATTER

  Identical features across arms. A pooled leave-one-city-out model whose predictors differ by
  source would confound "which network" with "how skilful", which is the exact confound
  Amendment 2 exists to remove. Both arms therefore use t2m, u10, v10, wind, BLH and
  day-of-year, and nothing else.

  NO lat/lon in Bud0. They are admissible under gotcha #73 (they exist for a target with no
  observations), but a model given latitude can learn "this latitude implies this pollution
  level" -- which would make the band contrast partly circular, since band IS latitude. Excluded
  by choice, and the choice is recorded here rather than buried.

  Bud0 is genuinely sensorless (V2): the training fold drops every row of the target city,
  asserted in code.

  Scoring is on held-out stations no rung ever sees, in every city and at every rung.

Usage: python scripts/modular_validation_all.py [--seed 0]
Out:   data/processed/modular/ladder_all.csv, summary_all.csv
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.modular import shrinkage as sh   # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
PANEL = REPO / "data" / "processed" / "cnemc_panel"

FEATS = ["temperature_2m", "u_component_of_wind_10m", "v_component_of_wind_10m",
         "wind", "boundary_layer_height", "doy_sin", "doy_cos"]


def band(lat: float) -> str:
    a = abs(lat)
    return ("deep_tropical" if a < 15 else "tropical" if a < 23.5
            else "subtropical" if a < 35 else "temperate")


# ── station data, one interface per arm ───────────────────────────────────────────────────

def stations_openaq(cluster: int) -> pd.DataFrame:
    d = pd.read_parquet(MOD / "openaq" / f"{cluster}.parquet",
                        columns=["station_id", "datetime_utc", "pm25"])
    d["date"] = pd.to_datetime(d.datetime_utc).dt.floor("D")
    return d[["station_id", "date", "pm25"]]


def stations_cnemc(slug: str) -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(PANEL / "cities" / slug / "*.parquet"))):
        try:
            frames.append(pd.read_parquet(f, columns=["station_id", "pm25", "datetime_utc"]))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    d = pd.concat(frames, ignore_index=True)
    d["pm25"] = pd.to_numeric(d.pm25, errors="coerce")
    d["date"] = pd.to_datetime(d.datetime_utc, errors="coerce", utc=True).dt.tz_localize(None).dt.floor("D")
    d = d.dropna(subset=["pm25", "date"])
    return d[(d.pm25 > 0) & (d.pm25 < 1000)][["station_id", "date", "pm25"]]


def drivers_openaq(cluster: int) -> pd.DataFrame:
    d = pd.read_csv(MOD / "drivers" / f"{cluster}.csv")
    d["date"] = pd.to_datetime(d.date, errors="coerce").dt.tz_localize(None)
    return d


def drivers_cnemc() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(PANEL / "met_raw" / "cnemc_era5_*.csv"))):
        d = pd.read_csv(f)
        keep = ["slug", "date"] + [c for c in FEATS if c in d.columns]
        frames.append(d[keep])
    m = pd.concat(frames, ignore_index=True)
    m["date"] = pd.to_datetime(m["date"], errors="coerce", utc=True).dt.tz_localize(None)
    m["wind"] = np.hypot(m.u_component_of_wind_10m, m.v_component_of_wind_10m)
    return m.dropna(subset=["date"]).drop_duplicates(["slug", "date"])


# ── assembly ──────────────────────────────────────────────────────────────────────────────

def build_frame(sample: pd.DataFrame, manifest: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Return {city_id: station frame} and the pooled daily driver+target table."""
    st, rows = {}, []
    cn_drv = drivers_cnemc()

    for r in sample.itertuples():
        cid = str(r.slug)
        try:
            if r.src == "OpenAQ":
                c = int(r.cluster)
                if not (MOD / "openaq" / f"{c}.parquet").exists():
                    continue
                if not (MOD / "drivers" / f"{c}.csv").exists():
                    continue
                s = stations_openaq(c)
                d = drivers_openaq(c)
            else:
                s = stations_cnemc(cid)
                d = cn_drv[cn_drv.slug == cid].copy()
            if s.empty or s.station_id.nunique() < 10 or d.empty:
                continue
            city = s.groupby("date").pm25.mean().rename("pm25_city").reset_index()
            m = city.merge(d, on="date", how="inner")
            if len(m) < 200:
                continue
            m["city"] = cid
            m["band"] = band(r.lat)
            m["src"] = r.src
            st[cid] = s
            rows.append(m)
        except Exception as e:
            print(f"  skip {cid}: {str(e)[:60]}")
    return st, pd.concat(rows, ignore_index=True)


def fit_bud0(pool: pd.DataFrame, seed: int) -> pd.DataFrame:
    from sklearn.ensemble import HistGradientBoostingRegressor
    p = pool.copy()
    doy = p.date.dt.dayofyear
    p["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    p["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    feats = [c for c in FEATS if c in p.columns]
    out = []
    for city in sorted(p.city.unique()):
        tr, te = p[p.city != city], p[p.city == city]
        assert city not in set(tr.city), "V2 violated: target city leaked into training"
        if len(tr) < 1000 or len(te) < 100:
            continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, random_state=seed)
        m.fit(tr[feats], tr.pm25_city)
        out.append(pd.DataFrame({"city": city, "date": te.date.values,
                                 "bud0": m.predict(te[feats])}))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def _affine(obs, prior):
    m = np.isfinite(obs) & np.isfinite(prior)
    if m.sum() < 30:
        return 0.0, 1.0
    A = np.vstack([np.ones(m.sum()), prior[m]]).T
    c, *_ = np.linalg.lstsq(A, obs[m], rcond=None)
    return float(c[0]), float(c[1])


def ladder(city: str, st: pd.DataFrame, bud0: pd.DataFrame, seed: int,
           bg_override: pd.Series | None = None) -> dict | None:
    """bg_override -- use this daily background for Bud3 instead of the city's own outer ring.

    Supplied by independent_background.py so the same-network and independent backgrounds run
    through an IDENTICAL Bud0->Bud1->Bud2->Bud3 chain. Comparing a gain measured against Bud2
    with one measured against a climatological constant is not a comparison at all.
    """
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(st.station_id.unique()))
    rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    held, pool = ids[:n_hold], ids[n_hold:]
    roles = {"b1": pool[:2], "b2": pool[:min(6, len(pool))], "reg": pool[min(6, len(pool)):]}

    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    target = daily(held).rename("obs")
    p0 = bud0[bud0.city == city].set_index("date").bud0
    fr = pd.concat([p0, target], axis=1).dropna()
    if len(fr) < 120:
        return None

    pred = {"Bud0": fr.bud0.to_numpy()}
    for rung, key in (("Bud1", "b1"), ("Bud2", "b2")):
        j = pd.concat([p0, daily(roles[key]).rename("fit")], axis=1).dropna()
        a, b = _affine(j.fit.to_numpy(), j.bud0.to_numpy())
        pred[rung] = a + b * fr.bud0.to_numpy()
    bg = (bg_override.rename("bg") if bg_override is not None
          else (st[st.station_id.isin(roles["reg"])].groupby("date").pm25.quantile(0.10)
                .rename("bg") if len(roles["reg"]) else None))
    if bg is not None:
        j = pd.concat([p0, bg, daily(roles["b2"]).rename("fit")], axis=1).dropna()
        if len(j) > 60:
            A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.bg.to_numpy()]).T
            c, *_ = np.linalg.lstsq(A, j.fit.to_numpy(), rcond=None)
            k = pd.concat([p0, bg], axis=1).reindex(fr.index)
            pred["Bud3"] = (c[0] + c[1] * k.bud0.to_numpy()
                            + c[2] * k.bg.fillna(k.bg.mean()).to_numpy())

    obs = fr.obs.to_numpy()
    days = fr.index.astype(str).to_numpy()
    cur = pred["Bud0"]
    row = {"city": city, "n_held": len(held), "n_days": len(fr),
           "rmse_Bud0": float(np.sqrt(np.mean((cur - obs) ** 2)))}
    for rung in ("Bud1", "Bud2", "Bud3"):
        if rung not in pred:
            row[f"rmse_{rung}"], row[f"w_{rung}"] = np.nan, np.nan
            continue
        r = sh.optimal_weight(cur, pred[rung], obs, groups=days, seed=seed)
        cur = sh.combine(cur, pred[rung], r.w)
        row[f"rmse_{rung}"], row[f"w_{rung}"] = r.skill_shrunk, r.w
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-blh", action="store_true",
                    help="drop BLH from Bud0. Sensitivity check: BLH coverage differs by up "
                         "to 5.1 pp across bands, so any band contrast must survive its "
                         "removal to be attributed to regime rather than driver completeness.")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    sample = pd.read_csv(MOD / "validation_sample.csv")
    man = pd.read_csv(MOD / "openaq_manifest.csv")
    ok = set(man[(man.status == "OK") & (man.stations >= 10)].cluster.astype(int))
    sample = sample[(sample.src == "CNEMC") | (sample.cluster.fillna(-1).astype(int).isin(ok))]
    print(f"sample after ingest exclusions: {len(sample)} "
          f"({int((sample.src=='OpenAQ').sum())} OpenAQ + {int((sample.src=='CNEMC').sum())} CNEMC)")

    global FEATS
    if a.no_blh:
        FEATS = [f for f in FEATS if f != "boundary_layer_height"]
        print("  --no-blh: Bud0 features =", FEATS)
    st, pool = build_frame(sample, man)
    print(f"cities with usable data: {len(st)} | {len(pool):,} city-days")
    print(f"by band: {pool.drop_duplicates('city').band.value_counts().to_dict()}")

    print("fitting leave-one-city-out Bud0 ...")
    bud0 = fit_bud0(pool, a.seed)
    print(f"  Bud0 for {bud0.city.nunique()} cities")

    meta = pool.drop_duplicates("city").set_index("city")[["band", "src"]]
    rows = []
    for city in sorted(st):
        if city not in set(bud0.city):
            continue
        r = ladder(city, st[city], bud0, a.seed)
        if r:
            r["mean_pm"] = float(pool[pool.city == city].pm25_city.mean())
            r["band"] = meta.loc[city, "band"]
            r["src"] = meta.loc[city, "src"]
            rows.append(r)
    L = pd.DataFrame(rows)
    L.to_csv(MOD / f"ladder_all{a.tag}.csv", index=False)

    print(f"\n=== LADDER: {len(L)} cities ===")
    g = L.groupby("band")[["rmse_Bud0", "rmse_Bud1", "rmse_Bud2", "rmse_Bud3"]].median()
    g["n"] = L.groupby("band").size()
    print(g.round(2).to_string())
    g.to_csv(MOD / f"summary_all{a.tag}.csv")

    print("\nmedian shrinkage weight by band:")
    print(L.groupby("band")[["w_Bud1", "w_Bud2", "w_Bud3"]].median().round(3).to_string())

    mono = ((L.rmse_Bud1 <= L.rmse_Bud0 + 1e-9) & (L.rmse_Bud2 <= L.rmse_Bud1 + 1e-9)
            & (L.rmse_Bud3.fillna(np.inf) <= L.rmse_Bud2 + 1e-9))
    print(f"\nV1 monotone: {int(mono.sum())}/{len(L)} ({100*mono.mean():.0f}%) "
          f"-- {'PASS' if mono.mean() >= 0.9 else 'FAIL'}")
    if (~mono).any():
        print("  violations:", ", ".join(L[~mono].city.tolist()))
    print("\nV5: any Kandy-relevance claim rests on the deep_tropical cell ALONE "
          f"(n={int((L.band=='deep_tropical').sum())}).")


if __name__ == "__main__":
    main()
