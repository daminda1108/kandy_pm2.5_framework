"""t_anchor.py — per-city basin temporal anchor T(t) from TWO anchor stations.

The city analogue of the locked Kandy chain (predict_T_anchor_v3.py +
scripts/sharpen_T_diurnal.py), trained on ONLY the draw's anchor pair:

  1. residual target  r(t) = pm25_anchor(t) − c_prior_scaled(t), where
     c_prior_scaled = c_prior × ratio and ratio is the ROW-MEAN
     pm25.mean()/prior.mean() over anchor rows (gotcha #39 — never timestamp-mean).
     pm25_anchor(t) = per-hour mean of the (≤2) anchor observations.
  2. lag-free LGBM quantile heads (α=0.05/0.50/0.95) on exogenous AREA-mean
     drivers + calendar harmonics: sin/cos hour, sin/cos doy, dow, blh, u10, v10,
     wind speed, t2m, c_prior_scaled. Lag-free by design (forecast-ready; mirrors
     the Kandy lag-free decision).
  3. CV+ conformal per (month × 6-h hour-bin): 5 sequential time folds give
     out-of-fold quantiles; per-stratum widening factors are added to q05/q95
     (Mondrian over the same strata as Kandy).
  4. additive per-year level re-anchor so annual-mean q50 == L(year) =
     VanD basin area mean (β≡1; 2024/25 = 2023-proxy, Amendment 2). The same
     shift is applied to all three quantiles (level moves, widths preserved).
  5. diurnal + monthly amplitude sharpening to the ANCHOR-observed climatology
     (the lag-free GBM damps the swing — Kandy lesson): multiplicative hour-of-day
     and month factors (obs_clim / model_clim, clipped to [0.5, 2]), then the
     annual mean is restored to L(year).

Output: hourly DataFrame [datetime, T_q05, T_q50, T_q95] over the score years.
Anchor rows are the ONLY station data touched — the vault stays sealed.
"""
from __future__ import annotations

import numpy as np

ALPHA = 0.10                 # 90% interval (project standard)
CLIP_SHARPEN = (0.5, 2.0)    # bounds on climatology sharpening factors
N_FOLDS = 5                  # sequential CV folds for conformal scores

LGBM_PARAMS = dict(objective="quantile", learning_rate=0.05, num_leaves=63,
                   n_estimators=600, min_child_samples=20, subsample=0.8,
                   colsample_bytree=0.8, verbose=-1, n_jobs=-1)

FEATURES = ["sin_h", "cos_h", "sin_doy", "cos_doy", "dow",
            "blh_m", "u10", "v10", "wspd", "t2m", "c_prior_scaled"]


def _hod_bin(h) -> "np.ndarray":
    return np.asarray(h) // 6        # 4 bins, as in the Kandy conformal table


def _calendar(df):
    dt = df["datetime"]
    df["sin_h"] = np.sin(2 * np.pi * dt.dt.hour / 24)
    df["cos_h"] = np.cos(2 * np.pi * dt.dt.hour / 24)
    doy = dt.dt.dayofyear
    df["sin_doy"] = np.sin(2 * np.pi * doy / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * doy / 365.25)
    df["dow"] = dt.dt.dayofweek
    return df


def _driver_table(cp):
    """Hourly area-mean driver table with calendar features (no station data)."""
    from . import drivers
    g = drivers.geos_cf_prior(cp)
    b = drivers.blh(cp)
    w = drivers.era5_winds(cp)
    df = g.merge(b, on="datetime").merge(w, on="datetime")
    df["wspd"] = np.hypot(df.u10, df.v10)
    return _calendar(df)


def _anchor_series(cp, anchors):
    """Per-hour mean pm25 of the anchor pair (full record) + the row-mean ratio."""
    import pandas as pd
    df = pd.read_parquet(cp.station_parquet(),
                         columns=["datetime_utc", "station_id", "pm25", "c_prior"])
    df = df[df.station_id.isin(list(anchors))].dropna(subset=["pm25"])
    df["datetime"] = (pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)
                        .dt.tz_localize(None))
    df = df.dropna(subset=["datetime"])
    both = df.dropna(subset=["c_prior"])
    ratio = float(both.pm25.mean() / both.c_prior.mean())   # row-mean (gotcha #39)
    hourly = df.groupby("datetime")["pm25"].mean().rename("pm25_anchor").reset_index()
    return hourly, ratio


def fit_and_build(cp, anchors, sharpen: bool = True):
    """Train on the anchor pair, return hourly T(t) for cp.score_years.

    Returns (T DataFrame [datetime, T_q05, T_q50, T_q95], info dict).
    """
    import pandas as pd
    from lightgbm import LGBMRegressor
    from .vand import level_for_year

    drv = _driver_table(cp)
    obs, ratio = _anchor_series(cp, anchors)
    drv["c_prior_scaled"] = drv.pm25_prior * ratio

    train = drv.merge(obs, on="datetime").dropna(subset=FEATURES + ["pm25_anchor"])
    train["resid"] = train.pm25_anchor - train.c_prior_scaled
    X, y = train[FEATURES], train.resid

    # -- quantile heads (full fit) + sequential-fold OOF for conformal ------
    heads, oof = {}, {}
    fold = np.arange(len(train)) * N_FOLDS // max(len(train), 1)
    for a in (0.05, 0.50, 0.95):
        heads[a] = LGBMRegressor(alpha=a, **LGBM_PARAMS).fit(X, y)
        pred = np.full(len(train), np.nan)
        for k in range(N_FOLDS):
            tr, te = fold != k, fold == k
            if te.sum() == 0 or tr.sum() < 500:
                continue
            m = LGBMRegressor(alpha=a, **LGBM_PARAMS).fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
        oof[a] = pred

    # -- Mondrian conformal factors per (month × 6-h bin) -------------------
    cal = train.assign(q05=oof[0.05], q95=oof[0.95]).dropna(subset=["q05", "q95"])
    cal["stratum"] = (cal.datetime.dt.month.astype(str) + "_"
                      + _hod_bin(cal.datetime.dt.hour).astype(str))
    cal["s_lo"] = cal.q05 - cal.resid          # >0 when obs below q05
    cal["s_hi"] = cal.resid - cal.q95
    qq = 1 - ALPHA / 2
    table = cal.groupby("stratum")[["s_lo", "s_hi"]].quantile(qq)
    glob_lo = float(cal.s_lo.quantile(qq))
    glob_hi = float(cal.s_hi.quantile(qq))

    # -- hourly inference over score years -----------------------------------
    inf = drv[drv.datetime.dt.year.isin(set(cp.score_years))].copy()
    q05 = heads[0.05].predict(inf[FEATURES])
    q50 = heads[0.50].predict(inf[FEATURES])
    q95 = heads[0.95].predict(inf[FEATURES])
    q05, q95 = np.minimum(q05, q50), np.maximum(q95, q50)      # monotone
    strat = (inf.datetime.dt.month.astype(str) + "_"
             + _hod_bin(inf.datetime.dt.hour).astype(str))
    c_lo = strat.map(table.s_lo).fillna(glob_lo).to_numpy()
    c_hi = strat.map(table.s_hi).fillna(glob_hi).to_numpy()
    base = inf.c_prior_scaled.to_numpy()
    T = pd.DataFrame({"datetime": inf.datetime.to_numpy(),
                      "T_q05": base + q05 - np.maximum(c_lo, 0),
                      "T_q50": base + q50,
                      "T_q95": base + q95 + np.maximum(c_hi, 0)})

    # -- sharpening to anchor climatology (before the level anchor) ----------
    if sharpen:
        m_obs = obs.set_index("datetime").pm25_anchor
        tq = T.set_index("datetime").T_q50
        fh = ((m_obs.groupby(m_obs.index.hour).mean() / m_obs.mean())
              / (tq.groupby(tq.index.hour).mean() / tq.mean())).clip(*CLIP_SHARPEN)
        fm = ((m_obs.groupby(m_obs.index.month).mean() / m_obs.mean())
              / (tq.groupby(tq.index.month).mean() / tq.mean())).clip(*CLIP_SHARPEN)
        fac = (T.datetime.dt.hour.map(fh).fillna(1.0)
               * T.datetime.dt.month.map(fm).fillna(1.0)).to_numpy()
        for c in ("T_q05", "T_q50", "T_q95"):
            T[c] = T[c] * fac

    # -- additive per-year level re-anchor to VanD basin ----------------------
    levels = {}
    yr = T.datetime.dt.year
    for y in sorted(set(cp.score_years)):
        L, tile = level_for_year(cp, y)
        sel = (yr == y).to_numpy()
        if sel.sum() == 0:
            continue
        shift = L - float(T.loc[sel, "T_q50"].mean())
        for c in ("T_q05", "T_q50", "T_q95"):
            T.loc[sel, c] = T.loc[sel, c] + shift
        levels[y] = {"L": round(L, 2), "tile": tile, "shift": round(shift, 2)}

    info = {"ratio": round(ratio, 4), "n_train": int(len(train)),
            "anchors": tuple(map(str, anchors)), "levels": levels,
            "driver_source": drv.attrs.get("source", "mixed")}
    return T, info


def _selftest() -> int:
    import pandas as pd
    from .citypack import get
    from .anchors import draws
    cp = get("xichang")
    d = draws(cp)[0]
    T, info = fit_and_build(cp, d.anchors)
    print(f"anchors={info['anchors']} ratio={info['ratio']} n_train={info['n_train']:,}")
    for y, v in info["levels"].items():
        print(f"  {y}: L={v['L']} (tile {v['tile']})  shift={v['shift']:+.2f}")
    ann = T.groupby(T.datetime.dt.year).T_q50.mean().round(2)
    print("annual T_q50 means:", ann.to_dict())
    width = float((T.T_q95 - T.T_q05).mean())
    neg = float((T.T_q50 < 0).mean())
    # diurnal-shape sanity vs the ANCHOR climatology (in-sample by design — this
    # checks the sharpening plumbing, NOT a validation gate)
    obs, _ = _anchor_series(cp, d.anchors)
    oc = obs.set_index("datetime").pm25_anchor
    tq = T.set_index("datetime").T_q50
    r = np.corrcoef(oc.groupby(oc.index.hour).mean(),
                    tq.groupby(tq.index.hour).mean())[0, 1]
    print(f"mean 90% width={width:.1f}  neg-q50 frac={neg:.3f}  "
          f"diurnal corr vs anchor clim={r:+.3f}")
    ok = (abs(np.diff([v["L"] for v in info["levels"].values()])).max() < 50
          and r > 0.8 and neg < 0.05)
    print("T-ANCHOR SELFTEST", "PASS" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
