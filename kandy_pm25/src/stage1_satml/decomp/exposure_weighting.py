"""
exposure_weighting.py — area vs DYNAMIC (time-activity) population exposure (2026-06-04).

The area mean is a spatial average; personal exposure is governed by *time-activity*:
people sleep in the cleaner residential periphery but spend their active hours in the
commercial core and commute through the congested roads, where concentrations are
highest. Static residential weighting therefore UNDER-states exposure — dynamic /
mobility-based assessment finds personal PM2.5 exposure 12–19 % above residential on
average (Park & Kwan 2017; Yu et al. 2021), and the commute microenvironment alone can
contribute ~30 % of daily exposure from ~6 % of the time because on-road/in-vehicle
concentrations are elevated (Hudda & Fruin 2013).

We build a time-activity-weighted exposure from three microenvironments:
  E_dyn = [ t_home·E_home + t_work·E_work + t_commute·κ_iv·E_commute ] / Σt
    E_home    = PM weighted by residential population   (WorldPop)        t_home=0.65
    E_work    = PM weighted by commercial activity      (VIIRS night-lights) t_work=0.27
    E_commute = PM weighted by congested roads          (S_traffic)       t_commute=0.08
    κ_iv = 1.5  in-vehicle/roadside enhancement over ambient (Hudda & Fruin 2013)

Reports area mean < residential < DYNAMIC < core, and feeds the health burden at the
dynamic exposure (the concentration people actually breathe).

Out: data/processed/decomp/exposure_weighting.csv + final_model_suite/figX2_exposure_inequality.png
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
DEC = REPO / "data" / "processed" / "decomp"
PIN = REPO / "data" / "processed" / "pinn_inputs"
from src.stage1_satml.decomp.pubfig import PUB_OUT as OUT  # publication style + folder
OUT.mkdir(parents=True, exist_ok=True)
KOALA_FLOOR = 24.52
KOALA_YEAR = 2019        # KOALA 24.5 is the Jan-Dec 2019 annual mean only (Senarathna 2024,
                         # one year of NIFS data) -> a single-year anchor, NOT a per-year series
YEARS = range(2019, 2024)
T_HOME, T_WORK, T_COMMUTE, K_INVEHICLE = 0.65, 0.27, 0.08, 1.5


def _norm(a):
    a = np.clip(np.nan_to_num(a, nan=0.0), 0, None)
    return a / (a.sum() + 1e-12)


def _microenv_weights(lats, lons):
    """Residential, commercial-activity, and commute weight fields (each sums to 1)."""
    resid = np.load(DEC / "population_kandy.npz")["pop"].astype(float)          # WorldPop
    ntl = np.load(PIN / "kandy_viirs_ntl_stations.npz")
    nlat, nlon = ntl["lat_grid"][:, 0], ntl["lon_grid"][0, :]
    NL = np.expm1(np.clip(ntl["NTL_log"].astype(float), 0, None))               # ~linear radiance
    from scipy.interpolate import RegularGridInterpolator
    if nlat[0] > nlat[-1]:
        nlat, NL = nlat[::-1], NL[::-1, :]
    if nlon[0] > nlon[-1]:
        nlon, NL = nlon[::-1], NL[:, ::-1]
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    act = RegularGridInterpolator((nlat, nlon), NL, bounds_error=False, fill_value=0.0)(
        np.stack([LA.ravel(), LO.ravel()], 1)).reshape(len(lats), len(lons))
    commute = np.load(DEC / "S_traffic_kandy.npz")["S_traffic"].astype(float)
    return _norm(resid), _norm(act), _norm(commute)


def _field_path(year, suffix):
    """headline = additive (Lenschow) field; fall back to 4-factor then smooth."""
    for suf in [suffix, "_additive", "_4factor", ""]:
        p = DEC / f"kandy_decomp_predictions_{year}{suf}.parquet"
        if p.exists():
            return p
    raise FileNotFoundError(year)


# tier selector: v1 archive | v2 (paper/scorecard) | v3 (shipped: + ventilated-hour
# floor). Default follows the SHIPPED product so health numbers cannot silently
# describe a different field from the one the explorer draws (2026-07-25 audit).
_VAR = os.environ.get("PAPERFIG_VARIANT", "v3")
_ADD = {"v1": "_additive", "v2": "_additive_v2"}.get(_VAR, "_additive_v3")


def _annual(year, col="pm25_q50", suffix=_ADD):
    d = pd.read_parquet(_field_path(year, suffix), columns=["lat", "lon", col])
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    Z = d.groupby(["lat", "lon"])[col].mean().unstack("lon").reindex(index=lats, columns=lons).values
    return Z, lats, lons


def dynamic_exposure(Z, wr, wa, wc):
    E_home = float((Z * wr).sum()); E_work = float((Z * wa).sum())
    E_commute = float((Z * wc).sum()) * K_INVEHICLE
    return (T_HOME * E_home + T_WORK * E_work + T_COMMUTE * E_commute) / (T_HOME + T_WORK + T_COMMUTE)


def main():
    rows = []
    for y in YEARS:
        Z, lats, lons = _annual(y)                             # additive headline field (Lenschow)
        Zs = Z                                                  # area mean = spatial mean of headline
        wr, wa, wc = _microenv_weights(lats, lons)
        rows.append(dict(
            year=y, area_mean=float(Zs.mean()),
            residential=float((Z * wr).sum()),
            dynamic=dynamic_exposure(Z, wr, wa, wc),
            core=float((Z * wa).sum()),
            koala_floor_2019=KOALA_FLOOR if y == KOALA_YEAR else np.nan))
    df = pd.DataFrame(rows)
    df.to_csv(DEC / "exposure_weighting.csv", index=False)
    print(df.round(2).to_string(index=False))
    print(f"\n  area ~{df.area_mean.mean():.1f} | residential ~{df.residential.mean():.1f} | "
          f"DYNAMIC ~{df.dynamic.mean():.1f} | commercial-core ~{df.core.mean():.1f}  "
          f"(dynamic +{(df.dynamic.mean()/df.area_mean.mean()-1)*100:.0f}% over area)")

    fig, ax = plt.subplots(figsize=(7.6, 4.6), constrained_layout=True)
    x = df.year
    ax.plot(x, df.area_mean, "o-", color="#4C72B0", lw=2, label="area mean (spatial avg)")
    ax.plot(x, df.residential, "s-", color="#55A868", lw=2, label="residential (WorldPop, home only)")
    ax.plot(x, df.dynamic, "D-", color="#C44E52", lw=2.4, label="DYNAMIC time-activity (home+work+commute)")
    ax.plot(x, df.core, "^--", color="#8172B3", lw=1.6, label="commercial-core (activity-weighted)")
    # KOALA is a single-year (2019) floor/core anchor — plot it ONLY at 2019, not
    # as a line spanning every year (it was not re-measured each year).
    ax.scatter([KOALA_YEAR], [KOALA_FLOOR], marker="*", s=180, color="k", zorder=6,
               label="KOALA 2019 floor/core (Senarathna 2024, 2019 only)")
    ax.set_xticks(list(x)); ax.set_xlabel("year"); ax.set_ylabel("annual PM₂.₅ (µg m⁻³)")
    ax.set_title("Exposure rises with mobility: residents sleep in the cleaner periphery but\n"
                 "work + commute through the polluted core — dynamic exposure exceeds the area mean",
                 fontsize=9.3)
    ax.legend(fontsize=7.6); ax.grid(alpha=0.25)
    fig.savefig(OUT / "figX2_exposure_inequality.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print(f"Wrote {DEC/'exposure_weighting.csv'}\nWrote {OUT/'figX2_exposure_inequality.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
