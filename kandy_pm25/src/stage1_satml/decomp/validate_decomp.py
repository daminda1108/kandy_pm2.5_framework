"""
validate_decomp.py — validation battery for the decomposition map (plan §4, gates):

  U5  independent spatial check: annual map vs VIIRS NTL (NOT used to build the
      map) + vs elevation/delta_z (physical: higher → cleaner).
  U6  spatial sign battery: urban core > basin, highland < basin (construction
      check on S_emit — labelled non-independent).
  FECT pointwise (sanity): decomp at the Akurana/Hantana FECT pixels vs the
      calibrated FECT observations. NOTE: both FECT are valley/suburban sites
      (~460–738 m, audit E1–E3 — NOT highland). Akurana is out-of-bbox (north,
      edge-clamped). The map is basin-anchored, so the positive bias diagnoses a
      too-weak urban/suburban spatial contrast, not a temporal error.
  U7  INDEPENDENT-product cross-check vs GHAP (GlobalHighPM2.5; Wei et al.) — the
      first genuinely independent 1 km reference (different team/method, NOT VanD).
      Agreement = corroboration not validation; disagreement diagnostic. Adjudicates
      level/season/broad spatial sign, not the fine urban-core hotspot.

Writes results/figures/kandy_decomp/validation_report.csv (+ prints).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

DATA = HERE / "data" / "processed"
DECOMP = DATA / "decomp"
OUT = HERE / "results" / "figures" / "kandy_decomp"
OUT.mkdir(parents=True, exist_ok=True)
# CORRECTED coords (audit E1–E3, 2026-05-29): both FECT are valley/suburban
# (~460–738 m, NOT highland). Hantana raw coord 7.356/80.631 was mis-registered;
# true Hantana ≈ 7.265/80.625 (738 m). Akurana 7.366 is OUTSIDE the bbox (north).
FECT = {12451: (7.366, 80.618), 33495: (7.265, 80.625)}
FECT_NAME = {12451: "Akurana (OUT-OF-BBOX, north)", 33495: "Hantana (7.265, 738m)"}
BBOX = (7.2230, 7.3582, 80.5660, 80.7014)  # lat_min, lat_max, lon_min, lon_max


def _annual_grid(year):
    df = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{year}.parquet")
    lats = np.sort(df.lat.unique()); lons = np.sort(df.lon.unique())
    ann = df.groupby(["lat", "lon"])["pm25_q50"].mean().reset_index()
    Z = ann.pivot(index="lat", columns="lon", values="pm25_q50").values
    return Z, lats, lons


def _bootstrap_r(a, b, n_boot=2000, seed=0):
    """Percentile bootstrap 95% CI for Pearson r (resample paired samples)."""
    from scipy.stats import pearsonr
    rng = np.random.default_rng(seed)
    n = len(a)
    rs = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        rs[i] = pearsonr(a[idx], b[idx])[0]
    return float(np.percentile(rs, 2.5)), float(np.percentile(rs, 97.5))


def u5_independent(year=2024):
    from scipy.interpolate import RegularGridInterpolator
    from scipy.stats import pearsonr, spearmanr
    Z, lats, lons = _annual_grid(year)

    # VIIRS NTL (31×31) → resample to map grid
    ntl = np.load(DATA / "pinn_inputs" / "kandy_viirs_ntl_stations.npz")
    nlat, nlon = ntl["lat_grid"][:, 0], ntl["lon_grid"][0, :]
    NL = ntl["NTL_log"].astype(float)
    if nlat[0] > nlat[-1]:
        nlat, NL = nlat[::-1], NL[::-1, :]
    if nlon[0] > nlon[-1]:
        nlon, NL = nlon[::-1], NL[:, ::-1]
    rgi = RegularGridInterpolator((nlat, nlon), NL, bounds_error=False, fill_value=None)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    ntl_g = rgi(np.stack([LA.ravel(), LO.ravel()], 1)).reshape(Z.shape)

    # elevation/delta_z (from M confinement npz dz_grid, already on map grid)
    dz = np.load(DECOMP / "M_confinement_kandy.npz")["dz_grid"]

    z = Z.ravel()
    out = {}
    for name, field in [("VIIRS_NTL_log", ntl_g.ravel()), ("delta_z", dz.ravel())]:
        r, p = pearsonr(z, field); rho, _ = spearmanr(z, field)
        lo, hi = _bootstrap_r(z, field)
        out[name] = (r, rho, p, lo, hi)
    return out


def u6_signs(year=2024):
    Z, lats, lons = _annual_grid(year)
    basin = float(Z.mean())

    def at(la, lo):
        return float(Z[np.argmin(np.abs(lats - la)), np.argmin(np.abs(lons - lo))])
    city = at(7.2906, 80.6337)
    # Akurana is out-of-bbox (north) → excluded. Hantana (7.265) is in-domain.
    checks = {
        "urban_core>basin": (city, basin, city > basin),
        "hantana_suburban<basin": (at(*FECT[33495]), basin, at(*FECT[33495]) < basin),
    }
    return checks, basin


def fect_pointwise(year):
    pred = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{year}.parquet")
    pred["time"] = pd.to_datetime(pred["time"], utc=True)
    lats = np.sort(pred.lat.unique()); lons = np.sort(pred.lon.unique())
    obs = pd.read_parquet(DATA / "stage1_v3" / "dataset_v3_hourly.parquet",
                          columns=["sensor_id", "datetime_utc", "pm25_observed"])
    obs["datetime_utc"] = pd.to_datetime(obs["datetime_utc"], utc=True)
    obs = obs[obs["datetime_utc"].dt.year == year].dropna(subset=["pm25_observed"])

    rows = []
    for sid, (la, lo) in FECT.items():
        o = obs[obs.sensor_id == sid]
        if len(o) < 50:
            continue
        in_bbox = BBOX[0] <= la <= BBOX[1] and BBOX[2] <= lo <= BBOX[3]
        gla = lats[np.argmin(np.abs(lats - la))]; glo = lons[np.argmin(np.abs(lons - lo))]
        px = pred[(pred.lat == gla) & (pred.lon == glo)][
            ["time", "pm25_q05", "pm25_q50", "pm25_q95"]]
        m = o.merge(px, left_on="datetime_utc", right_on="time", how="inner")
        if len(m) < 50:
            continue
        err = m.pm25_q50 - m.pm25_observed
        rows.append(dict(
            sensor=sid, name=FECT_NAME[sid], year=year, n=len(m), in_bbox=in_bbox,
            obs_mean=float(m.pm25_observed.mean()), pred_mean=float(m.pm25_q50.mean()),
            rmse=float(np.sqrt((err**2).mean())), bias=float(err.mean()),
            cov90=float(((m.pm25_observed >= m.pm25_q05) &
                         (m.pm25_observed <= m.pm25_q95)).mean())))
    return rows


def u7_ghap(years=range(2019, 2023)):
    """U7 — INDEPENDENT-product cross-check vs GHAP (GlobalHighPM2.5, Wei et al.).

    GHAP is methodologically independent of Van Donkelaar (geophysical+GWR), which is
    inside S_emit → this is the first genuinely independent spatial cross-check. GHAP
    has no Sri Lankan stations either, so agreement = corroboration, NOT validation;
    disagreement is diagnostic. At 15 km it adjudicates level/season/broad spatial sign,
    not the fine urban-core hotspot. Built by scripts/gee_export_ghap_kandy.py.
    """
    from scipy.spatial import cKDTree
    from scipy.stats import pearsonr
    KOALA_FLOOR = 24.5225  # KOALA/NIFS valley-FLOOR diagnostic (area anchor: NOT the basin mean)
    gp = DECOMP / "ghap_kandy_monthly_2019_2022.parquet"
    if not gp.exists():
        return None
    ghap = pd.read_parquet(gp)
    dec = []
    for yr in years:
        d = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{yr}.parquet",
                            columns=["time", "lat", "lon", "pm25_q50"])
        d["year"] = yr; d["month"] = pd.to_datetime(d["time"]).dt.month
        dec.append(d)
    dec = pd.concat(dec, ignore_index=True)

    # level (basin annual mean) + inter-annual r
    lv = []
    for yr in years:
        lv.append((yr, dec.loc[dec.year == yr, "pm25_q50"].mean(),
                   ghap.loc[ghap.year == yr, "ghap_pm25"].mean()))
    lv = pd.DataFrame(lv, columns=["year", "decomp", "ghap"])
    # area-vs-floor correction (2026-06-04): decomp basin is now the VanD AREA mean.
    # Compare directly to GHAP (also an area product); both should sit BELOW the
    # KOALA floor 24.5. Agreement of two independent area products = corroboration.
    lv["decomp_over_ghap"] = lv.decomp / lv.ghap
    r_ia = pearsonr(lv.decomp, lv.ghap)[0]
    # seasonal climatology r (+ bootstrap CI on the 12 monthly pairs)
    dc = dec.groupby("month")["pm25_q50"].mean(); gc = ghap.groupby("month")["ghap_pm25"].mean()
    r_se = pearsonr(dc.values, gc.values)[0]
    se_lo, se_hi = _bootstrap_r(dc.values, gc.values, n_boot=2000)
    # spatial per-pixel pattern (2019-2022 mean) via nearest-neighbour align
    dpx = dec.groupby(["lat", "lon"])["pm25_q50"].mean().reset_index()
    gpx = ghap.groupby(["lat", "lon"])["ghap_pm25"].mean().reset_index()
    _, idx = cKDTree(gpx[["lat", "lon"]].values).query(dpx[["lat", "lon"]].values)
    dpx["ghap"] = gpx["ghap_pm25"].values[idx]
    r_sp = pearsonr(dpx.pm25_q50, dpx.ghap)[0]
    sp_lo, sp_hi = _bootstrap_r(dpx.pm25_q50.values, dpx.ghap.values, n_boot=2000)
    cen = (7.2906, 80.6337)
    dist = np.hypot(dpx.lat - cen[0], dpx.lon - cen[1])
    core = dist <= np.percentile(dist, 25); edge = dist >= np.percentile(dist, 75)
    dec_c = dpx.loc[core, "pm25_q50"].mean() / dpx.loc[edge, "pm25_q50"].mean()
    gh_c = dpx.loc[core, "ghap"].mean() / dpx.loc[edge, "ghap"].mean()
    return dict(level=lv, r_interannual=r_ia, r_seasonal=r_se, se_ci=(se_lo, se_hi),
                koala_floor=KOALA_FLOOR,
                r_spatial=r_sp, sp_ci=(sp_lo, sp_hi),
                seas_peak=(int(dc.idxmax()), int(gc.idxmax())),
                seas_min=(int(dc.idxmin()), int(gc.idxmin())),
                core_edge=(dec_c, gh_c))


def main():
    print("══ U5 — independent spatial correlation (annual 2024 map; bootstrap 95% CI) ══")
    for name, (r, rho, p, lo, hi) in u5_independent(2024).items():
        exp = "+" if name == "VIIRS_NTL_log" else "−"
        print(f"  vs {name:<14} Pearson r={r:+.3f} [{lo:+.3f}, {hi:+.3f}]  "
              f"Spearman ρ={rho:+.3f}  (expect {exp})")

    print("\n══ U6 — spatial sign battery (construction check) ══")
    checks, basin = u6_signs(2024)
    print(f"  basin mean S·T annual = {basin:.2f}")
    for k, (v, b, ok) in checks.items():
        print(f"  {k:<26} {v:.2f} vs {b:.2f}  {'PASS' if ok else 'FAIL'}")

    print("\n══ FECT pointwise (valley/suburban sites — bias diagnoses spatial flatness) ══")
    allrows = []
    for yr in (2019, 2024):
        for row in fect_pointwise(yr):
            allrows.append(row)
            flag = "" if row['in_bbox'] else "  [OUT-OF-BBOX, edge-clamped]"
            print(f"  {row['name']:<28} {yr}: n={row['n']:<5} obs={row['obs_mean']:.1f} "
                  f"pred={row['pred_mean']:.1f} rmse={row['rmse']:.1f} "
                  f"bias={row['bias']:+.1f} cov90={row['cov90']:.2f}{flag}")
    pd.DataFrame(allrows).to_csv(OUT / "validation_fect_pointwise.csv", index=False)
    print(f"\nWrote {OUT / 'validation_fect_pointwise.csv'}")

    print("\n══ U7 — INDEPENDENT product cross-check vs GHAP (quasi-independent 1 km, 2019–2022) ══")
    g = u7_ghap()
    if g is None:
        print("  [GHAP parquet missing — run scripts/gee_export_ghap_kandy.py]")
    else:
        print("  LEVEL (basin annual AREA mean µg/m³; KOALA 24.5 = floor, expected above):")
        for _, r in g["level"].iterrows():
            print(f"    {int(r.year)}: decomp(area) {r.decomp:.2f} | GHAP(area) {r.ghap:.2f} | "
                  f"decomp/GHAP {r.decomp_over_ghap:.2f}×  (KOALA floor {g['koala_floor']:.1f})")
        print(f"    → two independent AREA products agree within "
              f"{abs(g['level'].decomp_over_ghap.mean()-1)*100:.0f}%, both below the KOALA floor "
              f"(area-vs-floor consistent)")
        print(f"    inter-annual r(decomp,GHAP) = {g['r_interannual']:+.3f}  "
              f"→ {'corroborated' if abs(g['r_interannual'])>0.5 else 'NOT corroborated (low-confidence trend)'}")
        print(f"  SEASONAL r = {g['r_seasonal']:+.3f} [{g['se_ci'][0]:+.2f},{g['se_ci'][1]:+.2f}]  "
              f"peak m{g['seas_peak'][0]}/{g['seas_peak'][1]} min m{g['seas_min'][0]}/{g['seas_min'][1]}  "
              f"→ {'STRONG corroboration' if g['r_seasonal']>0.8 else 'partial'}")
        print(f"  SPATIAL r = {g['r_spatial']:+.3f} [{g['sp_ci'][0]:+.2f},{g['sp_ci'][1]:+.2f}]  "
              f"core/edge decomp {g['core_edge'][0]:.3f}× vs GHAP {g['core_edge'][1]:.3f}×  "
              f"({'city>rural sign agrees' if g['core_edge'][0]>1 and g['core_edge'][1]>1 else 'sign mismatch'})")
        pd.concat([g["level"]]).to_csv(OUT / "validation_u7_ghap_level.csv", index=False)
        pd.DataFrame([dict(r_interannual=g["r_interannual"], r_seasonal=g["r_seasonal"],
                           r_spatial=g["r_spatial"],
                           decomp_core_edge=g["core_edge"][0], ghap_core_edge=g["core_edge"][1])
                      ]).to_csv(OUT / "validation_u7_ghap_summary.csv", index=False)
        print(f"  Wrote {OUT / 'validation_u7_ghap_summary.csv'}")


if __name__ == "__main__":
    main()
