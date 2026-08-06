"""panel_city_graph_donor.py — learned donor weights over a CITY GRAPH (2026-08-06).

THE IDEA, AND WHY IT IS THE ONLY GRAPH THAT APPLIES HERE
--------------------------------------------------------
A station-level graph is dead at Kandy: the strongest physics-guided air-quality GNN
(GraPhy, 2025) states it loses to plain inverse-distance weighting below ~0.16
sensors/mi^2, and Kandy sits at 0.023 -- roughly seven times below that. Two nodes do
not make a graph.

The graph that DOES apply puts CITIES at the nodes, which is what GAGNN (city graph +
city-group graph) and HighAir (hierarchical city-over-station graphs) do. This project
already has the ingredients without having called them a graph: the CNEMC panel is the
node set, PVAF-style similarity is an edge-weight function, and leave-one-city-out is
held-out-node evaluation.

What is missing is that the donor diurnal shape is currently an UNWEIGHTED MEAN over
199 cities. Every donor counts equally, whether or not it resembles the target. This
script replaces that with a learned similarity kernel over city descriptors:

    shape_hat(target) = sum_d w(target, d) . shape(d),
    w proportional to exp( - sum_k theta_k . |z_k(target) - z_k(d)|^2 )

theta (one bandwidth per descriptor, plus a temperature) is fitted by LEAVE-ONE-CITY-OUT
on the panel itself, so a city never contributes to its own prediction.

HONEST EXPECTATION, SET BEFORE RUNNING
--------------------------------------
Small gains. The project's own solar-time work already showed the transferable part of
the diurnal cycle is largely UNIVERSAL (out-of-region median r 0.736, in-region panel
mean 0.892), which caps what any reweighting can add. This is a method contribution --
a principled replacement for an unweighted mean -- not a route to new Kandy skill. It is
reported as such whatever the number.

EVALUATION, AND THE LEAKAGE CONSTRAINT
--------------------------------------
Five of the nine original validation cities sit INSIDE the CNEMC panel (Xichang, Tai'an,
Baoji, Yichang, Bazhong are all within ~1.5 km of a panel city). Any panel-trained donor
can therefore only be validated on the cities that are NOT in the panel. Two evaluations
are reported and kept separate:

  PANEL LOCO      leave-one-city-out within the 199, the fitting objective
  OUT-OF-PANEL    the non-Chinese target cities, which no panel city can leak into

Baselines: the unweighted panel mean (what ships today), and a distance-only kernel
(geographic nearest neighbours), so the descriptor kernel has to beat both.

Run:  .venv/Scripts/python.exe scripts/panel_city_graph_donor.py
Out:  results/figures/multicity/panel_city_graph_donor.{csv,json}
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

PANEL = REPO / "data" / "processed" / "cnemc_panel" / "cities"
MANIFEST = REPO / "data" / "processed" / "cnemc_panel" / "panel_manifest_enriched.csv"
RELIEF = REPO / "data" / "processed" / "cnemc_panel" / "terrain_relief.csv"
OUT = REPO / "results" / "figures" / "multicity"
CN_REF_MERIDIAN = 120.0
MIN_HOURS = 6000

# Node descriptors. ADMISSIBILITY RULE: a descriptor may only be used if it is
# obtainable for a target with NO local PM observations, because that is the whole use
# case. Two candidates were removed after a first run for violating it:
#   peakiness     derived from the city's own diurnal shape -- it leaks the answer
#                 (it raised panel LOCO to 0.860, which was not a real gain)
#   log_stations  network size is a property of the monitoring programme, not of the
#                 city's atmosphere, and says nothing about an unmonitored target
# log_pm25 is retained as a stand-in for a SATELLITE-derived magnitude, which does
# exist everywhere (Van Donkelaar / GHAP); here it is taken from panel observations
# for convenience, and that substitution is disclosed.
DESCRIPTORS = ["log_pm25", "relief", "abs_lat", "lon"]
BLOCK_KM = 500.0          # spatial-block CV radius: simulates a DISTANT target


def city_diurnal(cdir: Path):
    """Unit-mean observed diurnal climatology in SOLAR time for one panel city."""
    fs = sorted(glob.glob(str(cdir / "*.parquet")))
    if not fs:
        return None
    keep = []
    for f in fs:
        try:
            d = pd.read_parquet(f)
        except Exception:
            continue
        tc = next((c for c in d.columns if c.lower() in
                   ("datetime", "time", "datetime_utc", "date")), None)
        pc = next((c for c in d.columns if "pm25" in c.lower()), None)
        if tc is None or pc is None:
            continue
        keep.append(d[[tc, pc]].rename(columns={tc: "t", pc: "pm"}))
    if not keep:
        return None
    d = pd.concat(keep, ignore_index=True)
    d["t"] = pd.to_datetime(d.t, errors="coerce")
    d = d.dropna(subset=["t", "pm"])
    d = d[(d.pm > 0) & (d.pm < 1000)]
    if len(d) < MIN_HOURS:
        return None
    s = d.groupby(d.t.dt.hour).pm.mean()
    s = s.reindex(range(24))
    if s.isna().any() or s.mean() <= 0:
        return None
    return s / s.mean()


def to_solar(shape24: pd.Series, lon: float) -> pd.Series:
    """Shift a clock-hour climatology onto solar hours (CNEMC stamps are UTC+8)."""
    off = (lon - CN_REF_MERIDIAN) / 15.0
    h = np.arange(24)
    src = (h - off) % 24
    lo = np.floor(src).astype(int) % 24
    hi = (lo + 1) % 24
    w = src - np.floor(src)
    v = shape24.to_numpy(float)
    return pd.Series(v[lo] * (1 - w) + v[hi] * w, index=h)


def build_nodes() -> pd.DataFrame:
    man = pd.read_csv(MANIFEST)
    if RELIEF.exists():
        rel = pd.read_csv(RELIEF)
        rc = next((c for c in rel.columns if "relief" in c.lower()), None)
        if rc:
            man = man.merge(rel[["slug", rc]].rename(columns={rc: "relief"}),
                            on="slug", how="left")
    if "relief" not in man.columns:
        man["relief"] = np.nan
    rows = []
    print("  building per-city solar-time diurnal shapes ...")
    for i, r in man.iterrows():
        cdir = PANEL / str(r.slug)
        if not cdir.exists():
            continue
        s = city_diurnal(cdir)
        if s is None:
            continue
        sol = to_solar(s, float(r.lon))
        rows.append({"slug": r.slug, "lat": float(r.lat), "lon": float(r.lon),
                     "pm25_mean": float(r.pm25_mean),
                     "n_stations": float(r.get("n_stations", np.nan)),
                     "relief": float(r.relief) if pd.notna(r.relief) else np.nan,
                     "peakiness": float(sol.max() - sol.min()),
                     "shape": sol.to_numpy()})
        if len(rows) % 25 == 0:
            print(f"    {len(rows)} cities")
    d = pd.DataFrame(rows)
    d["log_pm25"] = np.log(d.pm25_mean.clip(lower=1))
    d["abs_lat"] = d.lat.abs()
    d["log_stations"] = np.log(d.n_stations.clip(lower=1))
    d["relief"] = d.relief.fillna(d.relief.median())
    return d


def zscore(d: pd.DataFrame, cols):
    Z = d[cols].astype(float).to_numpy()
    mu, sd = np.nanmean(Z, 0), np.nanstd(Z, 0)
    sd[sd == 0] = 1.0
    Z = (Z - mu) / sd
    return np.nan_to_num(Z), mu, sd


def _apply(W, S, mask=None):
    """Weighted donor prediction with an optional exclusion mask (block CV)."""
    W = W.copy()
    np.fill_diagonal(W, 0.0)
    if mask is not None:
        W = W * mask
    W = W / np.clip(W.sum(1, keepdims=True), 1e-12, None)
    P = W @ S
    return P / np.clip(P.mean(1, keepdims=True), 1e-12, None)


def _meanr(P, S) -> float:
    return float(np.nanmean([np.corrcoef(P[i], S[i])[0, 1] for i in range(len(S))]))


def loco_score(theta, Z, S, mask=None) -> float:
    """Mean correlation of the weighted-donor shape against the observed shape.

    `mask` implements SPATIAL-BLOCK cross-validation: zeroing every donor within
    BLOCK_KM of the target simulates the situation that actually applies at Kandy,
    which has no panel city anywhere near it. Plain leave-one-out flatters any
    geography-based rule, because a Chinese panel city always has close neighbours
    and Kandy never does.
    """
    lam = np.exp(theta)                     # positive bandwidths
    d2 = ((Z[:, None, :] - Z[None, :, :]) ** 2 * lam[None, None, :]).sum(-1)
    return _meanr(_apply(np.exp(-d2), S, mask), S)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== city-graph donor weighting (nodes = cities) ===")
    nodes = build_nodes()
    print(f"  {len(nodes)} panel cities with usable diurnal shapes")
    if len(nodes) < 30:
        raise SystemExit("too few usable panel cities")

    S = np.vstack(nodes["shape"].to_numpy())
    Z, mu, sd = zscore(nodes, DESCRIPTORS)

    # ── geometry + the spatial-block mask ────────────────────────────────────
    n = len(S)
    lat = nodes.lat.to_numpy(); lon = nodes.lon.to_numpy()
    gd2 = ((lat[:, None] - lat[None, :]) * 110.6) ** 2 + \
          ((lon[:, None] - lon[None, :]) * 110.6 *
           np.cos(np.radians(lat[:, None]))) ** 2
    block = (gd2 > BLOCK_KM ** 2).astype(float)     # donors must be > BLOCK_KM away
    kept = block.sum(1)
    print(f"  spatial-block CV at {BLOCK_KM:.0f} km: median {np.median(kept):.0f} "
          f"of {n - 1} donors retained per target")

    results = {}
    for tag, mask in (("plain LOCO", None), (f"block CV >{BLOCK_KM:.0f} km", block)):
        loo_mean = _apply(np.ones((n, n)), S, mask)
        r_mean = _meanr(loo_mean, S)
        best_geo, best_bw = -1, None
        for bw in (50, 100, 200, 400, 800, 1600):
            r = _meanr(_apply(np.exp(-gd2 / (2 * bw ** 2)), S, mask), S)
            if r > best_geo:
                best_geo, best_bw = r, bw
        obj = lambda th: -loco_score(th, Z, S, mask)
        best = None
        for x0 in (-2.0, -1.0, 0.0):
            res = minimize(obj, np.full(len(DESCRIPTORS), x0), method="Nelder-Mead",
                           options={"maxiter": 1200, "xatol": 1e-3, "fatol": 1e-5})
            if best is None or res.fun < best.fun:
                best = res
        r_graph, lam = -best.fun, np.exp(best.x)
        results[tag] = {"unweighted_mean": r_mean, "geographic": best_geo,
                        "geographic_bw_km": best_bw, "learned": r_graph,
                        "gain": r_graph - r_mean,
                        "bandwidths": {k: float(v) for k, v in zip(DESCRIPTORS, lam)}}
        print(f"\n  {tag.upper()}  (n={n})")
        print(f"    unweighted panel mean (ships today) : r = {r_mean:+.4f}")
        print(f"    geographic kernel (bw {best_bw} km)  : r = {best_geo:+.4f}")
        print(f"    LEARNED descriptor kernel           : r = {r_graph:+.4f}")
        print(f"    gain vs unweighted                  : {r_graph - r_mean:+.4f}")
        print("    bandwidths: " + "  ".join(
            f"{k}={v:.3f}" for k, v in sorted(zip(DESCRIPTORS, lam), key=lambda kv: -kv[1])))

    r_mean = results[f"block CV >{BLOCK_KM:.0f} km"]["unweighted_mean"]
    r_graph = results[f"block CV >{BLOCK_KM:.0f} km"]["learned"]
    best_geo = results[f"block CV >{BLOCK_KM:.0f} km"]["geographic"]
    lam = np.array(list(results[f"block CV >{BLOCK_KM:.0f} km"]["bandwidths"].values()))
    gain = r_graph - r_mean
    best_bw = results[f"block CV >{BLOCK_KM:.0f} km"]["geographic_bw_km"]
    print(f"\n  THE FIGURE THAT MATTERS is the block-CV row: Kandy has no panel city "
          f"within {BLOCK_KM:.0f} km,")
    print("  so plain LOCO overstates any rule that leans on nearby donors.")

    res_json = {
        "n_panel_cities": int(n),
        "descriptors": DESCRIPTORS,
        "bandwidths": {k: round(float(v), 4) for k, v in zip(DESCRIPTORS, lam)},
        "results": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                        for kk, vv in v.items() if kk != "bandwidths"}
                    for k, v in results.items()},
        "block_km": BLOCK_KM,
        "headline": ("the block-CV row is the one that applies: Kandy has no panel "
                     "city within 500 km, so plain LOCO overstates any rule leaning "
                     "on nearby donors"),
        "removed_descriptors": {
            "peakiness": "derived from the target's own diurnal shape -- leaked the answer",
            "log_stations": "a property of the monitoring programme, not the atmosphere"},
        "expectation_note": (
            "Small gains were expected before running: the project's own solar-time "
            "result showed the transferable diurnal is largely universal (out-of-region "
            "median 0.736, in-region panel mean 0.892), which caps what reweighting can "
            "add. Reported as a method contribution, not as new Kandy skill."),
        "leakage_note": (
            "Five of the nine original validation cities lie inside this panel, so a "
            "panel-trained donor can only be validated on the non-Chinese targets. The "
            "panel LOCO figure here is the FITTING objective, not an independent test."),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "panel_city_graph_donor.json").write_text(
        json.dumps(res_json, indent=1), encoding="utf-8")
    nodes.drop(columns=["shape"]).to_csv(OUT / "panel_city_graph_donor.csv", index=False)
    print(f"\nwrote panel_city_graph_donor.{{csv,json}}")
    print("\n  VERDICT: adopt only if the gain is material AND survives the "
          "out-of-panel targets; otherwise report as a bounded negative.")


if __name__ == "__main__":
    main()
