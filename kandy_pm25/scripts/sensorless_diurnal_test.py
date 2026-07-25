"""sensorless_diurnal_test.py — can the DIURNAL cycle be produced without local sensors?

THE GAP (docs/sensorless_product_scope_2026-07-25.md). A sensorless product exists only
at DAILY scale (Track T-a). The hourly/diurnal shape has never been produced sensorlessly
anywhere in the project: Kandy's comes from a FECT-trained GBM + sharpen_T_diurnal, and
the analogue cities' from fit_and_build(), which trains a residual GBM on the 2 anchor
sensors' HOURLY observations. So "0 sensors" has only ever meant "no sensor
level-anchoring".

OPTION A (this script). Build the within-day shape from SENSOR-FREE inputs only and score
it against each city's HELD-OUT diurnal climatology:

    S(t)  proportional to  e_city(hour) / (BLH(t) * max(|u|(t), u0)) ** gamma

a box-model dilution argument: concentration ~ emission rate / ventilation, where
ventilation = mixing height x wind. Every input is sensor-free — e(t) is the EDGAR
road-transport/domestic profile from the city's source mix (city_config emix), BLH and
wind are ERA5. Normalised to mean 1 within each day, so it carries SHAPE only and the
daily level is untouched (it would come from Track T-a / the satellite anchor).

gamma = 0 is the e(t)-only limit (pure emission timing, no meteorology). gamma is fitted
LEAVE-ONE-CITY-OUT so a city never informs its own exponent — the same discipline as
Track T-a, and what makes the result a genuine sensorless claim at the target.

BASELINE: the shipped 2-sensor model's diurnal r for the same city (its GBM saw
sensors), read from the N=9 validation scorecard. The question is not "is the sensorless
shape perfect" but "how much of the 2-sensor diurnal skill survives with zero sensors".

Out: results/figures/multicity/sensorless_diurnal.{csv,txt}
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xichang_paper_figures as xf

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "figures" / "multicity"
U0 = 0.5                       # m/s floor: ventilation never truly zero
GAMMAS = np.round(np.arange(0.0, 1.01, 0.125), 3)
CITIES = ["medellin", "kathmandu", "chiangmai", "xichang", "bazhou",
          "chandigarh", "baoji", "taian", "yichang"]


def city_tables(city):
    """(obs diurnal climatology from held-out stations, sensor-free driver frame)."""
    xf._setup(city)
    from city_config import cfg, citypack, e_profile
    cp = citypack(city)
    years = list(cfg(city)["years"])

    # ── observed diurnal climatology, ALL stations (they are held out by construction:
    #    nothing here is fed to the sensorless shape) ──────────────────────────────
    obs = pd.concat([xf._obs(y) for y in years], ignore_index=True)
    obs["h"] = obs.loct.dt.hour
    obs_d = obs.groupby("h").pm25.mean()
    obs_d = obs_d / obs_d.mean()                      # unit-mean shape

    # ── sensor-free drivers: ERA5 BLH + wind, and the EDGAR e(t) source-mix prior ──
    from src.transfer_validation import drivers
    b = drivers.blh(cp); w = drivers.era5_winds(cp)
    if b is None or w is None:
        return None
    src = f"{b.attrs.get('source','?')}|{w.attrs.get('source','?')}"
    if "PROXY" in src:            # station-derived BLH/wind would NOT be sensor-free
        return None
    d = b.merge(w, on="datetime", how="inner")
    d["datetime"] = pd.to_datetime(d.datetime)
    d = d.dropna(subset=["blh_m", "u10", "v10"])
    d["loct"] = d.datetime.dt.tz_localize("UTC").dt.tz_convert(xf.TZ)
    d["h"] = d.loct.dt.hour
    d["day"] = d.loct.dt.floor("D")
    d["wspd"] = np.hypot(d.u10, d.v10)
    e = e_profile(city)                                # 24-vector, mean 1, sensor-free
    d["e"] = e[d.h.to_numpy()]
    return obs_d, d, src


def shape_for_gamma(d, gamma):
    """Unit-mean-per-day sensor-free shape -> its diurnal climatology (unit mean)."""
    vent = (np.maximum(d.blh_m.to_numpy(), 50.0)
            * np.maximum(d.wspd.to_numpy(), U0)) ** gamma
    raw = d.e.to_numpy() / vent
    s = pd.Series(raw, index=d.index)
    # normalise WITHIN each day: this carries shape only, never the daily level
    s = s / s.groupby(d.day.to_numpy()).transform("mean")
    clim = s.groupby(d.h.to_numpy()).mean()
    return clim / clim.mean()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # baseline: the shipped 2-sensor diurnal r from the N=9 scorecard
    sc = pd.read_csv(OUT / "validation_scorecard.csv")
    base = {}
    for _, r in sc.iterrows():
        key = str(r.get("city", "")).lower()
        base[key] = float(r.get("diurnal", np.nan))

    data = {}
    for c in CITIES:
        try:
            t = city_tables(c)
        except Exception as ex:
            print(f"  {c}: skip ({str(ex)[:70]})"); continue
        if t is None:
            print(f"  {c}: skip (no sensor-free BLH/wind — would need station proxies)")
            continue
        data[c] = t
        print(f"  {c}: obs+drivers ok ({t[2]})")

    # ── LOCO gamma: pick gamma on the OTHER cities, evaluate on the held-out one ──
    rows = []
    for c in data:
        others = [o for o in data if o != c]
        best_g, best_score = None, -9
        for g in GAMMAS:
            rs = []
            for o in others:
                obs_d, d, _ = data[o]
                s = shape_for_gamma(d, g)
                idx = obs_d.index.intersection(s.index)
                if len(idx) >= 20:
                    rs.append(np.corrcoef(obs_d.loc[idx], s.loc[idx])[0, 1])
            m = float(np.nanmean(rs)) if rs else -9
            if m > best_score:
                best_score, best_g = m, g
        obs_d, d, _ = data[c]
        s = shape_for_gamma(d, best_g)
        idx = obs_d.index.intersection(s.index)
        r_loco = float(np.corrcoef(obs_d.loc[idx], s.loc[idx])[0, 1])
        r_e_only = float(np.corrcoef(obs_d.loc[idx],
                                     shape_for_gamma(d, 0.0).loc[idx])[0, 1])
        # in-sample best gamma for this city (upper bound, NOT a sensorless claim)
        r_oracle = max(float(np.corrcoef(obs_d.loc[idx],
                                        shape_for_gamma(d, g).loc[idx])[0, 1])
                       for g in GAMMAS)
        rows.append(dict(city=c, gamma_loco=best_g, r_sensorless_loco=round(r_loco, 3),
                         r_e_only=round(r_e_only, 3), r_oracle_gamma=round(r_oracle, 3),
                         r_2sensor_shipped=base.get(c, np.nan)))
    t = pd.DataFrame(rows).sort_values("r_sensorless_loco", ascending=False)
    t.to_csv(OUT / "sensorless_diurnal.csv", index=False)

    L = ["OPTION A — can the DIURNAL cycle be built with ZERO local sensors?",
         "=" * 78,
         "shape = e_city(hour) / (BLH * max(|u|,0.5))**gamma, unit-mean per day.",
         "All inputs sensor-free (EDGAR source-mix e(t) + ERA5). gamma fitted",
         "LEAVE-ONE-CITY-OUT so no city informs its own exponent.",
         "Scored vs each city's observed diurnal climatology (all stations).", "",
         f"{'city':<12}{'gam':>5}{'sensorless':>12}{'e(t) only':>11}{'oracle g':>10}{'2-sensor':>10}",
         "-" * 78]
    for _, r in t.iterrows():
        b = r.r_2sensor_shipped
        L.append(f"{r.city:<12}{r.gamma_loco:5.3f}{r.r_sensorless_loco:12.3f}"
                 f"{r.r_e_only:11.3f}{r.r_oracle_gamma:10.3f}"
                 f"{(f'{b:.2f}' if np.isfinite(b) else 'n/a'):>10}")
    ok = t.r_sensorless_loco >= 0.60
    L += ["", f"cities with sensorless diurnal r >= 0.60: {int(ok.sum())} / {len(t)}",
          f"median sensorless r = {t.r_sensorless_loco.median():.3f}   "
          f"median e(t)-only r = {t.r_e_only.median():.3f}",
          f"median shipped 2-sensor r = {np.nanmedian(t.r_2sensor_shipped):.3f}"]
    verdict = ("VIABLE — a sensorless hourly product is available now (Option A)"
               if ok.mean() >= 0.6 else
               "NOT VIABLE as-is — the sensor-free box model does not recover the "
               "diurnal cycle;\n         the 2 sensors are buying real diurnal "
               "information. Option B (panel-learned\n         hourly shape) is the "
               "remaining route.")
    L += ["", f"VERDICT: {verdict}"]
    txt = "\n".join(L)
    (OUT / "sensorless_diurnal.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)


if __name__ == "__main__":
    main()
