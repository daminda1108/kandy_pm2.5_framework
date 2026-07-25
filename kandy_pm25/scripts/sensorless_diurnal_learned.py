"""sensorless_diurnal_learned.py — OPTION B: can a PANEL-LEARNED model produce the
diurnal cycle with zero local sensors?

Context. Option A (sensorless_diurnal_test.py) showed a fixed box-model shape
    e(hour) / (BLH * |u|)**gamma
recovers only part of the diurnal cycle: LOCO median r = 0.412 against a shipped
2-sensor median of 0.708. Two diagnostics from that run motivate this one:
  * e(t) ALONE is useless (median r 0.058, negative at several cities) — emission timing
    does not explain the cycle;
  * the ventilation term carries the signal (gamma 0.5-0.75 always selected), and the
    in-sample "oracle gamma" was barely better than the LOCO gamma, so the limitation is
    the FUNCTIONAL FORM, not the fitting.
A learned function of the same sensor-free drivers therefore has real headroom. That is
Option B, and this is its feasibility test.

Design.
  target   : observed hourly PM2.5 / that day's observed mean  (unit-mean-per-day SHAPE,
             so the daily level stays the job of Track T-a / the satellite anchor)
  features : ALL sensor-free — hour sin/cos, e(hour) from the EDGAR source mix, BLH and
             wind and t2m, their ratios to the same day's mean (the relative mixing state,
             which is what a box model is groping at), ventilation index, day-of-year
             sin/cos, plus city descriptors (latitude, traffic share) so the model can
             generalise across regimes
  model    : LightGBM
  validation: LEAVE-ONE-CITY-OUT. Train on the others, predict the held-out city's hourly
             shape, score its diurnal climatology against observations. No city informs
             its own prediction — the same discipline as Track T-a.

Scale caveat, stated up front: the 199-city panel met is DAILY (panel_daily_met.parquet,
289,688 city-days), which is exactly why Track T-a is daily. Hourly panel training would
need a new hourly ERA5 pull for the panel. This test therefore runs on the cities that
already have sensor-free HOURLY drivers, so LOCO has few training cities. It answers
"does a learned form beat the fixed one", which is what decides whether the bigger pull
is worth doing.

Out: results/figures/multicity/sensorless_diurnal_learned.{csv,txt}
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xichang_paper_figures as xf
from sensorless_diurnal_test import CITIES, U0, shape_for_gamma

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "figures" / "multicity"

FEATURES = ["h_sin", "h_cos", "e_t", "blh", "log_blh", "wspd", "t2m",
            "blh_rel", "wspd_rel", "vent", "log_vent", "vent_rel",
            "doy_sin", "doy_cos", "lat", "traffic_share"]


def build_city(city):
    """Hourly design matrix + unit-mean-per-day observed shape, sensor-free features."""
    xf._setup(city)
    from city_config import cfg, citypack, e_profile, CITIES as CC
    cp = citypack(city)
    years = list(cfg(city)["years"])
    from src.transfer_validation import drivers
    b = drivers.blh(cp); w = drivers.era5_winds(cp)
    if b is None or w is None:
        return None
    if "PROXY" in f"{b.attrs.get('source','')}{w.attrs.get('source','')}":
        return None                      # station-derived met would not be sensor-free
    d = b.merge(w, on="datetime", how="inner")
    d["datetime"] = pd.to_datetime(d.datetime)
    d = d.dropna(subset=["blh_m", "u10", "v10", "t2m"])
    d["loct"] = d.datetime.dt.tz_localize("UTC").dt.tz_convert(xf.TZ)

    obs = pd.concat([xf._obs(y) for y in years], ignore_index=True)
    obs["loct"] = obs.loct.dt.floor("h")
    o = obs.groupby("loct").pm25.mean().rename("pm").reset_index()   # network mean/hour
    d["loct"] = d.loct.dt.floor("h")
    m = d.merge(o, on="loct", how="inner")
    if len(m) < 2000:
        return None
    m["day"] = m.loct.dt.floor("D")
    # target: unit-mean-per-day observed shape (drop days with too few hours)
    cnt = m.groupby("day").pm.transform("size")
    m = m[cnt >= 18].copy()
    m["y"] = m.pm / m.groupby("day").pm.transform("mean")
    m = m[np.isfinite(m.y) & (m.y > 0) & (m.y < 6)]

    h = m.loct.dt.hour.to_numpy()
    e = e_profile(city)
    m["h_sin"] = np.sin(2 * np.pi * h / 24); m["h_cos"] = np.cos(2 * np.pi * h / 24)
    m["e_t"] = e[h]
    m["blh"] = np.maximum(m.blh_m, 50.0); m["log_blh"] = np.log(m.blh)
    m["wspd"] = np.maximum(np.hypot(m.u10, m.v10), U0)
    m["vent"] = m.blh * m.wspd; m["log_vent"] = np.log(m.vent)
    for c in ("blh", "wspd", "vent"):
        m[f"{c}_rel"] = m[c] / m.groupby("day")[c].transform("mean")
    doy = m.loct.dt.dayofyear.to_numpy()
    m["doy_sin"] = np.sin(2 * np.pi * doy / 365); m["doy_cos"] = np.cos(2 * np.pi * doy / 365)
    m["lat"] = float(CC[city]["cen"][0])
    m["traffic_share"] = float(CC[city]["emix"].get("traffic", 0.0))
    m["h"] = h
    m["city"] = city
    return m[FEATURES + ["y", "h", "city"]].dropna()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from lightgbm import LGBMRegressor
    frames, boxr = {}, {}
    a = pd.read_csv(OUT / "sensorless_diurnal.csv").set_index("city")
    for c in CITIES:
        try:
            f = build_city(c)
        except Exception as ex:
            print(f"  {c}: skip ({str(ex)[:60]})"); continue
        if f is None or len(f) < 2000:
            print(f"  {c}: skip (no sensor-free hourly drivers / too few matched hours)")
            continue
        frames[c] = f
        boxr[c] = float(a.r_sensorless_loco.get(c, np.nan))
        print(f"  {c}: {len(f):,} matched hours")
    if len(frames) < 3:
        print("too few cities for LOCO"); return

    sc = pd.read_csv(OUT / "validation_scorecard.csv")
    base = {str(r.get("city", "")).lower(): float(r.get("diurnal", np.nan))
            for _, r in sc.iterrows()}

    rows = []
    for c in frames:
        tr = pd.concat([frames[o] for o in frames if o != c], ignore_index=True)
        te = frames[c]
        mdl = LGBMRegressor(n_estimators=500, learning_rate=0.05, num_leaves=31,
                            min_child_samples=40, subsample=0.8, colsample_bytree=0.8,
                            verbose=-1)
        mdl.fit(tr[FEATURES], tr.y)
        te = te.assign(pred=mdl.predict(te[FEATURES]))
        # score the DIURNAL CLIMATOLOGY (what the product shows)
        obs_d = te.groupby("h").y.mean(); obs_d /= obs_d.mean()
        prd_d = te.groupby("h").pred.mean(); prd_d /= prd_d.mean()
        r = float(np.corrcoef(obs_d, prd_d)[0, 1])
        # amplitude fidelity: does it reproduce the swing, or flatten it?
        amp_o = float(obs_d.max() - obs_d.min()); amp_p = float(prd_d.max() - prd_d.min())
        rows.append(dict(city=c, n_hours=len(te), r_learned_loco=round(r, 3),
                         r_boxmodel_loco=round(boxr.get(c, np.nan), 3),
                         amp_obs=round(amp_o, 3), amp_pred=round(amp_p, 3),
                         amp_ratio=round(amp_p / amp_o, 2) if amp_o else np.nan,
                         r_2sensor_shipped=base.get(c, np.nan)))
    t = pd.DataFrame(rows).sort_values("r_learned_loco", ascending=False)
    t.to_csv(OUT / "sensorless_diurnal_learned.csv", index=False)

    L = ["OPTION B — PANEL-LEARNED sensorless diurnal (LightGBM, leave-one-city-out)",
         "=" * 82,
         "target = observed hourly / that day's mean (unit-mean SHAPE; level stays",
         "Track T-a's job). All features sensor-free. No city informs its own prediction.",
         f"training cities per fold: {len(frames)-1}  (panel met is DAILY, so hourly",
         "panel training would need a new 199-city hourly ERA5 pull — see docstring)", "",
         f"{'city':<12}{'hours':>9}{'LEARNED':>9}{'box A':>8}{'ampl.':>8}{'2-sensor':>10}",
         "-" * 82]
    for _, r in t.iterrows():
        b = r.r_2sensor_shipped
        L.append(f"{r.city:<12}{r.n_hours:9,d}{r.r_learned_loco:9.3f}"
                 f"{r.r_boxmodel_loco:8.3f}{r.amp_ratio:8.2f}"
                 f"{(f'{b:.2f}' if np.isfinite(b) else 'n/a'):>10}")
    med_l = t.r_learned_loco.median(); med_b = t.r_boxmodel_loco.median()
    med_s = np.nanmedian(t.r_2sensor_shipped)
    L += ["", f"median  LEARNED {med_l:.3f}  |  box model {med_b:.3f}  |  "
              f"shipped 2-sensor {med_s:.3f}",
          f"cities with learned r >= 0.60: {int((t.r_learned_loco>=0.60).sum())}/{len(t)}",
          f"median amplitude ratio (pred/obs swing): {t.amp_ratio.median():.2f}"]
    gain = med_l - med_b
    closed = (med_l - med_b) / (med_s - med_b) if np.isfinite(med_s) and med_s > med_b else np.nan
    L += ["", f"gain over the fixed box model: {gain:+.3f}"
              + (f"   ({closed:.0%} of the box->2-sensor gap closed)"
                 if np.isfinite(closed) else "")]
    if med_l >= 0.60 and gain > 0.05:
        v = ("VIABLE — a learned sensorless diurnal is worth the full panel pull "
             "(199-city hourly ERA5).")
    elif gain > 0.05:
        v = ("PARTIAL — learning beats the fixed form but still falls short of the "
             "2-sensor cycle.\n         Justifies the panel pull as a research bet, "
             "not a product change yet.")
    else:
        v = ("NOT VIABLE — learning does not beat the fixed box model on these cities. "
             "The diurnal\n         cycle is carrying local information the sensor-free "
             "drivers do not contain; the 2\n         sensors are buying it. Record as a "
             "null and keep the disclosed 2-sensor product.")
    L += ["", f"VERDICT: {v}"]
    txt = "\n".join(L)
    (OUT / "sensorless_diurnal_learned.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)


if __name__ == "__main__":
    main()
