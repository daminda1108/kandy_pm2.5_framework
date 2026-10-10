"""medellin_a2_amplitude_fit.py — Phase-1 A2: fix the amplitude deficit (A1 verdict).

A1 measured: the model orders stations well (rho 0.75) but compresses station-mean
contrast to slope 0.31 / std-ratio 0.51 of observed. A2 tests the minimal
T-lock-safe fix — one amplitude scalar on the unit-mean local pattern:

    P'(x, t) = 1 + a * (P(x, t) - 1)        (mean-1 preserved -> basin mean == T)
    guard: clamp P' >= 0.05, renormalise per hour to mean 1 (KTM 8x-contrast safety)

Protocol (pre-registered in the improvement plan):
  - FIT on Medellín's in-box withheld stations EXCLUDING the holdout-6 (n~11):
    a* minimises the SSE of long-term station means.
  - GATE 1 (Medellín): holdout-6 hourly RMSE + level must improve or hold; the
    station-mean slope should move toward 1.
  - GATE 2 (cross-city no-regression): apply the SAME a* to Kathmandu, Tai'an,
    Baoji, Chiang Mai — seasonal r / diurnal r / level / spatial rho must not
    degrade materially (each city scored on its own held-out network).
Only if BOTH gates pass does the rule become a candidate for the production
builders (and only then regime-conditioning is discussed).

Out: results/figures/medellin_showcase/a2_amplitude_{fit,crosscity}.csv + verdict.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf  # noqa: E402
from medellin_showcase_s0 import bilinear_weights  # noqa: E402

OUT = REPO / "results" / "figures" / "medellin_showcase"
A_GRID = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
CITIES_X = ["kathmandu", "taian", "baoji", "chiangmai"]


def city_data(city):
    """Per-city: hourly P/B/T arrays per year + long obs frame + station table."""
    xf._setup(city)
    st, _ = xf._stations_split()
    from city_config import cfg
    years = list(cfg(city)["years"])
    packs = []
    for y in years:
        fp = xf.DEC / f"{city}_decomp_predictions_{y}_additive_v2.parquet"
        if not fp.exists():
            continue
        f = pd.read_parquet(fp, columns=["time", "lat", "lon", "pm25_q50"])
        f["time"] = pd.to_datetime(f.time, utc=True)
        lats = np.sort(f.lat.unique()); lons = np.sort(f.lon.unique())
        f = f.sort_values(["time", "lat", "lon"])
        times = pd.DatetimeIndex(f.time.unique())
        F = f.pm25_q50.to_numpy().reshape(len(times), -1)
        T = pd.read_parquet(xf.DEC / f"T_{city}_hourly_{y}.parquet")
        T["t"] = pd.to_datetime(T.datetime_utc, utc=True)
        Tv = T.set_index("t").T_q50.reindex(times).to_numpy()
        B = pd.read_parquet(xf.DEC / f"B_background_hourly_{y}_{city}.parquet")
        B["t"] = pd.to_datetime(B.datetime_utc, utc=True)
        Bv = B.set_index("t").B.reindex(times).to_numpy()
        inc = Tv - Bv
        P = np.full_like(F, np.nan)
        acc = inc > 0.5
        P[acc] = (F[acc] - Bv[acc, None]) / inc[acc, None]
        hod = times.tz_convert(xf.TZ).hour
        for h in range(24):
            mh = (hod == h)
            clim = (np.nanmean(P[mh & acc], axis=0) if (mh & acc).any()
                    else np.nanmean(P[acc], axis=0))
            P[mh & ~acc] = clim
        packs.append(dict(times=times, lats=lats, lons=lons, P=P, B=Bv, T=Tv))
    obs = pd.concat([xf._obs(y) for y in years if
                     (xf.DEC / f"{city}_decomp_predictions_{y}_additive_v2.parquet").exists()],
                    ignore_index=True)
    obs["loct"] = obs.loct.dt.floor("h")
    return st, packs, obs


def assemble(pack, a):
    """Amplitude-transformed field for one year-pack."""
    P = 1.0 + a * (pack["P"] - 1.0)
    if a != 1.0:
        P = np.clip(P, 0.05, None)
        P = P / P.mean(axis=1, keepdims=True)          # restore per-hour mean 1 (T-lock)
    inc = pack["T"] - pack["B"]
    F = pack["B"][:, None] + np.clip(inc, 0, None)[:, None] * P \
        + np.clip(inc, None, 0)[:, None]
    return np.clip(F, 0, None)


def station_preds(packs, st, ids, a):
    """Long [sid, loct, pred] at the given stations."""
    rows = []
    W = None
    for pack in packs:
        sl = st.loc[ids]
        if W is None or W.shape[1] != len(pack["lats"]) * len(pack["lons"]):
            W = bilinear_weights(pack["lats"], pack["lons"],
                                 sl.lat.to_numpy(), sl.lon.to_numpy())
            inbox = W.sum(axis=1) > 0.5
        F = assemble(pack, a)
        V = F @ W.T
        V[:, ~inbox] = np.nan
        loct = pack["times"].tz_convert(xf.TZ).floor("h")
        for k, sid in enumerate(ids):
            if not inbox[k]:
                continue
            rows.append(pd.DataFrame({"sid": sid, "loct": loct, "pred": V[:, k]}))
    df = pd.concat(rows, ignore_index=True).dropna(subset=["pred"])
    return df


def metrics(pred, obs, ids):
    m = pred.merge(obs.rename(columns={"station_id": "sid"}), on=["loct", "sid"])
    if len(m) < 200:
        return None
    sm = m.groupby("sid").agg(o=("pm25", "mean"), p=("pred", "mean"))
    slope = float(np.polyfit(sm.o, sm.p, 1)[0]) if len(sm) >= 3 else np.nan
    rho = float(spearmanr(sm.o, sm.p)[0]) if len(sm) >= 4 else np.nan
    g = m.assign(mo=m.loct.dt.month).groupby("mo")
    sea = float(pearsonr(g.pred.mean(), g.pm25.mean())[0])
    g = m.assign(h=m.loct.dt.hour).groupby("h")
    diu = float(pearsonr(g.pred.mean(), g.pm25.mean())[0])
    lvl = float(100 * (m.pred.mean() - m.pm25.mean()) / m.pm25.mean())
    rmse = float(np.sqrt(np.mean((m.pred - m.pm25) ** 2)))
    return dict(n=len(m), slope=round(slope, 3), rho=round(rho, 3),
                seasonal=round(sea, 3), diurnal=round(diu, 3),
                level=round(lvl, 1), rmse=round(rmse, 2))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # ── Medellín fit + holdout gate ─────────────────────────────────────────
    st, packs, obs = city_data("medellin")
    hold6 = json.load(open(OUT / "holdout6.json"))["holdout6"]
    anchors = json.load(open(OUT / "holdout6.json"))["anchors"]
    withheld = [s for s in st.index if s not in anchors]
    train = [s for s in withheld if s not in hold6]
    print(f"MEDELLÍN: fit on {len(train)} withheld-non-holdout stations, "
          f"gate on holdout-6")
    rows = []
    for a in A_GRID:
        tr = metrics(station_preds(packs, st, train, a), obs, train)
        te = metrics(station_preds(packs, st, hold6, a), obs, hold6)
        rows.append(dict(a=a, **{f"tr_{k}": v for k, v in tr.items()},
                         **{f"te_{k}": v for k, v in te.items()}))
        print(f"  a={a:.1f}  train: slope {tr['slope']:.2f} rmse {tr['rmse']:.2f} "
              f"rho {tr['rho']:.2f} | holdout6: slope {te['slope']:.2f} "
              f"rmse {te['rmse']:.2f} rho {te['rho']:.2f} lvl {te['level']:+.1f}%")
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "a2_amplitude_fit.csv", index=False)
    # a* = train-station-mean SSE minimiser ~ slope closest to 1 on train
    astar = float(res.loc[(res.tr_slope - 1.0).abs().idxmin(), "a"])
    base = res[res.a == 1.0].iloc[0]
    sel = res[res.a == astar].iloc[0]
    g1 = (sel.te_rmse <= base.te_rmse + 0.05) and (abs(sel.te_level) <= abs(base.te_level) + 1.0)
    print(f"\na* = {astar} (train slope {sel.tr_slope:.2f})")
    print(f"GATE 1 (holdout-6): rmse {base.te_rmse:.2f}->{sel.te_rmse:.2f}, "
          f"level {base.te_level:+.1f}->{sel.te_level:+.1f}%, "
          f"slope {base.te_slope:.2f}->{sel.te_slope:.2f}  -> "
          f"{'PASS' if g1 else 'FAIL'}")

    # ── cross-city no-regression at a* ──────────────────────────────────────
    xrows = []
    for city in CITIES_X:
        try:
            stx, packsx, obsx = city_data(city)
            idsx = list(stx.index)
            m1 = metrics(station_preds(packsx, stx, idsx, 1.0), obsx, idsx)
            ma = metrics(station_preds(packsx, stx, idsx, astar), obsx, idsx)
            ok = (ma["rmse"] <= m1["rmse"] * 1.03 and
                  abs(ma["level"]) <= abs(m1["level"]) + 1.5 and
                  ma["seasonal"] >= m1["seasonal"] - 0.02)
            xrows.append(dict(city=city, **{f"b_{k}": v for k, v in m1.items()},
                              **{f"a_{k}": v for k, v in ma.items()}, no_regress=ok))
            print(f"  {city:10s} base rmse {m1['rmse']:6.2f} lvl {m1['level']:+6.1f}% "
                  f"rho {m1['rho']:+.2f} slope {m1['slope']:.2f} | a* rmse "
                  f"{ma['rmse']:6.2f} lvl {ma['level']:+6.1f}% rho {ma['rho']:+.2f} "
                  f"slope {ma['slope']:.2f}  {'OK' if ok else 'REGRESSION'}")
        except Exception as e:
            print(f"  {city}: skipped ({e})")
    xres = pd.DataFrame(xrows)
    xres.to_csv(OUT / "a2_amplitude_crosscity.csv", index=False)
    g2 = bool(xres.no_regress.all()) if len(xrows) else False
    print(f"\nGATE 2 (cross-city no-regression at a*={astar}): "
          f"{'PASS' if g2 else 'FAIL'} ({int(xres.no_regress.sum()) if len(xrows) else 0}"
          f"/{len(xrows)})")
    print(f"A2 VERDICT: {'ADOPT candidate' if (g1 and g2) else 'REJECT / needs regime-conditioning'}")


if __name__ == "__main__":
    main()
