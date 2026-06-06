"""
health_burden.py — attributable PM2.5 mortality burden for Kandy (2026-06-04, Tier 1.3).

Turns the reconstructed PM2.5 field + WorldPop population into the attributable
premature-mortality burden the monograph's health framing promises, via the Global
Exposure Mortality Model (GEMM; Burnett et al. 2018, PNAS 115:9592). Per 1 km pixel:

  z      = max(0, PM2.5 - C0),  C0 = 2.4 µg m⁻³ (GEMM counterfactual / TMREL)
  RR(z)  = exp{ θ · log(1 + z/α) · 1/(1+exp(-(z-μ)/ν)) }     [GEMM NCD+LRI single curve]
  AF     = (RR-1)/RR                                          [attributable fraction]
  deaths = AF · pop · CDR · f_NCD+LRI                         [attributable deaths/yr]

Uses the GEMM NCD+LRI hazard (non-communicable disease + lower-respiratory infection,
adults; the aggregate recommended by Burnett 2018 for total burden), α=1.6, μ=15.5,
ν=36.8, θ=0.143. Baseline: Sri Lanka crude death rate 6.6/1000 (World Bank 2022) ×
NCD+LRI share 0.85 (WHO NCD profile). Population: WorldPop 2020 (population_kandy.npz),
renormalised to the bbox count 422 k. Uncertainty propagated from the PM q05/q95
intervals. Burden vs the WHO AQG (5 µg m⁻³) gives the avoidable fraction.

Note: a screening-level estimate — single-curve (non-age-resolved) GEMM × crude
NCD+LRI baseline, applied at the population-weighted exposure. Age-stratified baseline
rates and YLL would refine it; the order of magnitude and the avoidable share are robust.

Out: data/processed/decomp/health_burden.csv + final_model_suite/figX5_health_burden.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.figures_pub import _draw, _scale_bar, _north_arrow, LANDMARKS

DEC = REPO / "data" / "processed" / "decomp"
from src.stage1_satml.decomp.pubfig import PUB_OUT as OUT  # publication style + folder
OUT.mkdir(parents=True, exist_ok=True)

# GEMM NCD+LRI (Burnett 2018)
THETA, ALPHA, MU, NU, C0 = 0.143, 1.6, 15.5, 36.8, 2.4
# Sri Lanka baseline
CDR = 6.6 / 1000.0          # crude death rate (World Bank 2022)
F_NCD_LRI = 0.85            # NCD (~83%, WHO) + LRI (~2%) share of deaths
WHO_AQG = 5.0
BBOX_POP = 422314.0        # WorldPop bbox count (cell-sum overcounts edges → renormalise)


def gemm_rr(pm):
    z = np.clip(pm - C0, 0, None)
    return np.exp(THETA * np.log1p(z / ALPHA) / (1.0 + np.exp(-(z - MU) / NU)))


def af(pm):
    rr = gemm_rr(pm)
    return (rr - 1.0) / rr


def _field_path(year, suffix="_additive"):
    """headline = additive (Lenschow) field; fall back to 4-factor then smooth."""
    for suf in [suffix, "_additive", "_4factor", ""]:
        p = DEC / f"kandy_decomp_predictions_{year}{suf}.parquet"
        if p.exists():
            return p
    raise FileNotFoundError(year)


def _annual(year, col="pm25_q50", four_factor=False):
    d = pd.read_parquet(_field_path(year), columns=["lat", "lon", col])
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    Z = d.groupby(["lat", "lon"])[col].mean().unstack("lon").reindex(index=lats, columns=lons).values
    return Z, lats, lons


def main(year=2023):
    from src.stage1_satml.decomp.exposure_weighting import _microenv_weights, dynamic_exposure
    P = np.load(DEC / "population_kandy.npz"); pop = P["pop"].astype(float)
    pop = pop * (BBOX_POP / pop.sum())            # renormalise to the true bbox count
    # exposure on the REALISTIC field (4-factor core hotspot) — exposure is core-dominated
    ff = (DEC / f"kandy_decomp_predictions_{year}_4factor.parquet").exists()
    Z, lats, lons = _annual(year, "pm25_q50", four_factor=ff)
    Zlo, _, _ = _annual(year, "pm25_q05", four_factor=ff)
    Zhi, _, _ = _annual(year, "pm25_q95", four_factor=ff)
    wr, wa, wc = _microenv_weights(lats, lons)

    # DYNAMIC time-activity exposure (home+work+commute) — the concentration people
    # actually breathe; burden = total NCD+LRI baseline × attributable fraction at E_dyn
    pwe = dynamic_exposure(Z, wr, wa, wc)
    e_lo = dynamic_exposure(Zlo, wr, wa, wc); e_hi = dynamic_exposure(Zhi, wr, wa, wc)
    base_total = float(pop.sum()) * CDR * F_NCD_LRI
    tot = base_total * af(np.array([pwe]))[0]
    lo = base_total * af(np.array([e_lo]))[0]; hi = base_total * af(np.array([e_hi]))[0]
    avoidable = base_total * max(0.0, af(np.array([pwe]))[0] - af(np.array([WHO_AQG]))[0])
    # per-residence spatial map (where people live × local realistic AF) for the figure
    base = pop * CDR * F_NCD_LRI
    deaths = af(Z) * base

    rate = tot / BBOX_POP * 1e5
    summary = dict(
        year=year, population=int(BBOX_POP), dynamic_exposure=round(pwe, 1),
        exposure_uplift_pct=round((pwe / float(Z.mean()) - 1) * 100),
        attributable_deaths_per_yr=round(tot), ci_low=round(lo), ci_high=round(hi),
        rate_per_100k=round(rate, 1),
        attributable_fraction_pct=round(af(np.array([pwe]))[0] * 100, 1),
        avoidable_vs_WHO_AQG5=round(avoidable),
        gemm="NCD+LRI Burnett2018", baseline="SriLanka CDR 6.6/1000 x 0.85 NCD+LRI")
    pd.DataFrame([summary]).to_csv(DEC / "health_burden.csv", index=False)
    for k, v in summary.items():
        print(f"  {k:<28}{v}")

    # multi-year range (dynamic exposure each year)
    print("\n  per-year attributable deaths (dynamic exposure):")
    for y in range(2019, 2024):
        ffy = (DEC / f"kandy_decomp_predictions_{y}_4factor.parquet").exists()
        Zy, _, _ = _annual(y, "pm25_q50", four_factor=ffy)
        ey = dynamic_exposure(Zy, wr, wa, wc)
        print(f"    {y}: {round(base_total*af(np.array([ey]))[0])}  (E_dyn {ey:.1f})")

    # figure: (a) burden density map, (b) GEMM curve, (c) headline numbers
    fig = plt.figure(figsize=(15, 5.2), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1, 0.8])
    ax0 = fig.add_subplot(gs[0, 0])
    dens = deaths / 1.21                            # ~per km² (1 km pixels ~1.21 km² here)
    im = _draw(ax0, deaths, lats, lons, "magma", vmin=0, vmax=np.percentile(deaths, 99))
    for nm, (la, lo_, mk) in LANDMARKS.items():
        ax0.plot(lo_, la, mk, mfc="cyan", mec="k", mew=0.7, ms=5)
    _scale_bar(ax0, lats, lons); _north_arrow(ax0, lats, lons)
    ax0.set_title(f"(a) attributable PM₂.₅ deaths/yr per pixel ({year})\n"
                  f"total {tot:.0f}/yr [{lo:.0f}–{hi:.0f}] — concentrated where people + pollution meet", fontsize=9)
    ax0.set_xticks([]); ax0.set_yticks([])
    fig.colorbar(im, ax=ax0, shrink=0.8, label="deaths yr⁻¹ pixel⁻¹")

    ax1 = fig.add_subplot(gs[0, 1])
    pm = np.linspace(0, 60, 200)
    ax1.plot(pm, gemm_rr(pm), color="#B2182B", lw=2)
    ax1.axvline(pwe, color="#08519C", ls="--", label=f"Kandy dynamic exp. {pwe:.0f}")
    ax1.axvline(WHO_AQG, color="green", ls=":", label="WHO AQG 5")
    ax1.scatter([pwe], [gemm_rr(np.array([pwe]))[0]], color="#08519C", zorder=5)
    ax1.set_xlabel("PM₂.₅ (µg m⁻³)"); ax1.set_ylabel("relative risk (NCD+LRI)")
    ax1.set_title("(b) GEMM exposure–response\n(Burnett 2018)", fontsize=9)
    ax1.legend(fontsize=8); ax1.grid(alpha=0.25)

    ax2 = fig.add_subplot(gs[0, 2]); ax2.axis("off")
    txt = (f"KANDY PM₂.₅ HEALTH BURDEN\n({year}, pop {BBOX_POP/1e3:.0f}k)\n\n"
           f"dynamic exposure (time-activity)\n  {pwe:.0f} µg m⁻³  ({pwe/WHO_AQG:.1f}× WHO AQG)\n\n"
           f"attributable deaths/yr\n  {tot:.0f}  [{lo:.0f}–{hi:.0f}]\n"
           f"  = {rate:.0f} per 100k\n  = {af(np.array([pwe]))[0]*100:.0f}% of NCD+LRI deaths\n\n"
           f"avoidable if WHO AQG met\n  {avoidable:.0f} deaths/yr")
    ax2.text(0.0, 0.95, txt, va="top", ha="left", fontsize=9.5, family="monospace",
             bbox=dict(boxstyle="round,pad=0.5", fc="#FFF6EC", ec="#B2182B"))
    fig.suptitle("Attributable PM₂.₅ mortality burden, Kandy — GEMM NCD+LRI × WorldPop "
                 "(screening-level; PM intervals → burden CI)", fontsize=11)
    fig.savefig(OUT / "figX5_health_burden.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print(f"\nWrote {DEC/'health_burden.csv'}\nWrote {OUT/'figX5_health_burden.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
