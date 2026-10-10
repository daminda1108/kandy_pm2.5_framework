"""medellin_showcase_s0.py — S0/S1: the ground-data ladder, tiers 0 and 1 (2026-07-11).

Act 0 — ABSOLUTELY ZERO local ground data: level from the Van Donkelaar satellite product
        (T_vand), spatial pattern from physics. No Medellín station touches the model.
        Field: {city}_decomp_predictions_{y}_additive_v2_vand.parquet (xichang_prod).
Act 1 — 2-sensor Kandy-grade budget: sensor-anchored T (the existing headline).
        Field: {city}_decomp_predictions_{y}_additive_v2.parquet.

Both fields use the increment-split additive form and the same smooth S_emit·M pattern;
the ONLY difference is the ground data feeding T(t). Scored against (a) the full held-out
vault and (b) the FIXED 6-station showcase holdout (greedy max-min spread, deterministic)
that Act 3's data-value curve reuses. Sanity gate: T-lock (field basin mean == T_q50).

Run:  .venv/Scripts/python.exe scripts/medellin_showcase_s0.py
Out:  results/figures/medellin_showcase/{act0_act1_scorecard.csv, holdout6.json}
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf  # noqa: E402

CITY = "medellin"
YEARS = (2019, 2020, 2021, 2022, 2023)
OUT = REPO / "results" / "figures" / "medellin_showcase"


def bilinear_weights(lats, lons, st_lat, st_lon):
    """Dense bilinear weight matrix W (n_st x n_px): station values = field @ W.T.
    Out-of-box stations get all-zero rows (NaN downstream)."""
    n_lat, n_lon = len(lats), len(lons)
    W = np.zeros((len(st_lat), n_lat * n_lon))
    for k, (la, lo) in enumerate(zip(st_lat, st_lon)):
        if not (lats[0] <= la <= lats[-1] and lons[0] <= lo <= lons[-1]):
            continue
        i = np.clip(np.searchsorted(lats, la) - 1, 0, n_lat - 2)
        j = np.clip(np.searchsorted(lons, lo) - 1, 0, n_lon - 2)
        fy = (la - lats[i]) / (lats[i + 1] - lats[i])
        fx = (lo - lons[j]) / (lons[j + 1] - lons[j])
        W[k, i * n_lon + j] = (1 - fy) * (1 - fx)
        W[k, i * n_lon + j + 1] = (1 - fy) * fx
        W[k, (i + 1) * n_lon + j] = fy * (1 - fx)
        W[k, (i + 1) * n_lon + j + 1] = fy * fx
    return W


def field_at_stations(parquet, st):
    """(loct, station_id, pred) long frame from a field parquet, vectorised."""
    d = pd.read_parquet(parquet, columns=["time", "lat", "lon", "pm25_q50"])
    d["time"] = pd.to_datetime(d.time, utc=True)
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    d = d.sort_values(["time", "lat", "lon"])
    times = pd.DatetimeIndex(d.time.unique())
    F = np.clip(d.pm25_q50.to_numpy().reshape(len(times), -1), 0, None)
    W = bilinear_weights(lats, lons, st.lat.to_numpy(), st.lon.to_numpy())
    V = F @ W.T                                       # (nt, n_st)
    V[:, W.sum(axis=1) < 0.5] = np.nan
    loct = times.tz_convert(xf.TZ)
    return pd.DataFrame({
        "loct": np.repeat(loct.to_numpy(), len(st)),
        "station_id": np.tile(st.index.to_numpy(), len(times)),
        "pred": V.ravel()}), float(F.mean(axis=1).mean())


def pick_holdout6(st, vault, n=6, seed=7, box=None):
    """Greedy max-min spread among IN-BOX vault stations (a held-out station outside
    the model's field box cannot be scored and must not occupy a holdout slot)."""
    ids = sorted(vault)
    if box is not None:
        la0, la1, lo0, lo1 = box
        ids = [s for s in ids
               if la0 <= st.at[s, "lat"] <= la1 and lo0 <= st.at[s, "lon"] <= lo1]
    pts = st.loc[ids, ["lat", "lon"]].to_numpy()
    rng = np.random.default_rng(seed)
    chosen = [int(rng.integers(len(ids)))]
    while len(chosen) < n:
        d = np.min([np.hypot(pts[:, 0] - pts[c, 0], pts[:, 1] - pts[c, 1])
                    for c in chosen], axis=0)
        d[chosen] = -1
        chosen.append(int(np.argmax(d)))
    return [ids[c] for c in chosen]


def score(pred_df, obs_df, stations):
    from scipy.stats import pearsonr, spearmanr
    P = pred_df[pred_df.station_id.isin(stations)].dropna(subset=["pred"])
    O = obs_df[obs_df.station_id.isin(stations)]
    m = P.merge(O, on=["loct", "station_id"])
    if len(m) < 100:
        return dict(seasonal=np.nan, diurnal=np.nan, level=np.nan,
                    spatial=np.nan, rmse=np.nan, n_pairs=len(m))
    g = m.assign(mo=m.loct.dt.month).groupby("mo")
    r_se = pearsonr(g.pred.mean(), g.pm25.mean())[0]
    g = m.assign(h=m.loct.dt.hour).groupby("h")
    r_di = pearsonr(g.pred.mean(), g.pm25.mean())[0]
    ps = m.groupby("station_id").agg(p=("pred", "mean"), o=("pm25", "mean"))
    rho = spearmanr(ps.p, ps.o)[0] if len(ps) >= 4 else np.nan
    lvl = 100 * (m.pred.mean() - m.pm25.mean()) / m.pm25.mean()
    rmse = float(np.sqrt(((m.pred - m.pm25) ** 2).mean()))
    return dict(seasonal=round(r_se, 3), diurnal=round(r_di, 3), level=round(lvl, 1),
                spatial=round(rho, 3), rmse=round(rmse, 2), n_pairs=len(m))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    xf._setup(CITY)
    st, anchors = xf._stations_split()
    vault = [s for s in st.index if int(s) not in anchors]
    f0 = pd.read_parquet(xf.DEC / f"{CITY}_decomp_predictions_2022_additive_v2.parquet",
                         columns=["lat", "lon"])
    box = (f0.lat.min(), f0.lat.max(), f0.lon.min(), f0.lon.max())
    hold6 = pick_holdout6(st, vault, box=box)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({"holdout6": hold6, "anchors": sorted(int(a) for a in anchors),
               "note": "fixed showcase holdout — greedy max-min spread, seed 7; "
                       "NEVER used for training/assimilation in any act"},
              open(OUT / "holdout6.json", "w"), indent=2)
    print(f"anchors {sorted(anchors)} | vault {len(vault)} | holdout6 {hold6}")

    tiers = {"act0_vand": "_additive_v2_vand", "act1_sensor": "_additive_v2"}
    preds, obs_all = {t: [] for t in tiers}, []
    for y in YEARS:
        Ts = pd.read_parquet(xf.DEC / f"T_{CITY}_hourly_{y}.parquet")
        for tier, suf in tiers.items():
            fp = xf.DEC / f"{CITY}_decomp_predictions_{y}{suf}.parquet"
            df, basin = field_at_stations(fp, st)
            preds[tier].append(df)
            if tier == "act1_sensor":     # T-lock sanity on the sensor tier
                dT = abs(basin - Ts.T_q50.mean())
                print(f"  {y}: {tier} basin {basin:.2f} (T-lock Δ {dT:.3f})")
        obs_all.append(xf._obs(y))
    obs = pd.concat(obs_all, ignore_index=True)
    obs["loct"] = obs.loct.dt.floor("h")

    rows = []
    for tier in tiers:
        pr = pd.concat(preds[tier], ignore_index=True)
        pr["loct"] = pd.to_datetime(pr.loct).dt.floor("h")
        for setname, stations in (("vault_all", vault), ("holdout6", hold6)):
            rows.append(dict(tier=tier, testset=setname, **score(pr, obs, stations)))
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "act0_act1_scorecard.csv", index=False)
    print("\n=== ground-data ladder, tiers 0-1 (identical held-out sets) ===")
    print(res.to_string(index=False))
    print(f"\nWrote {OUT / 'act0_act1_scorecard.csv'} + holdout6.json")


if __name__ == "__main__":
    main()
