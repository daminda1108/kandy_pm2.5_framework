"""
build_s_learned.py — data-grounded spatial field combining emission and
confinement in the ratio LEARNED from the full Medellín network (2026-06-03):

    log PM(x,y) ≈ β_E·z(emission) + β_C·z(confinement),   β_E=0.40, β_C=0.32

(from scripts/medellin_full_emission_confinement.py: both identifiable on the
24-station elevation-spanning Aburrá network, corr 0.08, R²=0.31, P(β>0)=93/97%).

This REPLACES the misplaced confinement-dominant S_emit·M annual pattern that put
Kandy's hotspot on the lowest floor (Peradeniya/Katugastota fringe) instead of
the traffic core. Now emission (traffic core) co-leads, as the data say it should.

  emission  = traffic source (road network class-weighted + core-congestion boost),
              the same proxy the transport solver uses.
  confinement = c(x,y) = z-score(−δz)  (enclosed valley floor positive).

Out: data/processed/decomp/S_learned_kandy.npz  +  before/after figure.
"""
from __future__ import annotations
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import griddata

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.figures_pub import _draw, _scale_bar, _north_arrow, LANDMARKS

DEC = REPO / "data" / "processed" / "decomp"
PIN = REPO / "data" / "processed" / "pinn_inputs"
OUT = REPO / "results" / "figures" / "monograph" / "final"
OUT.mkdir(parents=True, exist_ok=True)
BETA_E, BETA_C = 0.40, 0.32          # learned Medellín weights
CITY = (7.2906, 80.6337)


def emission16(lats, lons):
    """Traffic emission proxy on the 16x16 grid: class-weighted road network +
    core-congestion boost (bus terminals / clock tower / lake), matching the solver."""
    rk = np.load(PIN / "kandy_road_kernel_100m.npz")
    R = griddata(np.column_stack([rk["lat_grid"].ravel(), rk["lon_grid"].ravel()]),
                 rk["R"].ravel(), tuple(np.meshgrid(lats, lons, indexing="ij")), method="linear")
    R = np.nan_to_num(R, nan=0.0)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    for clat, clon, amp, sig in [(7.2915, 80.6360, 0.6, 1100.0), (7.2880, 80.6420, 0.3, 800.0)]:
        d2 = ((LA - clat) * 111000) ** 2 + ((LO - clon) * 111000 * np.cos(np.radians(clat))) ** 2
        R = R + amp * np.exp(-d2 / (2 * sig ** 2))
    # smooth so the source is a coherent core + arteries, not 1-km road speckle
    from scipy.ndimage import gaussian_filter
    R = gaussian_filter(R, sigma=1.1)
    return R / (R.max() + 1e-9)


def main():
    M = np.load(DEC / "M_confinement_kandy.npz"); c, lats, lons = M["c"], M["lats"], M["lons"]
    E = emission16(lats, lons)
    # clip standardised predictors to +/-2.5 (as c already is) so the gridded
    # tails don't blow up exp() relative to the station-level fit
    z = lambda a: np.clip((a - a.mean()) / (a.std() + 1e-9), -2.5, 2.5)
    S_learned = np.exp(BETA_E * z(E) + BETA_C * z(c)); S_learned /= S_learned.mean()
    np.savez(DEC / "S_learned_kandy.npz", S_learned=S_learned, lats=lats, lons=lons,
             beta_E=BETA_E, beta_C=BETA_C, emission=E, confinement=c)

    L = pd.read_csv(REPO / "data/processed/stage1_v3/vandonkelaar_kandy_annual.csv"
                    ).set_index("year")["L_corrected"]
    Lc = float(L.loc[2019:2023].mean())
    # current smooth annual field for comparison
    d = pd.read_parquet(DEC / "kandy_decomp_predictions_2023.parquet",
                        columns=["lat", "lon", "pm25_q50"])
    cur = d.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(
        index=lats, columns=lons).values
    new = Lc * S_learned

    def at(la, lo, A):
        return A[int(np.argmin(np.abs(lats - la))), int(np.argmin(np.abs(lons - lo)))]
    print(f"S_learned: core {S_learned[int(np.argmin(abs(lats-CITY[0]))),int(np.argmin(abs(lons-CITY[1])))]:.2f}  "
          f"range {S_learned.min():.2f}-{S_learned.max():.2f}  mean {S_learned.mean():.2f}")
    print(f"core/edge: current {at(*CITY,cur)/np.percentile(cur,15):.2f}×  "
          f"learned {at(*CITY,new)/np.percentile(new,15):.2f}×")

    fig, ax = plt.subplots(1, 2, figsize=(12, 5.6), constrained_layout=True)
    for a, Z, ttl in [(ax[0], cur, "(a) Current smooth T·S·M (confinement-dominant)\n"
                       "hotspot displaced to low floor (Peradeniya/Katugastota)"),
                      (ax[1], new, "(b) Learned 0.40:0.32 emission:confinement (Medellín)\n"
                       "traffic core leads, confinement co-present")]:
        im = _draw(a, Z, lats, lons, "YlOrRd", vmin=10, vmax=45)
        for nm, (la, lo, mk) in LANDMARKS.items():
            a.annotate(nm, (lo, la), xytext=(4, 4), textcoords="offset points", fontsize=7)
        _scale_bar(a, lats, lons); a.set_xlabel("Lon (°E)")
    ax[0].set_ylabel("Lat (°N)"); _north_arrow(ax[1], lats, lons)
    cb = fig.colorbar(im, ax=ax, label="annual PM₂.₅ (µg m⁻³)", extend="both",
                      ticks=[10, 15, 25, 35, 45], shrink=0.7)
    cb.ax.set_yticklabels(["10", "15 IT-3", "25 IT-2", "35 IT-1", "45"], fontsize=7)
    fig.suptitle("Data-grounded spatial fix: emission:confinement weighting learned from "
                 "the full Medellín elevation-spanning network", fontsize=11)
    fig.savefig(OUT / "learned_spatial_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {DEC/'S_learned_kandy.npz'}")
    print(f"Wrote {OUT/'learned_spatial_comparison.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
