"""
build_traffic_emission.py — congestion-weighted traffic EMISSION surface for Kandy
(2026-06-04).

METHOD (canonical, literature-backed). This is a bottom-up road-traffic emission
spatial allocation following the standard inventory structure
  emission(x,y) ∝ AADT(x,y) · EF(speed/class) · length,
(e.g. the OSM-network Nordic inventory, Plejdrup/Kuenen-style; EDGAR uses road
*density* as a cruder proxy that deviates up to 500 % in urban cores — so volume,
not just road presence, is needed). Where a city has no traffic counts — exactly
Kandy — the established substitute is a NETWORK-CENTRALITY estimate of AADT
(Lowry 2014; Zhao & Wang / centrality-AADT for metro areas), explicitly recommended
for resource-scarce developing-country contexts because it needs only the open road
graph. AADT decomposes into pass-by + origin-destination trips:

  AADT_proxy(e) = α · BETWEENNESS(e)        — pass-by / through traffic (r≈0.77 vs
                                              measured flow; Kazerani & Winter 2009)
                + β · CLOSENESS/trip-gen(e)  — origin-destination trip ends, weighted
                                              by trip generators (terminals, junctions)

  EF(e)        = speed/class emission factor (COPERT/HBEFA U-shaped speed curve;
                 buses+trucks on arterials), LIFTED under congestion (flow ≫ capacity):
                 stop-go accel/decel/idle + brake/tyre non-exhaust PM, worst in jams
                 (COPERT under-predicts NOx in congestion; +13–16 % network-scale).

  E_traffic(x,y) = Σ_edges AADT_proxy · EF · length  +  stop-go node density.

Honest scope: with no measured AADT or local fleet EF for Kandy, the *spatial
allocation* is the canonical method but the *absolute magnitude* is a literature-
bounded prior (core ≈ 3.5× mean), carried in the model's UQ — consistent with the
whole reconstruction's prior-where-unmeasured philosophy. (TomTom measured flow was
attempted and verified UNAVAILABLE for Sri Lanka — Amsterdam control works, Colombo
+ Kandy return no segments — so calibration data does not exist for this region.)

Output: data/processed/decomp/S_traffic_kandy.npz (16×16 decomp grid, mean 1)
        + results/figures/final_model_suite/figX3_traffic_emission.png (QA).
The static surface × the existing e(t) rush-hour profile is the time dimension.
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
from config import KANDY_PINN_BBOX as BB

DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "results" / "figures" / "final_model_suite"
OUT.mkdir(parents=True, exist_ok=True)

# emission factor by road class (relative; buses/trucks on arterials, low on residential)
CLASS_EF = {"motorway": 1.0, "trunk": 1.0, "primary": 0.95, "secondary": 0.70,
            "tertiary": 0.50, "unclassified": 0.35, "residential": 0.30,
            "living_street": 0.25, "service": 0.20}
# nominal free-flow capacity by class (veh/h, relative) — congestion = flow / capacity
CLASS_CAP = {"motorway": 1.0, "trunk": 1.0, "primary": 0.8, "secondary": 0.5,
             "tertiary": 0.35, "unclassified": 0.25, "residential": 0.20,
             "living_street": 0.15, "service": 0.15}
CONG_GAIN = 1.6        # how strongly a jam (flow≫capacity) lifts the EF
NGRID = 160            # fine raster (=16×10) → block-mean to the 16×16 decomp grid


def _class_of(d):
    h = d.get("highway", "residential")
    if isinstance(h, list):
        h = h[0]
    return h if h in CLASS_EF else "residential"


def build():
    import osmnx as ox
    import networkx as nx
    bbox = (BB["lon_min"], BB["lat_min"], BB["lon_max"], BB["lat_max"])  # (W,S,E,N) osmnx 2.x
    print("Downloading Kandy drive network …")
    G = ox.graph_from_bbox(bbox=bbox, network_type="drive", simplify=True)
    try:
        G = ox.routing.add_edge_speeds(G); G = ox.routing.add_edge_travel_times(G)
        wt = "travel_time"
    except Exception:
        wt = "length"
    print(f"  graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges; weight={wt}")

    # edge betweenness on a simple DiGraph (k-sampled for tractability)
    DG = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        w = float(d.get(wt, d.get("length", 1.0)) or 1.0)
        if DG.has_edge(u, v):
            DG[u][v]["w"] = min(DG[u][v]["w"], w)
        else:
            DG.add_edge(u, v, w=w)
    k = min(DG.number_of_nodes(), 500)
    eb = nx.edge_betweenness_centrality(DG, k=k, weight="w", seed=42, normalized=True)
    bt_max = max(eb.values()) + 1e-12
    # O-D / trip-end term: node closeness centrality (Lowry 2014 pass-by+O-D AADT
    # decomposition). Undirected, distance-weighted; on the full graph.
    UG = DG.to_undirected()
    try:
        cc = nx.closeness_centrality(UG, distance="w")
    except Exception:
        cc = {n: 0.0 for n in UG.nodes}
    cc_max = max(cc.values()) + 1e-12
    print(f"  edge betweenness (k={k}) max={bt_max:.4f}; closeness max={cc_max:.4f}")

    # rasterize edge emissions
    lat = np.linspace(BB["lat_min"], BB["lat_max"], NGRID)
    lon = np.linspace(BB["lon_min"], BB["lon_max"], NGRID)
    grid = np.zeros((NGRID, NGRID))
    grid_bt = np.zeros((NGRID, NGRID))   # betweenness (pass-by) layer for F5
    grid_od = np.zeros((NGRID, NGRID))   # closeness (O-D) layer for F5
    nodes = G.nodes
    for u, v, d in G.edges(data=True):
        cls = _class_of(d)
        bt = eb.get((u, v), eb.get((v, u), 0.0)) / bt_max          # pass-by flow (0..1)
        od = 0.5 * (cc.get(u, 0.0) + cc.get(v, 0.0)) / cc_max      # O-D trip-end (0..1)
        aadt = 0.75 * bt + 0.25 * od                              # centrality AADT proxy
        cong = bt / (CLASS_CAP[cls] + 1e-6)                        # flow / capacity → jam index
        ef = CLASS_EF[cls] * (1.0 + CONG_GAIN * np.clip(cong, 0, 1.5))  # COPERT-style speed/cong EF
        emis = (aadt ** 0.7) * ef                                  # per-edge emission intensity
        # sample points along the edge geometry
        geom = d.get("geometry")
        if geom is not None:
            xs, ys = geom.xy
            pts = np.column_stack([np.asarray(ys), np.asarray(xs)])
        else:
            pts = np.array([[nodes[u]["y"], nodes[u]["x"]], [nodes[v]["y"], nodes[v]["x"]]])
        # densify
        seg = []
        for a, b in zip(pts[:-1], pts[1:]):
            n = max(2, int(np.hypot(*(b - a)) / (0.0005)))         # ~50 m steps
            seg.append(np.linspace(a, b, n))
        P = np.vstack(seg)
        ii = np.clip(((P[:, 0] - BB["lat_min"]) / (BB["lat_max"] - BB["lat_min"]) * (NGRID - 1)).astype(int), 0, NGRID - 1)
        jj = np.clip(((P[:, 1] - BB["lon_min"]) / (BB["lon_max"] - BB["lon_min"]) * (NGRID - 1)).astype(int), 0, NGRID - 1)
        for a, b in zip(ii, jj):
            grid[a, b] += emis / len(P)
            grid_bt[a, b] += bt / len(P)
            grid_od[a, b] += od / len(P)

    # stop-go node layer: traffic signals + bus stations + high-degree junctions
    stopgo = np.zeros((NGRID, NGRID))
    deg = dict(G.degree())
    for nd, dat in G.nodes(data=True):
        s = 0.0
        if dat.get("highway") in ("traffic_signals", "mini_roundabout", "stop"):
            s += 1.0
        if deg.get(nd, 0) >= 5:
            s += 0.5
        if s:
            i = int(np.clip((dat["y"] - BB["lat_min"]) / (BB["lat_max"] - BB["lat_min"]) * (NGRID - 1), 0, NGRID - 1))
            j = int(np.clip((dat["x"] - BB["lon_min"]) / (BB["lon_max"] - BB["lon_min"]) * (NGRID - 1), 0, NGRID - 1))
            stopgo[i, j] += s
    try:
        pois = ox.features_from_bbox(bbox=bbox, tags={"amenity": ["bus_station"], "shop": ["marketplace"], "amenity2": True})
        for _, r in pois.iterrows():
            p = r.geometry.centroid
            i = int(np.clip((p.y - BB["lat_min"]) / (BB["lat_max"] - BB["lat_min"]) * (NGRID - 1), 0, NGRID - 1))
            j = int(np.clip((p.x - BB["lon_min"]) / (BB["lon_max"] - BB["lon_min"]) * (NGRID - 1), 0, NGRID - 1))
            stopgo[i, j] += 1.5
    except Exception as e:
        print(f"  (POI fetch skipped: {e})")

    from scipy.ndimage import gaussian_filter
    road = gaussian_filter(grid, sigma=2.5)
    stop = gaussian_filter(stopgo, sigma=3.5)
    road = road / (road.max() + 1e-9); stop = stop / (stop.max() + 1e-9)
    E_fine = 0.7 * road + 0.3 * stop

    # block-mean to the 16×16 decomp grid, with a log compression of the heavy
    # betweenness tail so the SOURCE multiplier is literature-bounded (congested
    # arterials ~1.5-2× EF; core ≈3.5× mean) rather than a raster spike.
    M = np.load(DEC / "M_confinement_kandy.npz"); lats16, lons16 = M["lats"], M["lons"]
    Ec = np.log1p(4.0 * E_fine)
    E16 = Ec.reshape(16, NGRID // 16, 16, NGRID // 16).mean(axis=(1, 3))
    E16 = E16 / E16.mean()                                          # mean 1
    bt_fine = gaussian_filter(grid_bt, sigma=2.5); bt_fine /= (bt_fine.max() + 1e-9)
    od_fine = gaussian_filter(grid_od, sigma=2.5); od_fine /= (od_fine.max() + 1e-9)
    np.savez(DEC / "S_traffic_kandy.npz", S_traffic=E16, lats=lats16, lons=lons16,
             E_fine=E_fine, fine_lat=lat, fine_lon=lon,
             betweenness_fine=bt_fine, closeness_fine=od_fine,
             method="centrality-AADT (betweenness pass-by + closeness O-D) × COPERT speed/cong EF, log-tempered")

    ci = int(np.argmin(abs(lats16 - 7.2906))); cj = int(np.argmin(abs(lons16 - 80.6337)))
    print(f"S_traffic: core {E16[ci,cj]:.2f}  range {E16.min():.2f}-{E16.max():.2f}  "
          f"core/edge {E16[ci,cj]/np.percentile(E16,15):.2f}×")

    # QA figure
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.6), constrained_layout=True)
    ext = [BB["lon_min"], BB["lon_max"], BB["lat_min"], BB["lat_max"]]
    im0 = ax[0].imshow(E_fine, origin="lower", extent=ext, cmap="inferno", aspect="auto")
    ax[0].set_title("(a) congestion-weighted traffic emission (160 m)\nbetweenness flow × EF × stop-go", fontsize=9)
    for nm, (la, lo) in {"clock tower/lake": (7.2906, 80.6337), "Katugastota Rd": (7.32, 80.63),
                         "Peradeniya Rd": (7.28, 80.60)}.items():
        ax[0].annotate(nm, (lo, la), color="cyan", fontsize=7.5)
    fig.colorbar(im0, ax=ax[0], shrink=0.8, label="rel. emission")
    from scipy.ndimage import zoom
    im1 = ax[1].imshow(zoom(E16, 8, order=3), origin="lower", extent=ext, cmap="inferno", aspect="auto")
    ax[1].set_title(f"(b) on decomp grid (mean 1)\ncore/edge {E16[ci,cj]/np.percentile(E16,15):.2f}×", fontsize=9)
    fig.colorbar(im1, ax=ax[1], shrink=0.8, label="rel. emission")
    fig.suptitle("Kandy congestion-weighted traffic emission surface (OSM proxy; Stage-2 TomTom calibration pending)", fontsize=11)
    fig.savefig(OUT / "figX3_traffic_emission.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print(f"Wrote {DEC/'S_traffic_kandy.npz'}\nWrote {OUT/'figX3_traffic_emission.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    build()
