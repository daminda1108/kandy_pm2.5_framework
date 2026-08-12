"""kandy_emission_clock_fit.py — fit the diurnal emission clock e(t) to the holiday
instrument instead of assuming it (W10, 2026-08-06).

THE GAP
-------
e(t) is an EDGAR road-transport temporal profile (Crippa et al. 2020) blended with a
domestic-combustion profile at a 90/10 vehicular share. It is a pure prior: nothing
local has ever constrained it. F.23 showed the holiday instrument corroborates the
vehicular assumption (the holiday effect is 3.67x stronger at rush hours), but it also
flagged a mismatch -- the observed evening peak is LARGER than the morning one and
LATER than e(t) places it.

THE IDEA
--------
A public holiday removes local activity and leaves transboundary transport untouched.
So the holiday-minus-working-day difference AT HOUR h is an estimate of the local
emission contribution at hour h, up to a constant. That difference profile IS the
emission clock, measured rather than assumed:

    e_measured(h) proportional to  mean(resid | holiday, h) - mean(resid | working, h)

Meteorology and season are controlled non-parametrically by differencing each hour
against its own (month x hour x ventilation-quintile) cell mean, exactly as in F.22, so
the comparison is within hour-of-day and cannot manufacture a diurnal shape.

WHAT IS AND IS NOT UPDATED
--------------------------
With ~800 treated sensor-hours spread over 24 bins the measured profile is noisy, so we
do NOT replace e(t) wholesale. We fit a two-parameter correction to the EVENING LOBE
only -- a shift in its centre hour and a change in its amplitude relative to the morning
lobe -- which is exactly what the instrument identifies and no more. The morning lobe,
the night floor and the overall shape stay as the literature prior.

Run:  .venv/Scripts/python.exe scripts/kandy_emission_clock_fit.py
Out:  data/processed/decomp/kandy_emission_clock_fit.{csv,json}
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
TZ_H = 5.5
NBOOT = 4000
SEED = 20260806

from src.stage1_satml.decomp.emission_profile import (        # noqa: E402
    E_TRAFFIC, E_DOMESTIC, VEHICULAR_SHARE, emission_profile)


def poya_dates(y0: int, y1: int) -> set:
    """Full-moon (Poya) public holidays, local date."""
    import ephem
    out, d = set(), ephem.Date(f"{y0}/1/1")
    end = ephem.Date(f"{y1 + 1}/1/1")
    while d < end:
        d = ephem.next_full_moon(d)
        utc = pd.Timestamp(ephem.Date(d).datetime(), tz="UTC")
        out.add((utc + pd.Timedelta(hours=TZ_H)).date())
    return out


FIXED = [(1, 15), (2, 4), (4, 13), (4, 14), (5, 1), (12, 25)]


def load() -> pd.DataFrame:
    d = pd.read_parquet(STG / "dataset_v3_hourly.parquet",
                        columns=["datetime_utc", "pm25_observed", "blh_m", "ws_ms"]
                        if "ws_ms" in pd.read_parquet(
                            STG / "dataset_v3_hourly.parquet").columns
                        else ["datetime_utc", "pm25_observed", "blh_m"])
    d["t"] = pd.to_datetime(d.datetime_utc, utc=True)
    lt = d.t + pd.Timedelta(hours=TZ_H)
    d["hr"] = lt.dt.hour
    d["mon"] = lt.dt.month
    d["date"] = lt.dt.date
    d["dow"] = lt.dt.dayofweek
    d = d.dropna(subset=["pm25_observed", "blh_m"])
    vent = d.blh_m * (d.ws_ms if "ws_ms" in d.columns else 1.0)
    d["vq"] = pd.qcut(vent, 5, labels=False, duplicates="drop")
    return d


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== W10: fitting the emission clock e(t) to the holiday instrument ===")
    d = load()
    y0, y1 = d.t.dt.year.min(), d.t.dt.year.max()
    poya = poya_dates(int(y0), int(y1))
    fx = {dt.date(y, m, dd) for y in range(int(y0), int(y1) + 1) for m, dd in FIXED}
    d["holiday"] = d.date.map(lambda x: x in poya or x in fx)
    # working days only as control: exclude Sundays (partial activity) and holidays
    d["working"] = (~d.holiday) & (d.dow < 6)

    # non-parametric met/season control, identical to F.22
    cell = d.groupby(["mon", "hr", "vq"]).pm25_observed.transform("mean")
    n_in_cell = d.groupby(["mon", "hr", "vq"]).pm25_observed.transform("size")
    d = d[n_in_cell >= 10].copy()
    d["resid"] = d.pm25_observed - cell[d.index]
    print(f"  {len(d):,} sensor-hours {y0}-{y1}; "
          f"{int(d.holiday.sum()):,} on full public holidays")

    # ── the measured clock ────────────────────────────────────────────────────
    rows = []
    for h in range(24):
        g = d[d.hr == h]
        tr, ct = g[g.holiday], g[g.working]
        if len(tr) < 5 or len(ct) < 20:
            rows.append(dict(hr=h, n_treat=len(tr), delta=np.nan)); continue
        rows.append(dict(hr=h, n_treat=int(len(tr)), n_ctrl=int(len(ct)),
                         delta=float(ct.resid.mean() - tr.resid.mean())))
    H = pd.DataFrame(rows)
    # local emission at hour h is the ACTIVITY REMOVED by the holiday: positive delta
    raw = H.delta.to_numpy(dtype=float)
    raw = np.where(np.isfinite(raw), raw, 0.0)
    # circular 3-point smoothing: ~33 treated hours per bin is thin
    sm = np.convolve(np.r_[raw[-2:], raw, raw[:2]], np.ones(3) / 3, mode="same")[2:-2]
    meas = np.clip(sm, 0, None)
    meas = meas / meas.mean() if meas.mean() > 0 else meas

    shipped = emission_profile()
    print("\n   h   n_tr   holiday effect   measured e   shipped e")
    for h in range(24):
        print(f"  {h:>2}  {H.n_treat.iloc[h]:>5}   {raw[h]:>+9.3f}   "
              f"{meas[h]:>9.2f}   {shipped[h]:>9.2f}")

    def lobe_stats(e):
        e = np.asarray(e, float)
        mor = slice(5, 12)                      # 05-11 LT morning window
        eve = slice(15, 23)                     # 15-22 LT evening window
        mh = int(np.argmax(e[mor])) + 5
        eh = int(np.argmax(e[eve])) + 15
        return mh, eh, float(e[eve].max() / e[mor].max())

    m_s, e_s, r_s = lobe_stats(shipped)
    m_m, e_m, r_m = lobe_stats(meas)
    print(f"\n  SHIPPED  morning peak {m_s:02d}:00 | evening peak {e_s:02d}:00 | "
          f"evening/morning {r_s:.2f}")
    print(f"  MEASURED morning peak {m_m:02d}:00 | evening peak {e_m:02d}:00 | "
          f"evening/morning {r_m:.2f}")

    # bootstrap the two quantities the instrument identifies
    rng = np.random.default_rng(SEED)
    idx_t = d.index[d.holiday].to_numpy(); idx_c = d.index[d.working].to_numpy()
    bs_eh, bs_r = [], []
    for _ in range(NBOOT):
        tb = d.loc[rng.choice(idx_t, len(idx_t))]
        cb = d.loc[rng.choice(idx_c, len(idx_c))]
        mt = tb.groupby("hr").resid.mean().reindex(range(24))
        mc = cb.groupby("hr").resid.mean().reindex(range(24))
        v = (mc - mt).to_numpy(dtype=float)
        v = np.where(np.isfinite(v), v, 0.0)
        v = np.convolve(np.r_[v[-2:], v, v[:2]], np.ones(3) / 3, mode="same")[2:-2]
        v = np.clip(v, 0, None)
        if v.max() <= 0:
            continue
        _, eh_b, r_b = lobe_stats(v / v.mean())
        bs_eh.append(eh_b); bs_r.append(r_b)
    eh_lo, eh_hi = np.percentile(bs_eh, [5, 95])
    r_lo, r_hi = np.percentile(bs_r, [5, 95])
    print(f"  bootstrap: evening peak hour {np.median(bs_eh):.0f} "
          f"[{eh_lo:.0f}, {eh_hi:.0f}]   evening/morning {np.median(bs_r):.2f} "
          f"[{r_lo:.2f}, {r_hi:.2f}]")

    # ── the correction: evening lobe only, two parameters ─────────────────────
    shift = int(round(np.median(bs_eh))) - e_s
    ratio_target = float(np.median(bs_r))
    gain = ratio_target / r_s
    # shrink toward the prior in proportion to how loosely the ratio is identified
    width = (r_hi - r_lo) / max(1e-6, ratio_target)
    w = float(np.clip(1.0 / (1.0 + width), 0.0, 1.0))
    gain_applied = 1.0 + w * (gain - 1.0)
    shift_applied = int(round(w * shift))
    print(f"\n  CORRECTION (evening lobe only)")
    print(f"    shift  {shift:+d} h  -> applied {shift_applied:+d} h")
    print(f"    gain   {gain:.3f}    -> applied {gain_applied:.3f}  (shrinkage w={w:.2f})")

    def apply_correction(prof, shift_h, g):
        p = np.asarray(prof, float).copy()
        eve = np.arange(14, 24)
        base = p.copy()
        lobe = base[eve] - base[[2, 3]].mean()          # above the night floor
        lobe = np.clip(lobe, 0, None) * g
        moved = np.roll(np.r_[lobe, np.zeros(24 - len(eve))], shift_h)[:len(eve)] \
            if shift_h else lobe
        p[eve] = base[[2, 3]].mean() + moved
        return p / p.mean()

    e_new_traffic = apply_correction(E_TRAFFIC, shift_applied, gain_applied)
    e_new = VEHICULAR_SHARE * e_new_traffic + (1 - VEHICULAR_SHARE) * E_DOMESTIC
    e_new = e_new / e_new.mean()
    m_n, e_n, r_n = lobe_stats(e_new)
    print(f"  FITTED   morning peak {m_n:02d}:00 | evening peak {e_n:02d}:00 | "
          f"evening/morning {r_n:.2f}")
    print(f"  agreement with the measured clock: r = "
          f"{np.corrcoef(e_new, meas)[0, 1]:.3f} "
          f"(shipped was {np.corrcoef(shipped, meas)[0, 1]:.3f})")
    print(f"  max change vs shipped: {np.abs(e_new - shipped).max():.3f} "
          f"(profile mean is 1 by construction)")

    out = pd.DataFrame({"hour": range(24), "holiday_effect": raw,
                        "e_measured": meas, "e_shipped": shipped, "e_fitted": e_new})
    out.to_csv(DEC / "kandy_emission_clock_fit.csv", index=False)
    (DEC / "kandy_emission_clock_fit.json").write_text(json.dumps({
        "n_treated_hours": int(d.holiday.sum()),
        "shipped": {"morning_peak": m_s, "evening_peak": e_s, "eve_mor_ratio": round(r_s, 3)},
        "measured": {"morning_peak": m_m, "evening_peak": e_m, "eve_mor_ratio": round(r_m, 3),
                     "evening_peak_ci90": [float(eh_lo), float(eh_hi)],
                     "eve_mor_ratio_ci90": [round(float(r_lo), 3), round(float(r_hi), 3)]},
        "correction": {"shift_h_raw": int(shift), "shift_h_applied": int(shift_applied),
                       "gain_raw": round(float(gain), 3),
                       "gain_applied": round(float(gain_applied), 3),
                       "shrinkage_w": round(w, 3)},
        "fitted": {"morning_peak": m_n, "evening_peak": e_n, "eve_mor_ratio": round(r_n, 3)},
        "e_fitted": [round(float(v), 4) for v in e_new],
        "status": ("e(t) moves from an imposed literature prior to a prior with a LOCAL "
                   "observational correction on the one feature the holiday instrument "
                   "identifies: the evening lobe. Morning lobe, night floor and overall "
                   "shape remain the EDGAR prior."),
        "caveats": [
            "~800 treated sensor-hours over 24 bins; the per-hour effect is noisy and is "
            "3-point circularly smoothed before use.",
            "The holiday effect is a LOWER bound on local emission at every hour: sources "
            "with no holiday cycle (cooking, waste burning, road dust) are invisible to it.",
            "Two FECT sensors, both valley/suburban; the clock is assumed spatially uniform.",
            "The correction is shrunk toward the prior in proportion to the width of the "
            "bootstrap interval, so a poorly identified ratio moves e(t) very little."],
    }, indent=1), encoding="utf-8")
    print(f"\nwrote kandy_emission_clock_fit.{{csv,json}}")


if __name__ == "__main__":
    main()
