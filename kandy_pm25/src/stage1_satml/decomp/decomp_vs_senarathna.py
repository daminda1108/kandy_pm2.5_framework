"""
decomp_vs_senarathna.py — validate the 2019 decomposition map at the NIFS
valley-floor pixel against Senarathna et al. 2024 (KOALA Kandy, NIFS, 2019).

Unlike the earlier FECT-highland comparison (shape only — FECT sits ~10 µg/m³
below the valley floor), the decomposition predicts at *any* pixel, so we sample
the NIFS pixel where Senarathna actually measured. Because 2019 is anchored to
the per-year VanD level (which reproduces KOALA 24.5 at the 2019 check), this
tests SHAPE *and* MAGNITUDE simultaneously.

Outputs to results/figures/kandy_decomp/2019/:
  vs_senarathna_diurnal.png   — decomp@NIFS (q50 + 90% PI) vs Senarathna hourly
  vs_senarathna_monthly.png   — decomp@NIFS vs Senarathna monthly
  vs_senarathna_metrics.csv   — Pearson r (diurnal, monthly) + peak/trough timing
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

from src.stage1_satml.evaluation.compare_senarathna_v3 import (
    SENARATHNA_HOURLY, SENARATHNA_MONTHLY, MONTH_LABELS)

DECOMP = HERE / "data" / "processed" / "decomp"
FIG = HERE / "results" / "figures" / "kandy_decomp" / "2019"
FIG.mkdir(parents=True, exist_ok=True)
NIFS = (7.2675, 80.5985)


def main(year: int = 2019):
    df = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{year}.parquet")
    df["time"] = pd.to_datetime(df["time"], utc=True)
    lats, lons = np.sort(df.lat.unique()), np.sort(df.lon.unique())
    la = lats[np.argmin(np.abs(lats - NIFS[0]))]
    lo = lons[np.argmin(np.abs(lons - NIFS[1]))]
    p = df[(df.lat == la) & (df.lon == lo)].copy()
    lt = p["time"].dt.tz_convert("Asia/Colombo")
    p["hour"] = lt.dt.hour
    p["month"] = lt.dt.month
    print(f"NIFS pixel ({la:.4f},{lo:.4f}); annual mean {p.pm25_q50.mean():.2f} "
          f"(Senarathna 2019 ≈ 24.5)")

    di = p.groupby("hour").agg(q50=("pm25_q50", "mean"), q05=("pm25_q05", "mean"),
                               q95=("pm25_q95", "mean")).reset_index()
    di["sen"] = di["hour"].map(SENARATHNA_HOURLY)

    # No-M reference: T(t)·S_emit at NIFS (isolates temporal+emission structure
    # from the nocturnal confinement modulation, for an honest before/after).
    T = pd.read_parquet(HERE / "data" / "processed" / "stage1_v3" / "T_anchor" /
                        f"T_kandy_hourly_{year}.parquet")
    T["time"] = pd.to_datetime(T["datetime_utc"], utc=True)
    T["hour"] = T["time"].dt.tz_convert("Asia/Colombo").dt.hour
    Sz = np.load(HERE / "data" / "processed" / "decomp" / "S_emit_kandy.npz")
    s_lats, s_lons = Sz["lats"], Sz["lons"]
    s_nifs = float(Sz["S_emit"][np.argmin(np.abs(s_lats - la)),
                                np.argmin(np.abs(s_lons - lo))])
    di["noM"] = di["hour"].map(T.groupby("hour")["T_q50"].mean() * s_nifs)
    r_noM = float(np.corrcoef(di.noM, di.sen)[0, 1])
    mo = p.groupby("month").agg(q50=("pm25_q50", "mean")).reset_index()
    mo["sen"] = mo["month"].map(SENARATHNA_MONTHLY)

    r_di = float(np.corrcoef(di.q50, di.sen)[0, 1])
    r_mo = float(np.corrcoef(mo.q50, mo.sen)[0, 1])
    peak_d = int(di.loc[di[di.hour.between(4, 11)].q50.idxmax(), "hour"])
    peak_e = int(di.loc[di[di.hour.between(15, 22)].q50.idxmax(), "hour"])
    peak_mo = MONTH_LABELS[int(mo.loc[mo.q50.idxmax(), "month"]) - 1]
    print(f"  diurnal r={r_di:+.3f}  monthly r={r_mo:+.3f}  "
          f"morning peak {peak_d} LT (Sen 07)  evening peak {peak_e} LT (Sen 18)  "
          f"month peak {peak_mo} (Sen Mar)")
    pd.DataFrame([dict(year=year, nifs_annual=float(p.pm25_q50.mean()),
                       diurnal_r=r_di, monthly_r=r_mo, morning_peak_lt=peak_d,
                       evening_peak_lt=peak_e, month_peak=peak_mo)]).to_csv(
        FIG / "vs_senarathna_metrics.csv", index=False)

    # diurnal figure
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.fill_between(di.hour, di.q05, di.q95, alpha=0.18, color="#9c36b5",
                    label="decomp 90% PI")
    ax.plot(di.hour, di.sen, "o-", color="#c92a2a", lw=1.6, ms=5,
            label="Senarathna 2024 (NIFS, 2019)")
    ax.plot(di.hour, di.noM, "s:", color="#1864ab", lw=1.3, ms=4,
            label=f"T·S_emit @ NIFS (no M, r={r_noM:+.2f})")
    ax.plot(di.hour, di.q50, "^--", color="#9c36b5", lw=1.4, ms=4,
            label=f"Full T·S·M @ NIFS (r={r_di:+.2f})")
    ax.set_xticks(range(0, 24, 3)); ax.set_xlabel("Local hour (UTC+5:30)")
    ax.set_ylabel("PM₂.₅ (µg m⁻³)")
    ax.set_title(f"Diurnal cycle at NIFS, {year} — temporal anchor vs full model",
                 fontsize=9)
    ax.legend(fontsize=7); ax.grid(axis="y", lw=0.4, alpha=0.5)
    fig.tight_layout(); fig.savefig(FIG / "vs_senarathna_diurnal.png", dpi=150,
                                    bbox_inches="tight"); plt.close(fig)

    # monthly figure
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.plot(mo.month, mo.sen, "o-", color="#c92a2a", lw=1.6, ms=5,
            label="Senarathna 2024 (NIFS, 2019)")
    ax.plot(mo.month, mo.q50, "^--", color="#9c36b5", lw=1.4, ms=4,
            label="Decomposition @ NIFS pixel")
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(MONTH_LABELS)
    ax.set_ylabel("PM₂.₅ (µg m⁻³)")
    ax.set_title(f"Monthly cycle at NIFS, {year} — r = {r_mo:+.3f}", fontsize=9)
    ax.legend(fontsize=7); ax.grid(axis="y", lw=0.4, alpha=0.5)
    fig.tight_layout(); fig.savefig(FIG / "vs_senarathna_monthly.png", dpi=150,
                                    bbox_inches="tight"); plt.close(fig)
    print(f"Wrote figures + metrics to {FIG}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2019)
    main(ap.parse_args().year)
