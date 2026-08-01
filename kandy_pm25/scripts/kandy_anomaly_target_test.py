"""kandy_anomaly_target_test.py — A2: does an ANOMALY target remove the amplitude
damping at its cause, and can the climatology be made sensorless? (2026-08-01)

THE PATCH THIS IS AIMED AT
--------------------------
The lag-free anchor GBM regresses to the mean, so it reproduces the right diurnal PHASE
with a shrunken swing. Production repairs that AFTER the fact:

    sharpen_T_diurnal.py   maps T(t)'s climatology onto the OBSERVED FECT climatology
    sharpen_to_locked      does the same for the extension tier (gotcha #53)

Both are post-hoc corrections for a defect in the training target. If the model predicts
the DEPARTURE from a climatology instead of the level, the climatology carries the
amplitude and there is nothing left to damp — the patch family disappears at its cause.

AND A SECOND QUESTION, WHICH IS THE ONE THAT MATTERS FOR THE PAPER
------------------------------------------------------------------
A4 (the audit's open disclosure item) is that the shipped diurnal/seasonal SHAPE depends
on the two local FECT sensors twice over: the GBM trains on the FECT residual target, and
the sharpening maps onto the observed FECT climatology. Moving to an anomaly target does
NOT by itself fix that — it just relocates the dependence into the climatology.

It fixes it only if the climatology itself is sensorless. So two anomaly variants are
tested:

    clim_FECT         (month, hour) climatology from the TRAIN-period FECT record
    clim_SENSORLESS   panel-donor solar-time diurnal shape (24 h, cross-city, no Kandy
                      sensor) x a seasonal shape taken from the driver prior

If the sensorless climatology performs comparably, the shape claim stops depending on the
local sensors and A4 closes on evidence rather than on wording.

PROTOCOL — clean temporal split (gotcha #68)
--------------------------------------------
Production T(t) is trained AND sharpened on FECT, so scoring it against FECT is in-sample.
Everything here trains on <= 2022 and is scored on 2023 hours it has never seen. The
climatologies are also computed on the training period only.

Run:  .venv/Scripts/python.exe scripts/kandy_anomaly_target_test.py
Out:  data/processed/stage1_v3/training/anomaly_target_test.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

STG = REPO / "data" / "processed" / "stage1_v3"
DONOR = REPO / "results" / "figures" / "multicity" / "panel_donor_shapes.csv"
OUT = STG / "training" / "anomaly_target_test.csv"

TRAIN_END = 2022          # clean split: train <= 2022, score 2023
TEST_YEAR = 2023
TZ_OFFSET_H = 5.5         # Asia/Colombo, for local-hour climatologies

FEATURES = ["c_prior_scaled", "blh_m", "u10", "v10", "wind_speed_10m", "t2m", "d2m",
            "tp", "ssr_j_m2", "solar_zenith_angle",
            "hour_of_day_sin", "hour_of_day_cos", "dow_sin", "dow_cos",
            "doy_sin", "doy_cos"]
LGBM = dict(objective="regression", learning_rate=0.05, num_leaves=63,
            n_estimators=600, min_child_samples=20, subsample=0.8,
            colsample_bytree=0.8, verbose=-1, n_jobs=-1)


def load() -> pd.DataFrame:
    d = pd.read_parquet(STG / "dataset_v3_hourly.parquet")
    d["t"] = pd.to_datetime(d.datetime_utc, utc=True)
    lt = d.t + pd.Timedelta(hours=TZ_OFFSET_H)
    d["lh"] = lt.dt.hour
    d["mo"] = lt.dt.month
    d["yr"] = lt.dt.year
    d = d.dropna(subset=["pm25_observed"])
    keep = [c for c in FEATURES if c in d.columns]
    miss = set(FEATURES) - set(keep)
    if miss:
        print(f"  NOTE: features absent from the dataset, dropped: {sorted(miss)}")
    d = d.dropna(subset=["c_prior_scaled"])
    return d, keep


def clim_from_obs(tr: pd.DataFrame) -> pd.DataFrame:
    """(month, local hour) climatology of the observed record — TRAIN period only."""
    c = tr.groupby(["mo", "lh"]).pm25_observed.mean().rename("clim").reset_index()
    # fill any empty cell from the month mean, then the global mean
    full = pd.MultiIndex.from_product([range(1, 13), range(24)], names=["mo", "lh"])
    c = c.set_index(["mo", "lh"]).reindex(full)
    by_month = tr.groupby("mo").pm25_observed.mean()
    fill = pd.Series(by_month.reindex(c.index.get_level_values("mo")).to_numpy(),
                     index=c.index)
    c["clim"] = c.clim.fillna(fill).fillna(float(tr.pm25_observed.mean()))
    return c.reset_index()


def clim_sensorless(tr: pd.DataFrame) -> pd.DataFrame:
    """Panel-donor diurnal shape x a driver-derived seasonal shape, scaled to the
    train-period MEAN LEVEL only.

    The level is already sensorless in production (the VanD area anchor), so using the
    train mean here is consistent with what ships. What matters is that neither the
    DIURNAL nor the SEASONAL shape uses a Kandy sensor: the diurnal comes from the
    cross-city panel donor (solar time), the seasonal from the chemistry prior.
    """
    dn = pd.read_csv(DONOR)
    diur = dn["solar"].to_numpy(float)
    diur = diur / diur.mean()
    seas = tr.groupby("mo").c_prior_scaled.mean()
    seas = (seas / seas.mean()).reindex(range(1, 13)).interpolate(
        limit_direction="both").fillna(1.0)
    lvl = float(tr.pm25_observed.mean())
    rows = [{"mo": m, "lh": h, "clim": lvl * float(seas.loc[m]) * float(diur[h])}
            for m in range(1, 13) for h in range(24)]
    return pd.DataFrame(rows)


def sharpen(pred: np.ndarray, mo, lh, obs_clim: pd.DataFrame) -> np.ndarray:
    """Production-style post-hoc amplitude sharpening: map the prediction's own
    (month, hour) climatology onto the observed one, preserving the overall mean."""
    df = pd.DataFrame({"mo": mo, "lh": lh, "p": pred})
    pc = df.groupby(["mo", "lh"]).p.mean().rename("pclim").reset_index()
    j = df.merge(pc, on=["mo", "lh"], how="left").merge(obs_clim, on=["mo", "lh"], how="left")
    ratio = np.where(j.pclim.to_numpy() > 1e-6,
                     j.clim.to_numpy() / j.pclim.to_numpy(), 1.0)
    out = pred * ratio
    m = out.mean()
    return out * (pred.mean() / m) if m > 0 else out


def score(name, obs, pred, mo, lh) -> dict:
    ok = np.isfinite(obs) & np.isfinite(pred)
    o, p = obs[ok], pred[ok]
    d = pd.DataFrame({"o": o, "p": p, "lh": lh[ok], "mo": mo[ok]})
    di = d.groupby("lh")[["o", "p"]].mean()
    se = d.groupby("mo")[["o", "p"]].mean()
    return {"variant": name, "n": int(len(o)),
            "rmse": round(float(np.sqrt(np.mean((p - o) ** 2))), 3),
            "r": round(float(np.corrcoef(o, p)[0, 1]), 3),
            "diurnal_r": round(float(np.corrcoef(di.o, di.p)[0, 1]), 3),
            "diurnal_swing_obs": round(float(di.o.max() - di.o.min()), 2),
            "diurnal_swing_pred": round(float(di.p.max() - di.p.min()), 2),
            "swing_ratio": round(float((di.p.max() - di.p.min()) /
                                       max(di.o.max() - di.o.min(), 1e-6)), 3),
            "seasonal_r": round(float(np.corrcoef(se.o, se.p)[0, 1]), 3),
            "level_bias_pct": round(100 * float(p.mean() / o.mean() - 1), 2)}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== A2: anomaly target vs post-hoc sharpening (clean split) ===")
    d, feats = load()
    tr = d[d.yr <= TRAIN_END]
    te = d[d.yr == TEST_YEAR]
    print(f"  train <= {TRAIN_END}: {len(tr):,} rows | test {TEST_YEAR}: {len(te):,} rows")
    if len(te) < 500:
        raise SystemExit("test year too thin")

    Xtr, Xte = tr[feats].astype(float), te[feats].astype(float)
    ytr = tr.pm25_observed.to_numpy(float)
    obs = te.pm25_observed.to_numpy(float)
    mo, lh = te.mo.to_numpy(), te.lh.to_numpy()

    rows = []
    # (a) direct level prediction — shows the damping
    m = LGBMRegressor(**LGBM).fit(Xtr, ytr)
    raw = m.predict(Xte)
    rows.append(score("a. direct GBM (no sharpening)", obs, raw, mo, lh))

    # (b) production-style: direct + post-hoc sharpening to the TRAIN observed climatology
    cobs = clim_from_obs(tr)
    rows.append(score("b. direct + post-hoc sharpen (production-style)", obs,
                      sharpen(raw, mo, lh, cobs), mo, lh))

    # (c) anomaly target, FECT-derived climatology
    ctr = tr.merge(cobs, on=["mo", "lh"], how="left").clim.to_numpy(float)
    cte = te.merge(cobs, on=["mo", "lh"], how="left").clim.to_numpy(float)
    ma = LGBMRegressor(**LGBM).fit(Xtr, ytr - ctr)
    rows.append(score("c. ANOMALY target, FECT climatology", obs,
                      cte + ma.predict(Xte), mo, lh))

    # (d) anomaly target, SENSORLESS climatology (panel diurnal x driver seasonal)
    csl = clim_sensorless(tr)
    ctr2 = tr.merge(csl, on=["mo", "lh"], how="left").clim.to_numpy(float)
    cte2 = te.merge(csl, on=["mo", "lh"], how="left").clim.to_numpy(float)
    ms = LGBMRegressor(**LGBM).fit(Xtr, ytr - ctr2)
    rows.append(score("d. ANOMALY target, SENSORLESS climatology", obs,
                      cte2 + ms.predict(Xte), mo, lh))

    # (e) both: anomaly target AND post-hoc sharpening — the combination production
    # does not currently use, and the one the other four rows point at
    rows.append(score("e. ANOMALY (FECT clim) + post-hoc sharpen", obs,
                      sharpen(cte + ma.predict(Xte), mo, lh, cobs), mo, lh))

    r = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print("\n" + r.to_string(index=False))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r.to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print("\nread: swing_ratio ~1 means the amplitude is right WITHOUT a post-hoc patch;")
    print("      (d) comparable to (c) would mean the shape no longer needs the local sensors.")


if __name__ == "__main__":
    main()
