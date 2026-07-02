"""sensitivity_analysis.py — Phase 2 of the evidence-hardening plan.

How much do the HEADLINE conclusions (area level, population-weighted exposure, the
local/regional partition, and the attributable burden) depend on the two assumptions a
reviewer will challenge: the local fraction f and the regional background level?

Key structural fact (the additive model is T-locked): PM = B + [T-B]*P_local with P_local
unit-mean, so the basin/area mean is exactly T regardless of f. The population-weighted
exposure is E_w = B + (T-B)*P_w = T*[1 + f*(P_w-1)], linear in f through the fixed pattern
excess P_w. A background over/under-estimate by a factor s maps onto the SAME axis:
B' = s*(1-f)*T  <=>  effective (1-f) -> s*(1-f). So sweeping effective f over [0.10, 0.40]
covers BOTH the f uncertainty (SBI 90% CI [0.10, 0.27]; source-apportionment [0.15, 0.35])
AND a +/-20% background error (which maps to f in ~[0.10, 0.40] around f0=0.25).

We recover the fixed pattern P_local from the official additive_v2 field, then re-evaluate
every headline metric across the f sweep and report the range. Output: a table + a tornado
figure. No re-forecast (the field is T-locked); this is an exact re-weighting.

Out: data/processed/decomp/sensitivity_analysis.csv
     results/figures/paper_figures_v2/S1_sensitivity.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "results" / "figures" / "paper_figures_v2"
OUT.mkdir(parents=True, exist_ok=True)

YEAR = 2023
FRAC_LOCAL_YEAR = {2019: 0.28, 2020: 0.25, 2021: 0.21, 2022: 0.20, 2023: 0.27}
# GEMM NCD+LRI (Burnett 2018), Sri Lanka baseline — mirror health_burden.py
THETA, ALPHA, MU, NU, C0 = 0.143, 1.6, 15.5, 36.8, 2.4
CDR, F_NCD_LRI, WHO_AQG, BBOX_POP = 6.6 / 1000.0, 0.85, 5.0, 422314.0
T_HOME, T_WORK, T_COMMUTE, K_IV = 0.65, 0.27, 0.08, 1.5


def af(pm):
    z = np.clip(pm - C0, 0, None)
    rr = np.exp(THETA * np.log1p(z / ALPHA) / (1.0 + np.exp(-(z - MU) / NU)))
    return (rr - 1.0) / rr


def _annual_field(year, col="pm25_q50"):
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_additive_v2.parquet",
                        columns=["lat", "lon", col])
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    Z = d.groupby(["lat", "lon"])[col].mean().unstack("lon").reindex(index=lats, columns=lons).values
    return Z, lats, lons


def main():
    from src.stage1_satml.decomp.exposure_weighting import _microenv_weights

    Z, lats, lons = _annual_field(YEAR)
    T = float(Z.mean())                       # area mean == T by the T-lock invariant
    f0 = FRAC_LOCAL_YEAR[YEAR]
    B0 = (1 - f0) * T                          # annual background at the nominal f
    # recover the fixed unit-mean local pattern from the official field
    P = (Z - B0) / (T - B0)
    print(f"[check] T(area)={T:.2f}  B0={B0:.2f}  f0={f0}  <P_local>={np.nanmean(P):.3f} (want ~1.0)")

    wr, wa, wc = _microenv_weights(lats, lons)

    def dyn_from_pattern(f):
        """Population-weighted (time-activity) exposure at local fraction f, exact re-weighting."""
        B = (1 - f) * T
        Zf = B + (T - B) * P                   # rebuild field at f (T-locked: area mean stays T)
        E_home = float((Zf * wr).sum()); E_work = float((Zf * wa).sum())
        E_comm = float((Zf * wc).sum()) * K_IV
        return (T_HOME * E_home + T_WORK * E_work + T_COMMUTE * E_comm) / (T_HOME + T_WORK + T_COMMUTE)

    base_total = BBOX_POP * CDR * F_NCD_LRI
    fs = np.round(np.arange(0.10, 0.401, 0.025), 3)
    rows = []
    for f in fs:
        E = dyn_from_pattern(f)
        deaths = base_total * af(np.array([E]))[0]
        avoid = base_total * max(0.0, af(np.array([E]))[0] - af(np.array([WHO_AQG]))[0])
        rows.append(dict(f=f, background_frac=round(1 - f, 3), area_mean=round(T, 2),
                         dynamic_exposure=round(E, 2), local_pct=round(100 * f, 1),
                         deaths=round(deaths), avoidable=round(avoid),
                         attributable_fraction_pct=round(100 * af(np.array([E]))[0], 1)))
    df = pd.DataFrame(rows)
    df.to_csv(DEC / "sensitivity_analysis.csv", index=False)
    print(df.to_string(index=False))

    # headline range across the plausible band [0.15, 0.35] (source-apportionment bracket)
    band = df[(df.f >= 0.15) & (df.f <= 0.35)]
    d_lo, d_hi = int(band.deaths.min()), int(band.deaths.max())
    e_lo, e_hi = band.dynamic_exposure.min(), band.dynamic_exposure.max()
    print(f"\nHEADLINE ROBUSTNESS over f in [0.15,0.35] (= background +/-~20%):")
    print(f"  area mean         : {T:.1f} (INVARIANT — T-locked)")
    print(f"  dynamic exposure  : {e_lo:.1f} - {e_hi:.1f}")
    print(f"  attributable deaths: {d_lo} - {d_hi}  (nominal f=0.25 -> "
          f"{int(df[df.f==0.25].deaths.iloc[0])})")

    # ---- tornado / sweep figure ------------------------------------------------
    fig, ax = plt.subplots(1, 3, figsize=(10.4, 3.1), constrained_layout=True)
    ax[0].axhline(T, color="#4C72B0", lw=2)
    ax[0].fill_between(df.f, T - 0.05, T + 0.05, color="#4C72B0", alpha=0.15)
    ax[0].set_title("(a) area mean — invariant", fontsize=9); ax[0].set_ylim(T - 3, T + 3)
    ax[0].set_xlabel("local fraction $f$"); ax[0].set_ylabel(r"PM$_{2.5}$ ($\mu$g m$^{-3}$)")

    ax[1].plot(df.f, df.dynamic_exposure, "o-", color="#C44E52")
    ax[1].axvspan(0.15, 0.35, color="grey", alpha=0.12)
    ax[1].axvline(0.25, color="k", ls=":", lw=1)
    ax[1].set_title("(b) population-weighted exposure", fontsize=9)
    ax[1].set_xlabel("local fraction $f$"); ax[1].set_ylabel(r"PM$_{2.5}$ ($\mu$g m$^{-3}$)")

    ax[2].plot(df.f, df.deaths, "o-", color="#8172B3", label="attributable")
    ax[2].fill_between(df.f, band.deaths.min(), band.deaths.max(), color="grey", alpha=0.10)
    ax[2].axvspan(0.15, 0.35, color="grey", alpha=0.12)
    ax[2].axvline(0.25, color="k", ls=":", lw=1)
    ax[2].set_title("(c) attributable deaths/yr", fontsize=9)
    ax[2].set_xlabel("local fraction $f$"); ax[2].set_ylabel("deaths yr$^{-1}$")
    for a in ax:
        a.grid(alpha=0.25); a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Sensitivity of headline conclusions to the local fraction $f$ and background "
                 "(shaded = plausible band $f\\in[0.15,0.35]$ = background $\\pm20\\%$; dotted = nominal 0.25)",
                 fontsize=9.5)
    fig.savefig(OUT / "S1_sensitivity.png", dpi=350, bbox_inches="tight"); plt.close(fig)
    print(f"\nwrote {DEC/'sensitivity_analysis.csv'}\nwrote {OUT/'S1_sensitivity.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
