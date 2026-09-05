"""design_sensor_network.py -- where to put sensors in Kandy, and why there.

THE PREMISE, AND IT IS FALSIFIABLE. This project has measured a spatial ceiling six times: a
learned within-city pattern does not beat built-up land cover at 2.4 km by more than 0.130 in
rank correlation. Chapter 8 of the thesis argues the cause is a change of support. But there is a
second, cheaper explanation that the thesis states and cannot rule out: every network it scored
is a CONVENIENCE SAMPLE. Regulatory and low-cost networks are sited for compliance, access, power
and security, never for land-use contrast. Published land-use regression reaches R^2 0.43 to 0.83
precisely because those campaigns site deliberately.

So the design below is an experiment, not just an instrument order. If a deliberately contrasted
network still yields a low rank correlation, the information-limited reading is confirmed far
more strongly than six convenience-sample nulls could confirm it. If it does not, the ceiling was
a sampling artefact and the thesis says so. **Both outcomes are worth the campaign.**

WHAT THE NUMBERS SAY ABOUT THE PRESENT NETWORK. Within the 15x15 km domain the fine emission
surface spans 65x from its 10th to its 90th percentile. The existing fixed records sit between
the 61st and 100th percentile of that range: the entire lower 61 per cent is unsampled, and one
of the two low-cost sensors is outside the domain altogether. A network cannot recover a gradient
it never straddles.

FOUR STRATA, AND THEY ANSWER DIFFERENT QUESTIONS. Keeping them separate is the point: a single
optimisation that mixes model information with exposure protection serves neither well, and a
site used to fit a model cannot also validate it.

  A  ANCHOR      one reference-grade instrument. Everything else calibrates against it.
  B  DESIGN      spans the covariate space by conditioned Latin hypercube sampling, so the
                 network straddles the gradients the model claims to represent.
  C  PAIRED      microsite pairs INSIDE single model cells, at the separations the Kandy
                 transect showed matter. These measure the within-cell distribution, which
                 Chapter 8 argues is the well-posed quantity and the larger one.
  D  RECEPTOR    schools and health facilities. Chosen for who is there, not for information.
                 HELD OUT of any model fitting, so they can serve as an honest test.

Usage: python scripts/design_sensor_network.py [--n-design 12] [--n-pairs 3] [--n-receptor 8]
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
CELL_M = 998.0          # the delivered reporting cell, from the production field
PAIR_SEPARATIONS_M = [100, 300]   # the Kandy transect resolved 110 -> 4 ug/m3 over 300 m
MIN_SEP_M = 400.0       # design sites must not crowd; pairs are the deliberate exception


def load_layers():
    """Every covariate on a common 94 m grid: the finest the emission surface supports."""
    t = np.load(DEC / "S_traffic_kandy.npz")
    E, lat, lon = t["E_fine"], t["fine_lat"], t["fine_lon"]

    e = np.load(PIN / "kandy_elev_grid_100m.npz")
    z, zlat, zlon = e["elev"], e["lat_grid"], e["lon_grid"]
    if zlat.ndim == 2:
        zlat, zlon = zlat[:, 0], zlon[0, :]
    # nearest-neighbour onto the emission grid; both are regular so this is exact enough
    zi = np.abs(zlat[:, None] - lat[None, :]).argmin(0)
    zj = np.abs(zlon[:, None] - lon[None, :]).argmin(0)
    Z = z[np.ix_(zi, zj)]

    p = np.load(DEC / "population_kandy.npz")
    P, plat, plon = p["pop"], p["lats"], p["lons"]
    pi = np.abs(plat[:, None] - lat[None, :]).argmin(0)
    pj = np.abs(plon[:, None] - lon[None, :]).argmin(0)
    POP = P[np.ix_(pi, pj)]

    # confinement: how far below the local surroundings a cell sits. The model's own M term.
    from scipy.ndimage import uniform_filter
    DZ = uniform_filter(Z, size=25, mode="nearest") - Z
    return dict(E=E, Z=Z, POP=POP, DZ=DZ, lat=lat, lon=lon)


def clhs(X: np.ndarray, n: int, seed: int, n_iter: int = 12000):
    """Conditioned Latin hypercube sampling.

    Picks n rows whose MARGINAL distributions reproduce the population's, stratum by stratum.
    That is the property wanted here: the network should straddle every gradient the model
    claims to represent, rather than cluster where access is easy. Standard in environmental
    survey design for exactly this problem.
    """
    rng = np.random.default_rng(seed)
    N, k = X.shape
    edges = [np.quantile(X[:, j], np.linspace(0, 1, n + 1)) for j in range(k)]

    def cost(idx):
        c = 0.0
        for j in range(k):
            h, _ = np.histogram(X[idx, j], bins=edges[j])
            c += np.abs(h - 1).sum()          # one sample per stratum is the target
        return c

    idx = rng.choice(N, n, replace=False)
    best, bc = idx.copy(), cost(idx)
    T = 1.0
    for it in range(n_iter):
        cand = idx.copy()
        cand[rng.integers(n)] = rng.integers(N)
        if len(set(cand)) < n:
            continue
        cc = cost(cand)
        if cc < bc or rng.random() < np.exp(-(cc - bc) / max(T, 1e-9)):
            idx, bc_now = cand, cc
            if cc < bc:
                best, bc = cand.copy(), cc
        T *= 0.9995
        if bc == 0:
            break
    return best


def m_per_deg(lat0: float):
    return 111_000.0, 111_000.0 * np.cos(np.radians(lat0))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-design", type=int, default=12)
    ap.add_argument("--n-pairs", type=int, default=3)
    ap.add_argument("--n-receptor", type=int, default=8)
    a = ap.parse_args()

    L = load_layers()
    lat, lon = L["lat"], L["lon"]
    mlat, mlon = m_per_deg(float(lat.mean()))
    LON, LAT = np.meshgrid(lon, lat)

    ok = np.isfinite(L["E"]) & np.isfinite(L["Z"])
    flatE = L["E"][ok]
    df = pd.DataFrame(dict(
        lat=LAT[ok], lon=LON[ok], E=L["E"][ok], Z=L["Z"][ok],
        POP=L["POP"][ok], DZ=L["DZ"][ok]))
    df["E_pct"] = 100 * df.E.rank(pct=True)

    print("=== Kandy sensor network design ===")
    print(f"    canvas {ok.sum():,} candidate cells at ~94 m over the 15x15 km domain")
    print(f"    emission contrast p90/p10 = "
          f"{np.percentile(flatE, 90) / max(np.percentile(flatE, 10), 1e-9):.0f}x")

    # ── A. anchor ─────────────────────────────────────────────────────────────────────────
    # The reference goes where it does the most work: high population AND high emission, so it
    # anchors the calibration of every low-cost unit in the regime where they are least
    # trustworthy and where the most people are.
    sc = (df.POP.rank(pct=True) + df.E.rank(pct=True)).to_numpy()
    anchor = df.iloc[[int(np.argmax(sc))]].assign(stratum="A_anchor", role="reference monitor")

    # ── B. design sites, cLHS over the covariate space ────────────────────────────────────
    Xcols = ["E", "Z", "DZ", "POP"]
    X = df[Xcols].to_numpy(float)
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-12)
    sel = clhs(Xs, a.n_design, SEED)
    design = df.iloc[sel].copy()

    # thin anything that crowds another site: two sensors 200 m apart in the same regime buy
    # one sensor's worth of information, and the paired stratum exists to do that deliberately
    keep = []
    for i in design.index:
        r = design.loc[i]
        if all(np.hypot((r.lat - design.loc[j].lat) * mlat,
                        (r.lon - design.loc[j].lon) * mlon) > MIN_SEP_M for j in keep):
            keep.append(i)
    design = design.loc[keep].assign(stratum="B_design", role="low-cost, model information")

    # ── C. paired microsites ──────────────────────────────────────────────────────────────
    # Placed where the fine surface has the STEEPEST local gradient, because that is where the
    # within-cell distribution is widest and where a cell mean is least representative of a
    # person standing in it.
    gy, gx = np.gradient(np.where(np.isfinite(L["E"]), L["E"], np.nan))
    grad = np.hypot(gy, gx)
    g = pd.DataFrame(dict(lat=LAT[ok], lon=LON[ok], grad=grad[ok], E=L["E"][ok],
                          gy=gy[ok], gx=gx[ok])).dropna()
    g = g.sort_values("grad", ascending=False)

    def E_at(la, lo):
        i = int(np.abs(lat - la).argmin())
        j = int(np.abs(lon - lo).argmin())
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
        # The OFFSET MEMBER IS A REAL, DIFFERENT COORDINATE. A pair sharing one coordinate is
        # one point recorded twice, which is exactly the artefact the Elangasinghe re-analysis
        # had to withdraw. Offset runs ALONG the steepest gradient so the pair straddles the
        # contrast rather than running along a contour, where it would measure nothing.
        norm = np.hypot(r.gy, r.gx) or 1.0
        uy, ux = r.gy / norm, r.gx / norm
        pairs.append(dict(pair_id=pid, member="a", lat=r.lat, lon=r.lon, E=r.E,
                          pair_sep_m=0, stratum="C_paired",
                          role=f"{pid} anchor member, steepest-gradient cell"))
        for sep in PAIR_SEPARATIONS_M:
            dlat = (uy * sep) / mlat
            dlon = (ux * sep) / mlon
            la, lo = r.lat + dlat, r.lon + dlon
            same_cell = np.hypot((la - r.lat) * mlat, (lo - r.lon) * mlon) < CELL_M
            pairs.append(dict(
                pair_id=pid, member=f"b{sep}", lat=la, lon=lo, E=E_at(la, lo),
                pair_sep_m=sep, stratum="C_paired",
                role=(f"{pid} offset {sep} m along the gradient, "
                      f"{'SAME model cell' if same_cell else 'ADJACENT cell'}")))
    paired = pd.DataFrame(pairs)
    if len(paired):
        contrast = (paired.groupby("pair_id").E.max() /
                    paired.groupby("pair_id").E.min().clip(lower=1e-9))
        print(f"\n    paired microsites: {paired.pair_id.nunique()} pairs, "
              f"modelled within-pair emission contrast "
              f"{contrast.min():.1f}x to {contrast.max():.1f}x")

    # ── D. receptors ──────────────────────────────────────────────────────────────────────
    rc = pd.read_csv(DEC / "kandy_receptors_ranked.csv")
    rc = rc[rc.E_pct.notna()].sort_values("E_pct", ascending=False)
    # Two institutions 30 m apart are one site. Thin before selecting, or the campaign spends
    # two sensors to measure the same air and reports it as two receptors covered.
    kept = []
    for r in rc.itertuples():
        if all(np.hypot((r.lat - k[0]) * mlat, (r.lon - k[1]) * mlon) > 150.0 for k in kept):
            kept.append((r.lat, r.lon, r.Index))
    rc = rc.loc[[k[2] for k in kept]]
    # spread across receptor type rather than taking the top n, which would be all schools
    take = []
    for grp, sub in rc.groupby("group"):
        take.append(sub.head(max(1, a.n_receptor // max(rc.group.nunique(), 1))))
    receptor = pd.concat(take).sort_values("E_pct", ascending=False).head(a.n_receptor)
    receptor = receptor.assign(stratum="D_receptor",
                               role="exposure, HELD OUT of model fitting")

    cols = ["stratum", "role", "lat", "lon"]
    out = pd.concat([
        anchor.assign(name="")[cols + ["E_pct"]],
        design.assign(name="")[cols + ["E_pct"]],
        paired.assign(name="", E_pct=np.nan)[cols + ["E_pct"]],
        receptor[cols + ["E_pct", "name"]].assign(name=receptor.name.fillna("")),
    ], ignore_index=True)
    out["lat"] = out.lat.round(5)
    out["lon"] = out.lon.round(5)
    out.to_csv(OUT, index=False)

    print(f"\n    {'stratum':<12}{'n':>4}   purpose")
    for s, sub in out.groupby("stratum"):
        print(f"    {s:<12}{len(sub):>4}   {sub.role.iloc[0]}")
    print(f"    {'TOTAL':<12}{len(out):>4}")

    dpct = design.E_pct
    print(f"\n=== does the design straddle what the present network misses? ===")
    print(f"    existing in-domain records span the 61st to 100th percentile of emission")
    print(f"    design stratum spans the {dpct.min():.0f}th to {dpct.max():.0f}th, "
          f"median {dpct.median():.0f}th")
    below61 = int((dpct < 61).sum())
    print(f"    design sites in the previously UNSAMPLED lower 61 per cent: "
          f"{below61} of {len(design)}")

    summary = dict(
        candidate_cells=int(ok.sum()), grid_res_m=94,
        n_total=int(len(out)),
        n_anchor=int((out.stratum == "A_anchor").sum()),
        n_design=int((out.stratum == "B_design").sum()),
        n_paired=int((out.stratum == "C_paired").sum()),
        n_receptor=int((out.stratum == "D_receptor").sum()),
        design_pct_lo=float(round(dpct.min(), 1)), design_pct_hi=float(round(dpct.max(), 1)),
        design_below_61=below61,
        existing_pct_lo=61.0, existing_pct_hi=100.0,
        emission_contrast_p90_p10=float(round(
            np.percentile(flatE, 90) / max(np.percentile(flatE, 10), 1e-9), 1)),
        pair_separations_m=PAIR_SEPARATIONS_M, min_separation_m=MIN_SEP_M,
        receptors_total=int(len(rc)),
        receptors_above_p90=int((rc.E_pct >= 90).sum()),
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")
    print("\n[!] Coordinates are a DESIGN, not a siting decision. Every one needs a ground "
          "visit for power, security, mounting height and inlet exposure, and the plan says "
          "what to do when a site fails that check.")


if __name__ == "__main__":
    main()
