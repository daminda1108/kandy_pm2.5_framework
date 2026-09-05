"""design_sensor_network.py -- where to put sensors in Kandy, and why there.

THE PREMISE, AND IT IS FALSIFIABLE. This project has measured a spatial ceiling six times: a
learned within-city pattern does not beat built-up land cover at 2.4 km by more than 0.130 in
rank correlation. Chapter 8 argues the cause is a change of support. But a second, cheaper
explanation cannot be ruled out: every network scored so far is a CONVENIENCE SAMPLE, sited for
compliance, access, power and security, never for contrast. Published land-use regression reaches
R^2 0.43 to 0.83 because those campaigns site deliberately. So this design is an experiment. If a
deliberately contrasted network still yields a low rank correlation, the information-limited
reading is confirmed far more strongly than six convenience-sample nulls could confirm it.

WHAT THE PRESENT NETWORK MISSES. The fine emission surface spans 65x from its 10th to 90th
percentile at 94 m. The existing fixed records sit between the 61st and 100th percentile: the
lower 61 per cent is unsampled and one of the two sensors is outside the domain entirely.

────────────────────────────────────────────────────────────────────────────────────────────
THE PHYSICS THE DESIGN MUST SAMPLE, not just the emissions
────────────────────────────────────────────────────────────────────────────────────────────

A design stratified on emissions alone samples where the sources are and learns nothing about
what the atmosphere does with them. Kandy is a valley, and the processes that set concentration
there are as spatial as the sources:

  NOCTURNAL DRAINAGE. Cold air runs downslope after sunset and pools. The diagnostic wind field
  varies 3.2x in nocturnal speed across this domain, and its convergence marks where that pooled
  air accumulates. Those sinks are the highest-concentration places in the city at night and the
  model predicts one at Katugastota, down-valley of the core. That prediction has never been
  tested against an instrument.

  INVERSION AND CONFINEMENT. `delta_z` is depth below the surrounding terrain, which is what
  traps a nocturnal inversion. The model imposes a confinement term built from it and has never
  validated that term against an instrument. Sky view factor would be the natural second
  covariate for the radiative cooling that forms an inversion, and it is measured and then
  DROPPED for the reason given at DESIGN_COVARS: on this domain it is very nearly a constant.

  VENTILATION CONTRAST. A site whose ventilation swings between day and night experiences the
  diurnal cycle the model predicts. One that does not, does not. Sampling both is what makes the
  diurnal prediction falsifiable.

  THE VERTICAL GRADIENT, WHICH IS THE ONE NOBODY SAMPLES. This project's dynamic-transport null
  was diagnosed as a data problem rather than a physics problem: monitored stations worldwide sit
  on the valley FLOOR, so they never straddle the floor-to-ridge gradient, and the one city with
  700 m of station relief showed the expected signs. Kandy has 846 m of relief inside the domain.
  A deliberate floor-to-ridge transect is therefore the single most valuable physical addition
  available here, and it gets its own stratum rather than being left to chance.

LOGISTICS ENTERS AS A CONSTRAINT, NEVER AS AN OBJECTIVE. Sites must be reachable to be serviced,
so candidates further than ACCESS_MAX_M from the road network are removed BEFORE the design is
optimised. Making access an objective rather than a constraint is precisely how convenience
sampling happens, and it is what this design exists to avoid.

────────────────────────────────────────────────────────────────────────────────────────────
FIVE STRATA. Keeping them separate is the point: a site used to fit a model cannot validate it.
────────────────────────────────────────────────────────────────────────────────────────────

  A  ANCHOR     one reference-grade instrument. Everything else calibrates against it.
  B  DESIGN     spans the joint emission-AND-physics covariate space by conditioned Latin
                hypercube, so the network straddles the gradients the model claims.
  C  PAIRED     microsite triplets INSIDE single model cells, at the separations the Kandy
                transect showed matter. Measures the within-cell distribution.
  E  VERTICAL   a floor-to-ridge transect. Tests the confinement and inversion physics that
                every network on Earth is currently blind to.
  D  RECEPTOR   schools and health facilities. Chosen for who is there, HELD OUT of fitting.

Usage: python scripts/design_sensor_network.py [--n-design 12] [--n-pairs 3] [--n-vertical 5]
Out:   data/processed/decomp/sensor_design_kandy.csv
       data/processed/decomp/sensor_design_summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
DEC = REPO / "data" / "processed" / "decomp"
PIN = REPO / "data" / "processed" / "pinn_inputs"
OUT = DEC / "sensor_design_kandy.csv"
OUT_JSON = DEC / "sensor_design_summary.json"

SEED = 20260905
CELL_M = 998.0                    # the delivered reporting cell
PAIR_SEPARATIONS_M = [100, 300]   # the Kandy transect resolved 110 -> 4 ug/m3 over 300 m
MIN_SEP_M = 400.0                 # design sites must not crowd; pairs are the exception
ACCESS_MAX_M = 400.0              # feasibility screen: must be serviceable from a road
FLOOR_WIN = 31                    # ~3 km window defining the local valley floor

# The covariates the design stratum spans. Emission and population are the human footprint;
# the rest is what the atmosphere does with it.
#
# SVF IS DELIBERATELY ABSENT. Sky view factor is the natural covariate for radiative cooling and
# therefore for inversion formation, and it was in the first version of this list. Measured on
# this domain it has a coefficient of variation of 0.023 and an interquartile range of 0.021 on
# a 0-1 scale: it is very nearly a constant, because the ridges that would occlude the sky sit
# 5-10 km away, beyond the scan radius. The project recorded the same thing in a different
# context and dropped it there too. A near-constant covariate in a conditioned Latin hypercube
# is worse than useless: it consumes one of the optimiser's dimensions and dilutes the ones
# that carry contrast. `delta_z` carries the confinement signal on its own.
DESIGN_COVARS = ["E", "POP", "z_above_floor", "delta_z", "vent_night", "conv_night",
                 "vent_ratio"]


def m_per_deg(lat0: float):
    return 111_000.0, 111_000.0 * np.cos(np.radians(lat0))


def _regrid(A, slat, slon, tlat, tlon):
    """Nearest-neighbour onto the target grid. Both grids are regular, so this is exact enough."""
    i = np.abs(np.asarray(slat)[:, None] - np.asarray(tlat)[None, :]).argmin(0)
    j = np.abs(np.asarray(slon)[:, None] - np.asarray(tlon)[None, :]).argmin(0)
    return A[np.ix_(i, j)]


def load_layers():
    """Every covariate on the common 94 m emission grid."""
    from scipy.ndimage import uniform_filter, minimum_filter

    t = np.load(DEC / "S_traffic_kandy.npz")
    E, lat, lon = t["E_fine"], t["fine_lat"], t["fine_lon"]

    e = np.load(PIN / "kandy_elev_grid_100m.npz")
    z, zlat, zlon = e["elev"], e["lat_grid"], e["lon_grid"]
    if np.ndim(zlat) == 2:
        zlat, zlon = zlat[:, 0], zlon[0, :]
    Z = _regrid(z, zlat, zlon, lat, lon)

    p = np.load(DEC / "population_kandy.npz")
    POP = _regrid(p["pop"], p["lats"], p["lons"], lat, lon)

    # terrain confinement and sky view, from the model's own layers
    tp = np.load(PIN / "kandy_terrain_tpi_svf_100m.npz")
    tlat_, tlon_ = tp["lat_grid"], tp["lon_grid"]
    if np.ndim(tlat_) == 2:
        tlat_, tlon_ = tlat_[:, 0], tlon_[0, :]
    DZ = _regrid(np.asarray(tp["delta_z"], float), tlat_, tlon_, lat, lon)
    SVF = _regrid(np.asarray(tp["svf"], float), tlat_, tlon_, lat, lon)

    # height above the LOCAL valley floor: the axis no monitoring network samples
    floor = minimum_filter(Z, size=FLOOR_WIN, mode="nearest")
    ZAF = Z - floor

    # ── flow physics, from the WindNinja diagnostic library ───────────────────────────────
    wl = np.load(PIN / "windninja_library.npz")
    regs = [str(r).lower() for r in wl["regimes"]]
    ni = regs.index("night") if "night" in regs else 0
    di = regs.index("day") if "day" in regs else 1
    wlat, wlon = wl["lats"], wl["lons"]

    def regime(idx):
        u = wl["u"][:, :, idx].mean(axis=(0, 1))
        v = wl["v"][:, :, idx].mean(axis=(0, 1))
        return u, v

    un, vn = regime(ni)
    ud, vd = regime(di)
    spd_n, spd_d = np.hypot(un, vn), np.hypot(ud, vd)
    # Convergence: positive where the nocturnal drainage flow piles air up.
    #
    # SMOOTHED AT SOURCE, and this is not cosmetic. The wind library is 64x64 over 15 km, so a
    # cell is about 230 m; a finite-difference gradient on it is dominated by cell-to-cell
    # numerical noise. Regridding that to 94 m and treating it as a covariate would have the
    # design chasing artefacts of the differencing scheme, and would advertise a resolution the
    # flow field does not have. The smoothing window is one native cell.
    conv_n = -(np.gradient(un, axis=1) + np.gradient(vn, axis=0))
    conv_n = uniform_filter(conv_n, size=3, mode="nearest")

    VENT_N = _regrid(spd_n, wlat, wlon, lat, lon)
    CONV_N = _regrid(conv_n, wlat, wlon, lat, lon)
    VENT_R = _regrid(spd_d / np.clip(spd_n, 1e-6, None), wlat, wlon, lat, lon)

    return dict(E=E, Z=Z, POP=POP, delta_z=DZ, svf=SVF, z_above_floor=ZAF,
                vent_night=VENT_N, conv_night=CONV_N, vent_ratio=VENT_R,
                DZ=DZ, lat=lat, lon=lon)


def access_distance(lat, lon):
    """Metres to the nearest mapped road. A feasibility SCREEN, never a design objective."""
    import json as _json
    from scipy.spatial import cKDTree
    mlat, mlon = m_per_deg(float(np.mean(lat)))
    pts = []
    with open(DEC / "osm_kandy" / "roads.geojson", encoding="utf-8") as fh:
        gj = _json.load(fh)
    for ft in gj.get("features", []):
        g = ft.get("geometry") or {}
        cs = g.get("coordinates") or []
        segs = cs if g.get("type") == "MultiLineString" else [cs]
        for seg in segs:
            for c in seg:
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    pts.append((c[1] * mlat, c[0] * mlon))
    if not pts:
        return None
    tree = cKDTree(np.array(pts))
    LON, LAT = np.meshgrid(lon, lat)
    q = np.column_stack([(LAT * mlat).ravel(), (LON * mlon).ravel()])
    return tree.query(q)[0].reshape(LAT.shape)


def clhs(X: np.ndarray, n: int, seed: int, n_iter: int = 12000):
    """Conditioned Latin hypercube: pick n rows whose MARGINALS reproduce the population's.

    That is the property wanted here. The network should straddle every gradient the model
    claims to represent rather than cluster where access is easy. Standard in environmental
    survey design for exactly this problem.
    """
    rng = np.random.default_rng(seed)
    N, k = X.shape
    edges = [np.quantile(X[:, j], np.linspace(0, 1, n + 1)) for j in range(k)]

    def cost(idx):
        return sum(np.abs(np.histogram(X[idx, j], bins=edges[j])[0] - 1).sum()
                   for j in range(k))

    idx = rng.choice(N, n, replace=False)
    best, bc = idx.copy(), cost(idx)
    T = 1.0
    for _ in range(n_iter):
        cand = idx.copy()
        cand[rng.integers(n)] = rng.integers(N)
        if len(set(cand)) < n:
            continue
        cc = cost(cand)
        if cc < bc or rng.random() < np.exp(-(cc - bc) / max(T, 1e-9)):
            idx = cand
            if cc < bc:
                best, bc = cand.copy(), cc
        T *= 0.9995
        if bc == 0:
            break
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-design", type=int, default=12)
    ap.add_argument("--n-pairs", type=int, default=3)
    ap.add_argument("--n-vertical", type=int, default=5)
    ap.add_argument("--n-receptor", type=int, default=8)
    a = ap.parse_args()

    L = load_layers()
    lat, lon = L["lat"], L["lon"]
    mlat, mlon = m_per_deg(float(lat.mean()))
    LON, LAT = np.meshgrid(lon, lat)

    print("=== Kandy sensor network design ===")
    ACC = access_distance(lat, lon)
    finite = np.ones_like(L["E"], bool)
    for k in DESIGN_COVARS + ["Z", "svf"]:
        finite &= np.isfinite(L[k])
    feasible = finite & (ACC <= ACCESS_MAX_M) if ACC is not None else finite
    print(f"    {finite.sum():,} cells at ~94 m; {feasible.sum():,} within "
          f"{ACCESS_MAX_M:.0f} m of a road and therefore serviceable "
          f"({100*feasible.sum()/finite.sum():.0f}%)")
    print("    logistics is a CONSTRAINT on the candidate set, never a design objective")

    df = pd.DataFrame({k: L[k][feasible] for k in DESIGN_COVARS + ["Z", "svf"]})
    df["lat"], df["lon"] = LAT[feasible], LON[feasible]
    # percentile against the WHOLE domain, not just the feasible subset, so coverage claims
    # are about the city rather than about the part of it we can reach
    allE = np.sort(L["E"][finite])
    df["E_pct"] = 100 * np.searchsorted(allE, df.E.to_numpy()) / len(allE)

    print(f"\n    physical spread available to the design:")
    for k, unit in [("z_above_floor", "m above local floor"), ("delta_z", "m confinement"),
                    ("vent_night", "m/s nocturnal"), ("conv_night", "convergence"),
                    ("svf", "sky view")]:
        v = df[k]
        print(f"      {k:14} {v.min():8.2f} to {v.max():8.2f}   {unit}")

    # ── A. anchor ─────────────────────────────────────────────────────────────────────────
    sc = (df.POP.rank(pct=True) + df.E.rank(pct=True)).to_numpy()
    anchor = df.iloc[[int(np.argmax(sc))]].assign(
        stratum="A_anchor", role="reference monitor, calibrates the network")

    # ── B. design, cLHS over emission AND physics ─────────────────────────────────────────
    X = df[DESIGN_COVARS].to_numpy(float)
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-12)
    sel = clhs(Xs, a.n_design, SEED)
    design = df.iloc[sel].copy()
    keep = []
    for i in design.index:
        r = design.loc[i]
        if all(np.hypot((r.lat - design.loc[j].lat) * mlat,
                        (r.lon - design.loc[j].lon) * mlon) > MIN_SEP_M for j in keep):
            keep.append(i)
    design = design.loc[keep].assign(stratum="B_design",
                                     role="low-cost, spans emission and flow physics")

    # ── E. vertical transect ──────────────────────────────────────────────────────────────
    # The axis no monitoring network on Earth samples. Sites are taken at rising height above
    # the local valley floor, within one contiguous slope sector so the transect is a gradient
    # rather than a scatter of unrelated hillsides.
    core_lat, core_lon = float(anchor.lat.iloc[0]), float(anchor.lon.iloc[0])
    dist = np.hypot((df.lat - core_lat) * mlat, (df.lon - core_lon) * mlon)
    near = df[(dist > 300) & (dist < 6000)].copy()
    near["zaf"] = near.z_above_floor
    qs = np.linspace(0.02, 0.98, a.n_vertical)
    targets = near.zaf.quantile(qs).to_numpy()
    vert, used_v = [], []
    for tgt in targets:
        cand = near.assign(gap=(near.zaf - tgt).abs()).sort_values("gap")
        for r in cand.itertuples():
            if all(np.hypot((r.lat - u[0]) * mlat, (r.lon - u[1]) * mlon) > MIN_SEP_M
                   for u in used_v):
                used_v.append((r.lat, r.lon))
                vert.append(dict(lat=r.lat, lon=r.lon, E_pct=r.E_pct, stratum="E_vertical",
                                 role=f"vertical transect, {r.zaf:.0f} m above local floor",
                                 z_above_floor=r.zaf))
                break
    vertical = pd.DataFrame(vert)

    # ── C. paired microsites ──────────────────────────────────────────────────────────────
    Egrid = np.where(feasible, L["E"], np.nan)
    gy, gx = np.gradient(Egrid)
    grad = np.hypot(gy, gx)
    g = pd.DataFrame(dict(lat=LAT[feasible], lon=LON[feasible], grad=grad[feasible],
                          E=L["E"][feasible], gy=gy[feasible], gx=gx[feasible])).dropna()
    g = g.sort_values("grad", ascending=False)

    def E_at(la, lo):
        i = int(np.abs(lat - la).argmin()); j = int(np.abs(lon - lo).argmin())
        v = L["E"][i, j]
        return float(v) if np.isfinite(v) else np.nan

    pairs, used = [], []
    for r in g.itertuples():
        if len(used) >= a.n_pairs:
            break
        if any(np.hypot((r.lat - u[0]) * mlat, (r.lon - u[1]) * mlon) < CELL_M for u in used):
            continue
        used.append((r.lat, r.lon))
        pid = f"P{len(used)}"
        norm = np.hypot(r.gy, r.gx) or 1.0
        uy, ux = r.gy / norm, r.gx / norm
        pairs.append(dict(pair_id=pid, lat=r.lat, lon=r.lon, E=r.E, stratum="C_paired",
                          role=f"{pid} anchor member, steepest-gradient cell"))
        for sep in PAIR_SEPARATIONS_M:
            # A REAL, DIFFERENT coordinate. A pair sharing one coordinate is one point recorded
            # twice, which is the artefact the Elangasinghe re-analysis had to withdraw. Offset
            # runs ALONG the gradient so the pair straddles the contrast, not along a contour.
            la, lo = r.lat + (uy * sep) / mlat, r.lon + (ux * sep) / mlon
            same = np.hypot((la - r.lat) * mlat, (lo - r.lon) * mlon) < CELL_M
            pairs.append(dict(pair_id=pid, lat=la, lon=lo, E=E_at(la, lo), stratum="C_paired",
                              role=(f"{pid} offset {sep} m along the gradient, "
                                    f"{'SAME model cell' if same else 'ADJACENT cell'}")))
    paired = pd.DataFrame(pairs)
    if len(paired):
        c = (paired.groupby("pair_id").E.max() /
             paired.groupby("pair_id").E.min().clip(lower=1e-9))
        pair_contrast = (float(c.min()), float(c.max()))
    else:
        pair_contrast = (np.nan, np.nan)

    # ── D. receptors ──────────────────────────────────────────────────────────────────────
    rc = pd.read_csv(DEC / "kandy_receptors_ranked.csv")
    rc = rc[rc.E_pct.notna()].sort_values("E_pct", ascending=False)
    kept = []
    for r in rc.itertuples():
        if all(np.hypot((r.lat - k[0]) * mlat, (r.lon - k[1]) * mlon) > 150.0 for k in kept):
            kept.append((r.lat, r.lon, r.Index))
    rc = rc.loc[[k[2] for k in kept]]
    take = [sub.head(max(1, a.n_receptor // max(rc.group.nunique(), 1)))
            for _, sub in rc.groupby("group")]
    receptor = (pd.concat(take).sort_values("E_pct", ascending=False).head(a.n_receptor)
                .assign(stratum="D_receptor", role="exposure, HELD OUT of model fitting"))

    cols = ["stratum", "role", "lat", "lon", "E_pct"]
    out = pd.concat([
        anchor.assign(name="")[cols + ["name"]],
        design.assign(name="")[cols + ["name"]],
        vertical.assign(name="")[cols + ["name"]] if len(vertical) else None,
        paired.assign(name="", E_pct=np.nan)[cols + ["name"]],
        receptor.assign(name=receptor.name.fillna(""))[cols + ["name"]],
    ], ignore_index=True)
    out["lat"], out["lon"] = out.lat.round(5), out.lon.round(5)
    out.to_csv(OUT, index=False)

    print(f"\n    {'stratum':<12}{'n':>4}   purpose")
    for s, sub in out.groupby("stratum"):
        print(f"    {s:<12}{len(sub):>4}   {sub.role.iloc[0][:58]}")
    print(f"    {'TOTAL':<12}{len(out):>4}")

    dpct = design.E_pct
    below61 = int((dpct < 61).sum())
    print(f"\n=== does the design straddle what the present network misses? ===")
    print(f"    existing in-domain records span the 61st to 100th emission percentile")
    print(f"    design stratum spans the {dpct.min():.0f}th to {dpct.max():.0f}th, "
          f"{below61} of {len(design)} in the previously unsampled lower 61 per cent")
    if len(vertical):
        zr = vertical.z_above_floor
        print(f"    vertical transect spans {zr.min():.0f} to {zr.max():.0f} m above the local "
              f"valley floor, the axis no network samples")
    print(f"    paired triplets: modelled within-cell contrast "
          f"{pair_contrast[0]:.1f}x to {pair_contrast[1]:.1f}x "
          f"(one Kandy observation at 300 m suggests 27.5x)")

    summary = dict(
        cells_total=int(finite.sum()), cells_feasible=int(feasible.sum()),
        access_max_m=ACCESS_MAX_M, grid_res_m=94,
        n_total=int(len(out)),
        **{f"n_{s.split('_')[1]}": int((out.stratum == s).sum())
           for s in out.stratum.unique()},
        design_covars=DESIGN_COVARS,
        design_pct_lo=float(round(dpct.min(), 1)), design_pct_hi=float(round(dpct.max(), 1)),
        design_below_61=below61, existing_pct_lo=61.0, existing_pct_hi=100.0,
        vertical_zaf_lo=float(round(vertical.z_above_floor.min(), 1)) if len(vertical) else None,
        vertical_zaf_hi=float(round(vertical.z_above_floor.max(), 1)) if len(vertical) else None,
        pair_contrast_lo=round(pair_contrast[0], 2), pair_contrast_hi=round(pair_contrast[1], 2),
        receptors_total=int(len(rc)), receptors_above_p90=int((rc.E_pct >= 90).sum()),
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")
    print("\n[!] Coordinates are a DESIGN, not a siting decision. Each needs a ground visit for "
          "power, security, mounting height and inlet exposure. When a site fails, move to the "
          "nearest cell in the SAME covariate stratum, never to the nearest convenient "
          "building: the latter reintroduces the convenience sampling this design removes.")


if __name__ == "__main__":
    main()
