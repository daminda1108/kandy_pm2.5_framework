"""
build_s_emit_urban_increment.py — Akurana-anchored urban-increment spatial surface.

A SCENARIO / independent cross-check on the satellite S_emit(x,y), NOT a new
headline. Implements the Lenschow (2001) urban-increment decomposition with a
3-tier mass-balance constraint:

    area-mean( S_emit_UI )  =  1   (preserves the basin level T(t))

The non-core tiers are pinned by a REAL local observation (the FECT Akurana
peri-urban town, ~6 km N of the core, out-of-bbox) and a stated highland prior;
the urban CORE falls out as the mass-balance residual. Because most of the 15x15
km box is peri-urban + highland, pinning those low forces the small core up —
the "not all the bbox mean comes from the core" effect.

Tiers are assigned from a road-density + night-lights emission index on the
canonical 16x16 ~1 km grid. Akurana is the *exemplar* that sets the peri-urban
tier LEVEL (it is one grid-row north of the domain, so it is not classified, only
used as the level anchor).

Honest status: scenario, wide UQ. Akurana is a town (not clean background); N=1
peri-urban anchor; its calibrated level inherits the open KOALA-vs-FECT
PurpleAir-calibration question (r_A swings 0.54-0.87 across years); highland is a
prior; the core is an extrapolation bounded only by mass balance; horizontal only
(does nothing for the vertical confinement). See docs framing.

Outputs:
  data/processed/decomp/S_emit_urban_increment.npz
  data/processed/decomp/s_emit_urban_increment_summary.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import griddata

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

from src.stage1_satml.features.vandonkelaar import POINTS  # noqa: E402

DEC = HERE / "data" / "processed" / "decomp"
PIN = HERE / "data" / "processed" / "pinn_inputs"
FECT = HERE / "data" / "external" / "purpleair" / "processed" / \
    "fect_kandy_calibrated_hourly.parquet"
VAND_CSV = HERE / "data" / "processed" / "stage1_v3" / "vandonkelaar_kandy_annual.csv"

S_PERIOD = range(2019, 2024)          # match the satellite S_emit period
FECT_COL = "pm25_observed_barkjohn_clim_rh"


# ──────────────────────────────────────────────────────────────────────────
def load_grid_and_satellite():
    d = np.load(DEC / "S_emit_kandy.npz")
    lats, lons = d["lats"], d["lons"]
    S_sat = d["S_emit"]               # (16,16) VanD multiplier, mean 1
    return lats, lons, S_sat


def regrid_to(lats, lons, src_lat2d, src_lon2d, src_val2d):
    """Bilinear-resample a source 2-D field onto the canonical lat/lon lattice."""
    LON, LAT = np.meshgrid(lons, lats)
    pts = np.column_stack([src_lat2d.ravel(), src_lon2d.ravel()])
    out = griddata(pts, src_val2d.ravel(), (LAT, LON), method="linear")
    nn = griddata(pts, src_val2d.ravel(), (LAT, LON), method="nearest")
    out[np.isnan(out)] = nn[np.isnan(out)]
    return out


def emission_index(lats, lons):
    """Combined road+NTL emission-intensity index on the canonical grid (z-mean)."""
    ntl = np.load(PIN / "kandy_viirs_ntl_stations.npz")
    road = np.load(PIN / "kandy_road_kernel_100m.npz")
    NTL = regrid_to(lats, lons, ntl["lat_grid"], ntl["lon_grid"], ntl["NTL_log"])
    ROAD = regrid_to(lats, lons, road["lat_grid"], road["lon_grid"], road["R"])

    def z(a):
        return (a - np.nanmean(a)) / (np.nanstd(a) + 1e-9)
    from scipy.ndimage import gaussian_filter
    # Light spatial smoothing so the emission index reads as a coherent
    # core/periphery structure rather than the salt-and-pepper of the raw
    # road network at ~1 km (the core is a contiguous zone, not isolated pixels).
    E = gaussian_filter(0.5 * z(NTL) + 0.5 * z(ROAD), sigma=1.0)
    return E, NTL, ROAD


def akurana_anchor():
    """Akurana calibrated level + its ratio band to the basin level L."""
    df = pd.read_parquet(FECT, columns=["sensor_name", "datetime_utc", FECT_COL])
    df["year"] = pd.to_datetime(df["datetime_utc"]).dt.year
    ak = df[df.sensor_name == "FECT_Akurana"]
    v = pd.read_csv(VAND_CSV).set_index("year")["L_corrected"]
    per_year = {}
    for y in S_PERIOD:
        a = ak[ak.year == y][FECT_COL].mean()
        if np.isfinite(a) and y in v.index:
            per_year[y] = (a, v.loc[y], a / v.loc[y])
    ak_mean = ak[ak.year.isin(S_PERIOD)][FECT_COL].mean()
    L_mean = float(v.loc[list(S_PERIOD)].mean())
    rA = ak_mean / L_mean
    rA_band = [per_year[y][2] for y in per_year]
    return ak_mean, L_mean, rA, (min(rA_band), max(rA_band)), per_year


# ──────────────────────────────────────────────────────────────────────────
def build_surface(E, f_core, f_high, m_peri, m_high):
    """3-tier mass-balance surface (multipliers, area-mean = 1).

    Tiers by emission-index percentile: top f_core = core, bottom f_high =
    highland, the middle = peri-urban (anchored to Akurana, m_peri). Core
    multiplier m_core is the residual that makes the area mean exactly 1.
    Returns (S_UI, tier_id, m_core).
    """
    q_core = np.nanquantile(E, 1 - f_core)
    q_high = np.nanquantile(E, f_high)
    tier = np.full(E.shape, 1, dtype=int)      # 1 = peri-urban (default)
    tier[E >= q_core] = 2                       # 2 = core
    tier[E <= q_high] = 0                       # 0 = highland
    fc = np.mean(tier == 2)
    fh = np.mean(tier == 0)
    fp = np.mean(tier == 1)
    # mass balance: fc*m_core + fp*m_peri + fh*m_high = 1
    m_core = (1.0 - fp * m_peri - fh * m_high) / max(fc, 1e-6)
    S = np.where(tier == 2, m_core, np.where(tier == 0, m_high, m_peri)).astype(float)
    S = S / np.nanmean(S)                        # enforce mean 1 exactly
    return S, tier, m_core, (fc, fp, fh)


def main():
    lats, lons, S_sat = load_grid_and_satellite()
    E, NTL, ROAD = emission_index(lats, lons)
    ak_mean, L_mean, rA, rA_band, per_year = akurana_anchor()

    print("── Akurana anchor (2019–2023) ──")
    for y, (a, L, r) in per_year.items():
        print(f"   {y}: Akurana {a:5.2f}  L {L:5.2f}  r_A {r:.2f}")
    print(f"   period: Akurana {ak_mean:.2f}  L {L_mean:.2f}  r_A {rA:.3f}  "
          f"band [{rA_band[0]:.2f}, {rA_band[1]:.2f}]")

    # sanity: where do the known points land in the emission index?
    def at(la, lo, A):
        i = int(np.argmin(np.abs(lats - la))); j = int(np.argmin(np.abs(lons - lo)))
        return A[i, j]
    pct = lambda v: float((E < v).mean() * 100)
    print("\n── emission-index percentile of known points ──")
    for name in ["city", "nifs", "hantana_fect"]:
        la, lo = POINTS[name]
        print(f"   {name:14s} E pctile {pct(at(la, lo, E)):5.1f}")

    f_core, f_high = 0.15, 0.45
    NIFS_OBS = 24.52                 # KOALA/NIFS 2019 — the one near-core observation

    # ── Mode A: mass-balance (force area-mean = L). The reductio. ──
    S_A, tier, m_core_A, fr = build_surface(E, f_core, f_high, rA, 0.80 * rA)
    print("\n── Mode A: mass-balance, area-mean forced to L ──")
    print(f"   tiers core {fr[0]:.2f} / peri {fr[1]:.2f} / highland {fr[2]:.2f}")
    print(f"   CORE residual = {m_core_A:.2f}×L = {m_core_A*L_mean:.0f} µg/m³  "
          f"→ absurd; but NIFS (a core pixel, 98.8 pctile) is observed at "
          f"{NIFS_OBS:.1f}. ⇒ L is NOT the area-mean; it is a core-point level.")

    # ── Mode B: anchor all tiers from observation/prior, FLOAT the area-mean ──
    # core ← NIFS (24.5), peri ← Akurana, highland ← prior fraction of peri.
    def anchored(f_core, f_high, C_core, C_peri, C_high):
        q_core = np.nanquantile(E, 1 - f_core); q_high = np.nanquantile(E, f_high)
        tier = np.full(E.shape, 1, dtype=int)
        tier[E >= q_core] = 2; tier[E <= q_high] = 0
        absfield = np.where(tier == 2, C_core, np.where(tier == 0, C_high, C_peri))
        area_mean = float(absfield.mean())
        S = absfield / area_mean                       # multiplier, mean 1
        return S, tier, area_mean

    C_core, C_peri = NIFS_OBS, ak_mean
    C_high = 0.80 * ak_mean
    S_UI, tier, area_mean = anchored(f_core, f_high, C_core, C_peri, C_high)
    core_mult = S_UI[tier == 2].mean()
    print("\n── Mode B: observation-anchored, area-mean floats ──")
    print(f"   anchors  core(NIFS) {C_core:.1f}  peri(Akurana) {C_peri:.1f}  "
          f"highland(prior) {C_high:.1f} µg/m³")
    print(f"   IMPLIED basin area-mean = {area_mean:.1f} µg/m³  "
          f"(vs current decomp L = {L_mean:.1f}) → off-core field over-stated "
          f"by ~{L_mean/area_mean:.2f}× if FECT is taken at face value")
    print(f"   S_emit_UI multipliers  core {core_mult:.2f}  "
          f"peri {C_peri/area_mean:.2f}  highland {C_high/area_mean:.2f} (mean 1)")
    print(f"   OBSERVED valley-floor core/peri contrast = "
          f"{C_core/C_peri:.2f}×   (satellite S_emit {S_sat.max()/S_sat.min():.2f}×)")

    # ── UQ ensemble on Mode B (fractions × highland prior × r_A/Akurana band) ──
    rows = []
    for fc in (0.10, 0.15, 0.22):
        for fh in (0.35, 0.45, 0.55):
            for rh in (0.65, 0.80, 0.95):
                for ak in (rA_band[0]*L_mean, ak_mean, rA_band[1]*L_mean):
                    S, t, am = anchored(fc, fh, NIFS_OBS, ak, rh*ak)
                    rows.append(dict(f_core=fc, f_high=fh, rel_high=rh, akurana=ak,
                                     area_mean=am, core_mult=S[t==2].mean(),
                                     core_peri=NIFS_OBS/ak, overstate=L_mean/am))
    ens = pd.DataFrame(rows)
    print("\n── Mode-B UQ ensemble ──")
    print(f"   implied area-mean  median {ens.area_mean.median():.1f}  "
          f"[p10 {ens.area_mean.quantile(.1):.1f}, p90 {ens.area_mean.quantile(.9):.1f}]")
    print(f"   core multiplier    median {ens.core_mult.median():.2f}  "
          f"[p10 {ens.core_mult.quantile(.1):.2f}, p90 {ens.core_mult.quantile(.9):.2f}]")
    print(f"   off-core overstatement median {ens.overstate.median():.2f}×")

    np.savez(DEC / "S_emit_urban_increment.npz",
             S_emit_UI=S_UI, tier=tier, E=E, lats=lats, lons=lons,
             core_mult=core_mult, area_mean_implied=area_mean, L_decomp=L_mean,
             C_core=C_core, C_peri=C_peri, C_high=C_high, ak_mean=ak_mean, r_A=rA,
             core_blowup_modeA=m_core_A*L_mean)
    ens.to_csv(DEC / "s_emit_urban_increment_summary.csv", index=False)
    print(f"\nWrote {DEC/'S_emit_urban_increment.npz'}")
    print(f"Wrote {DEC/'s_emit_urban_increment_summary.csv'}")


if __name__ == "__main__":
    main()
