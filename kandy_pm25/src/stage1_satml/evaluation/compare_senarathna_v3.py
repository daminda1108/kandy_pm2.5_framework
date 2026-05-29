"""
compare_senarathna_v3.py — v3 LightGBM predictions vs Senarathna et al. 2024
(KOALA Kandy, NIFS station, January–December 2019).

Senarathna et al. 2024 (CJS 53(2):197-206) reports:
  - Hourly diurnal (Table 2): bimodal with peaks at 06:00–07:00 LT (morning rush
    + RH growth) and 18:00–19:00 LT (evening rush). Midday valley at 12:00–13:00 LT.
  - Weekly (Table 1): Sunday lowest (−1.40 µg/m³ vs Mon 24.78); Wed + Fri highest.
  - Monthly (Table 3): March peak (~34.9 µg/m³), April second; December lowest (~17.8).
  - Annual mean 2019 ≈ 24.5 µg/m³ at NIFS Kandy.

v3 predictions are at FECT sub-urban-highland (Akurana 1538 m + Hantana TR4
1698 m), expected ~10 µg/m³ below KOALA NIFS (valley floor). Compare:
  1. Pattern SHAPE (relative diurnal/weekly/monthly cycle) — should match if
     RECAP captures Kandy regime dynamics.
  2. Pattern PHASE (timing of peaks/troughs) — should match.
  3. Pattern AMPLITUDE (offset from b_FECT). Predicted = observed minus
     ~9 (Akurana) or ~14 (Hantana) µg/m³.

Outputs:
  data/processed/stage1_v3/training/senarathna_diurnal_comparison.csv
  data/processed/stage1_v3/training/senarathna_monthly_comparison.csv
  data/processed/stage1_v3/training/senarathna_weekly_comparison.csv
  results/figures/stage1_v3/diurnal_v3_vs_senarathna.png+pdf
  results/figures/stage1_v3/monthly_v3_vs_senarathna.png+pdf
  results/figures/stage1_v3/weekly_v3_vs_senarathna.png+pdf
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

_TRAIN = HERE / "data" / "processed" / "stage1_v3" / "training"
PRED_PATHS = {
    "lgbm": _TRAIN / "predictions_lomo_v3_lgbm.parquet",
    "lgbm_lagfree": _TRAIN / "predictions_lomo_v3_lgbm_lagfree.parquet",
    "blend": _TRAIN / "predictions_blend_v3.parquet",
}
# Column holding the q50 PM2.5-scale point prediction, per source
PRED_COL = {"lgbm": "pm25_pred_q50", "lgbm_lagfree": "pm25_pred_q50", "blend": "q50_blend"}
OUT_DIR = HERE / "data" / "processed" / "stage1_v3" / "training"
FIG_DIR = HERE / "results" / "figures" / "stage1_v3"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── Senarathna 2024 Table 2 — hourly variation of PM2.5 (µg/m³, Kandy NIFS 2019) ──
#   Reference: 00:00 mean = 22.18 µg/m³. Listed Coef = µg/m³ increment above ref.
SENARATHNA_BASELINE_00 = 22.18
SENARATHNA_HOURLY_COEF = {
    0: 0.0, 1: -0.25, 2: -0.20, 3: 0.01, 4: 2.31, 5: 7.03, 6: 11.99, 7: 13.70,
    8: 8.11, 9: 2.17, 10: -0.54, 11: -2.03, 12: -2.84, 13: -2.99, 14: -1.97,
    15: 1.74, 16: 1.35, 17: 3.41, 18: 9.74, 19: 8.65, 20: 5.56, 21: 3.24,
    22: 1.70, 23: 0.79,
}
SENARATHNA_HOURLY = {h: SENARATHNA_BASELINE_00 + c
                     for h, c in SENARATHNA_HOURLY_COEF.items()}

# ── Senarathna Table 3 — monthly variation (µg/m³, December = 17.76 ref) ──
SENARATHNA_MONTHLY_REF_DEC = 17.76
SENARATHNA_MONTHLY_COEF = {
    1: 8.37, 2: 9.16, 3: 17.11, 4: 15.74, 5: 11.51, 6: 5.34,  # approx from paper
    7: 6.06, 8: 6.59, 9: 5.49, 10: 7.97, 11: 8.95, 12: 0.0,
}
SENARATHNA_MONTHLY = {m: SENARATHNA_MONTHLY_REF_DEC + c
                      for m, c in SENARATHNA_MONTHLY_COEF.items()}

# ── Senarathna Table 1 — day-of-week (µg/m³, Monday = 24.78 ref). 0 = Monday ──
SENARATHNA_WEEKLY_REF_MON = 24.78
SENARATHNA_WEEKLY_COEF = {
    0: 0.0,    # Mon
    1: 0.105,  # Tue
    2: 1.296,  # Wed
    3: 0.782,  # Thu
    4: 1.260,  # Fri
    5: 0.300,  # Sat
    6: -1.395, # Sun
}
SENARATHNA_WEEKLY = {d: SENARATHNA_WEEKLY_REF_MON + c
                     for d, c in SENARATHNA_WEEKLY_COEF.items()}

DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]


def main(year: int | None = None, source: str = "lgbm"):
    p = pd.read_parquet(PRED_PATHS[source])
    p["datetime_utc"] = pd.to_datetime(p["datetime_utc"], utc=True)
    # Unify the q50 PM2.5-scale point prediction column across sources
    p["pm25_pred_q50"] = p[PRED_COL[source]]
    # Convert UTC → local time (Asia/Colombo = UTC+5:30)
    p["dt_local"] = p["datetime_utc"].dt.tz_convert("Asia/Colombo")
    # Optional year filter (Senarathna reference is calendar-year 2019)
    if year is not None:
        p = p[p["dt_local"].dt.year == year].copy()
        print(f"Filtered to year {year}: {len(p):,} rows "
              f"(sensors: {p['sensor_id'].value_counts().to_dict()})")
    p["hour_local"] = p["dt_local"].dt.hour
    p["dow_local"] = p["dt_local"].dt.dayofweek   # Mon=0
    p["month_local"] = p["dt_local"].dt.month
    tag = f" [{source}{'' if year is None else f', {year}'}]"
    # Preserve canonical filenames for the original (lgbm, all-years) invocation
    default_case = (year is None and source == "lgbm")
    suffix = "" if default_case else (f"_{source}" + ("" if year is None else f"_{year}"))

    # ── DIURNAL ────────────────────────────────────────────────────────────
    diurnal = p.groupby("hour_local").agg(
        n=("pm25_observed", "size"),
        obs_mean=("pm25_observed", "mean"),
        obs_sd=("pm25_observed", "std"),
        pred_mean=("pm25_pred_q50", "mean"),
    ).reset_index()
    diurnal["senarathna_mean"] = diurnal["hour_local"].map(SENARATHNA_HOURLY)
    diurnal["pred_minus_obs"] = diurnal["pred_mean"] - diurnal["obs_mean"]
    diurnal["obs_minus_senarathna"] = diurnal["obs_mean"] - diurnal["senarathna_mean"]
    diurnal.to_csv(OUT_DIR / f"senarathna_diurnal_comparison{suffix}.csv", index=False)

    # ── WEEKLY ─────────────────────────────────────────────────────────────
    weekly = p.groupby("dow_local").agg(
        n=("pm25_observed", "size"),
        obs_mean=("pm25_observed", "mean"),
        pred_mean=("pm25_pred_q50", "mean"),
    ).reset_index()
    weekly["senarathna_mean"] = weekly["dow_local"].map(SENARATHNA_WEEKLY)
    weekly["day"] = weekly["dow_local"].map(dict(enumerate(DAY_LABELS)))
    weekly.to_csv(OUT_DIR / f"senarathna_weekly_comparison{suffix}.csv", index=False)

    # ── MONTHLY ────────────────────────────────────────────────────────────
    monthly = p.groupby("month_local").agg(
        n=("pm25_observed", "size"),
        obs_mean=("pm25_observed", "mean"),
        pred_mean=("pm25_pred_q50", "mean"),
    ).reset_index()
    monthly["senarathna_mean"] = monthly["month_local"].map(SENARATHNA_MONTHLY)
    monthly["month"] = monthly["month_local"].map(dict(enumerate(MONTH_LABELS, 1)))
    monthly.to_csv(OUT_DIR / f"senarathna_monthly_comparison{suffix}.csv", index=False)

    # ── Shape correlation ──────────────────────────────────────────────────
    def _pearson_r(a, b):
        return float(np.corrcoef(a, b)[0, 1])

    r_diurnal_obs = _pearson_r(diurnal["obs_mean"], diurnal["senarathna_mean"])
    r_diurnal_pred = _pearson_r(diurnal["pred_mean"], diurnal["senarathna_mean"])
    r_weekly_obs = _pearson_r(weekly["obs_mean"], weekly["senarathna_mean"])
    r_weekly_pred = _pearson_r(weekly["pred_mean"], weekly["senarathna_mean"])
    r_monthly_obs = _pearson_r(monthly["obs_mean"], monthly["senarathna_mean"])
    r_monthly_pred = _pearson_r(monthly["pred_mean"], monthly["senarathna_mean"])

    print(f"\n══ SHAPE CORRELATION vs Senarathna 2024{tag} ══")
    print(f"{'Pattern':<15}{'FECT obs':>12}{'v3 pred':>12}")
    print("-" * 45)
    print(f"{'Diurnal (24h)':<15}{r_diurnal_obs:>12.3f}{r_diurnal_pred:>12.3f}")
    print(f"{'Weekly (7d)':<15}{r_weekly_obs:>12.3f}{r_weekly_pred:>12.3f}")
    print(f"{'Monthly (12m)':<15}{r_monthly_obs:>12.3f}{r_monthly_pred:>12.3f}")

    # Peak timing matches
    pred_peak_morning = diurnal[diurnal["hour_local"].between(4, 11)]["pred_mean"].idxmax()
    pred_peak_evening = diurnal[diurnal["hour_local"].between(15, 22)]["pred_mean"].idxmax()
    obs_peak_morning = diurnal[diurnal["hour_local"].between(4, 11)]["obs_mean"].idxmax()
    obs_peak_evening = diurnal[diurnal["hour_local"].between(15, 22)]["obs_mean"].idxmax()
    print(f"\nMorning-peak hour LT: Senarathna=07  FECT obs={diurnal.loc[obs_peak_morning,'hour_local']}  v3 pred={diurnal.loc[pred_peak_morning,'hour_local']}")
    print(f"Evening-peak hour LT: Senarathna=18  FECT obs={diurnal.loc[obs_peak_evening,'hour_local']}  v3 pred={diurnal.loc[pred_peak_evening,'hour_local']}")

    obs_monthly_peak = monthly["obs_mean"].idxmax()
    pred_monthly_peak = monthly["pred_mean"].idxmax()
    print(f"\nMonth-peak: Senarathna=Mar  FECT obs={MONTH_LABELS[monthly.loc[obs_monthly_peak,'month_local']-1]}  v3 pred={MONTH_LABELS[monthly.loc[pred_monthly_peak,'month_local']-1]}")
    obs_monthly_trough = monthly["obs_mean"].idxmin()
    pred_monthly_trough = monthly["pred_mean"].idxmin()
    print(f"Month-trough: Senarathna=Dec  FECT obs={MONTH_LABELS[monthly.loc[obs_monthly_trough,'month_local']-1]}  v3 pred={MONTH_LABELS[monthly.loc[pred_monthly_trough,'month_local']-1]}")

    # ── FIGURES ────────────────────────────────────────────────────────────
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 150})

    # --- diurnal ---
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(diurnal["hour_local"], diurnal["senarathna_mean"],
            "o-", color="#c92a2a", lw=1.5, ms=5,
            label="Senarathna 2024 (KOALA, valley floor)")
    ax.plot(diurnal["hour_local"], diurnal["obs_mean"],
            "s-", color="#1864ab", lw=1.5, ms=5,
            label="FECT observed (Akurana + Hantana TR4)")
    ax.plot(diurnal["hour_local"], diurnal["pred_mean"],
            "^--", color="#9c36b5", lw=1.3, ms=4,
            label="v3 LightGBM predicted")
    ax.set_xticks(range(0, 24, 3))
    ax.set_xlabel("Local hour (Asia/Colombo, UTC+5:30)")
    ax.set_ylabel("PM₂.₅ (µg m⁻³)")
    ax.set_title(f"Diurnal cycle — r(obs,Senarathna)={r_diurnal_obs:+.3f}, "
                 f"r(pred,Senarathna)={r_diurnal_pred:+.3f}", fontsize=9)
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"diurnal_v3_vs_senarathna{suffix}.{ext}",
                    bbox_inches="tight", dpi=300)
    plt.close(fig)

    # --- weekly ---
    fig, ax = plt.subplots(figsize=(5, 3.4))
    x = np.arange(7)
    w = 0.27
    ax.bar(x - w, weekly["senarathna_mean"], w, color="#c92a2a",
           label="Senarathna 2024")
    ax.bar(x, weekly["obs_mean"], w, color="#1864ab", label="FECT observed")
    ax.bar(x + w, weekly["pred_mean"], w, color="#9c36b5",
           label="v3 predicted")
    ax.set_xticks(x)
    ax.set_xticklabels(DAY_LABELS)
    ax.set_ylabel("PM₂.₅ (µg m⁻³)")
    ax.set_title(f"Weekly cycle — r(obs,Senarathna)={r_weekly_obs:+.3f}, "
                 f"r(pred,Senarathna)={r_weekly_pred:+.3f}", fontsize=9)
    ax.legend(fontsize=7)
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"weekly_v3_vs_senarathna{suffix}.{ext}",
                    bbox_inches="tight", dpi=300)
    plt.close(fig)

    # --- monthly ---
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(monthly["month_local"], monthly["senarathna_mean"],
            "o-", color="#c92a2a", lw=1.5, ms=5,
            label="Senarathna 2024 (KOALA, 2019)")
    ax.plot(monthly["month_local"], monthly["obs_mean"],
            "s-", color="#1864ab", lw=1.5, ms=5,
            label="FECT observed (full 2019-2025)")
    ax.plot(monthly["month_local"], monthly["pred_mean"],
            "^--", color="#9c36b5", lw=1.3, ms=4,
            label="v3 LightGBM predicted")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_ylabel("PM₂.₅ (µg m⁻³)")
    ax.set_title(f"Monthly cycle — r(obs,Senarathna)={r_monthly_obs:+.3f}, "
                 f"r(pred,Senarathna)={r_monthly_pred:+.3f}", fontsize=9)
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"monthly_v3_vs_senarathna{suffix}.{ext}",
                    bbox_inches="tight", dpi=300)
    plt.close(fig)

    print(f"\nFigures: {FIG_DIR}")
    print(f"CSVs:    {OUT_DIR}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Compare Stage-1 v3 predictions vs Senarathna 2024 (KOALA 2019).")
    ap.add_argument("--year", type=int, default=None,
                    help="Filter predictions to a single calendar year (local time), e.g. 2019.")
    ap.add_argument("--source", choices=["lgbm", "lgbm_lagfree", "blend"], default="lgbm",
                    help="Prediction source: 'lgbm', 'lgbm_lagfree' (no pm25 lags), or 'blend' (production v3 blend).")
    args = ap.parse_args()
    main(year=args.year, source=args.source)
