"""score.py — vault scoring: gates V1–V6b per the FROZEN prereg (+ Amendments 1–2).

⚠ THIS MODULE READS VAULT-STATION PM2.5. Running it on a city OPENS that city's
vault — after the first run, no further protocol amendments are legitimate for
that city. The runner prints an explicit banner with a timestamp.

Gates (docs/transfer_validation_phase0_prereg_2026-06-10.md):
  V1 level     |basin_pred − network_mean| / network_mean      ≤15% / ≤25%
  V2 seasonal  Pearson r, monthly city-mean (pred vs vault)    ≥0.80 / ≥0.60
  V3 diurnal   Pearson r, hour-of-day city-mean climatology    ≥0.70 / ≥0.50
  V4 spatial   Spearman ρ, per-station common-period means     ≥0.40 / ≥0.20
  V5 UQ        cov90 of [pm_q05, pm_q95] at vault obs          [0.85,0.95] / [0.80,0.97]
  V6a          f_sat (rural-floor) vs literature bracket       report-only (Amendment 1)
  V6b          f_reconciling ∈ literature bracket              PASS/FAIL
               f_reconciling = f_input · sd(obs station means) / sd(pred station
               means): the f that would reconcile the predicted cross-station
               spread with the observed one. Biased HIGH by siting noise and
               unmodelled local sources (stated in output).

Binding-vs-report-only per city follows Amendment 2's gate map (citypack role).
"""
from __future__ import annotations

import numpy as np

PM25_CAP = 500.0     # obs sanity cap (project convention)


def _vault_obs(cp, vault_ids):
    """Vault-station hourly obs inside the score window. ⚠ vault read."""
    import pandas as pd
    df = pd.read_parquet(cp.station_parquet(),
                         columns=["datetime_utc", "station_id", "pm25"])
    df = df[df.station_id.isin(list(vault_ids))]
    df["datetime"] = (pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)
                        .dt.tz_localize(None))
    df = df.dropna(subset=["datetime", "pm25"])
    df = df[(df.pm25 > 0) & (df.pm25 < PM25_CAP)]
    df = df[df.datetime.dt.year.isin(set(cp.score_years))]
    return df[["datetime", "station_id", "pm25"]]


def score_draw(cp, draw, T, fields, f_local: float) -> dict:
    """All gate metrics for one anchor draw. Returns a flat dict."""
    import pandas as pd
    from scipy.stats import spearmanr
    from .assembly import predict_at_stations

    obs = _vault_obs(cp, draw.vault)
    pred = predict_at_stations(cp, T, fields, f_local)
    m = obs.merge(pred, on=["datetime", "station_id"], how="inner")
    if len(m) == 0:
        return {"error": "no overlapping (hour, station) rows"}

    out = {"n_pairs": int(len(m)), "n_vault_active": int(m.station_id.nunique())}

    # V1 — level
    net_mean = float(m.pm25.mean())
    out["V1_level_err_pct"] = 100.0 * (float(m.pm_q50.mean()) - net_mean) / net_mean

    # V2 — seasonal (monthly city-mean, common months)
    mm = m.set_index("datetime").groupby(pd.Grouper(freq="MS"))[["pm25", "pm_q50"]].mean().dropna()
    out["V2_seasonal_r"] = (float(np.corrcoef(mm.pm25, mm.pm_q50)[0, 1])
                            if len(mm) >= 6 else np.nan)
    out["V2_n_months"] = int(len(mm))

    # V3 — diurnal climatology
    hh = m.groupby(m.datetime.dt.hour)[["pm25", "pm_q50"]].mean()
    out["V3_diurnal_r"] = float(np.corrcoef(hh.pm25, hh.pm_q50)[0, 1])

    # V4 — spatial (common-period station means: each station's own hours,
    # predicted at exactly those hours — period bias cancels per station)
    st = m.groupby("station_id")[["pm25", "pm_q50"]].mean()
    if len(st) >= 4:
        rho, _ = spearmanr(st.pm25, st.pm_q50)
        out["V4_spatial_rho"] = float(rho)
    else:
        out["V4_spatial_rho"] = np.nan
    out["V4_n_stations"] = int(len(st))

    # V5 — UQ coverage
    out["V5_cov90"] = float(((m.pm25 >= m.pm_q05) & (m.pm25 <= m.pm_q95)).mean())
    out["V5_mean_width"] = float((m.pm_q95 - m.pm_q05).mean())

    # V6b — reconciling f from cross-station spread (noise-inflated, see header)
    sd_obs, sd_pred = float(st.pm25.std()), float(st.pm_q50.std())
    out["V6b_f_reconciling"] = (f_local * sd_obs / sd_pred if sd_pred > 0 else np.nan)
    return out


def verdict(cp, per_draw) -> dict:
    """PASS/PARTIAL/FAIL per gate, honouring the FROZEN aggregation rule (§4):
    PASS = median meets PASS threshold AND no draw falls below the PARTIAL floor;
    PARTIAL = median meets the PARTIAL floor; else FAIL. Report-only gates per
    the Amendment-2 binding map are labelled, not judged."""
    binding = {
        "primary":          {"V1", "V2", "V3", "V5", "V6b"},
        "secondary":        {"V4", "V5"},
        "negative_control": {"V4"},
    }.get(cp.role, set())

    def grade(gate, vals, ok_fn, part_fn):
        tag = "BINDING" if gate in binding else "report"
        vals = np.asarray(vals, dtype=float)
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            return f"{tag}: n/a"
        med = float(np.median(vals))
        if ok_fn(med) and all(part_fn(v) for v in vals):
            return f"{tag}: PASS"
        if part_fn(med):
            return f"{tag}: PARTIAL"
        return f"{tag}: FAIL"

    v = {}
    e = per_draw["V1_level_err_pct"].abs()
    v["V1"] = grade("V1", e, lambda x: x <= 15, lambda x: x <= 25)
    v["V2"] = grade("V2", per_draw["V2_seasonal_r"],
                    lambda x: x >= 0.80, lambda x: x >= 0.60)
    v["V3"] = grade("V3", per_draw["V3_diurnal_r"],
                    lambda x: x >= 0.70, lambda x: x >= 0.50)
    rho_med = float(per_draw["V4_spatial_rho"].median())
    if cp.role == "negative_control":
        v["V4"] = ("BINDING: FAIL-AS-EXPECTED (specificity OK)" if rho_med < 0.20
                   else "BINDING: UNEXPECTED PASS — gates too weak")
    else:
        v["V4"] = grade("V4", per_draw["V4_spatial_rho"],
                        lambda x: x >= 0.40, lambda x: x >= 0.20)
    v["V5"] = grade("V5", per_draw["V5_cov90"],
                    lambda x: 0.85 <= x <= 0.95, lambda x: 0.80 <= x <= 0.97)
    lo, hi = cp.f_bracket
    v["V6b"] = grade("V6b", per_draw["V6b_f_reconciling"],
                     lambda x: lo <= x <= hi,
                     lambda x: lo - 0.10 <= x <= hi + 0.10)
    return v
