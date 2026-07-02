"""build_xichang_traffic_emission.py — congestion-weighted traffic EMISSION surface
for Xichang, built with the IDENTICAL method as Kandy (decomp/build_traffic_emission.py).

Same bottom-up structure  emission(x,y) ∝ AADT(x,y)·EF(speed/class)·length,  with AADT
estimated from the open road graph by network centrality (Lowry 2014 centrality-AADT;
betweenness = pass-by, closeness = O-D trip ends) and a COPERT-style speed/congestion
emission factor lifted in jams. Identical CLASS_EF / CLASS_CAP / CONG_GAIN / log-temper
as Kandy → the ONLY change is the bounding box (Xichang station footprint) and the output
grid (the 64×64 spatial_fields grid the twin uses for S_emit), so the emission surface is
directly comparable to Kandy's and to Xichang's observed station pattern.

Web-grounded scope (Liangshan/Sichuan valley city, PM2.5 ~17–22 µg/m³, ~2× WHO): local
urban combustion — vehicle + residential/biomass + light industry — concentrated on the
valley floor, amplified by winter inversions. The traffic surface is the canonical spatial
allocation; magnitude is a literature-bounded prior carried in UQ (as for Kandy).

Output: data/processed/decomp/S_traffic_xichang.npz  (64×64, mean 1, + bt/od layers).
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.transfer_validation.citypack import get
from src.transfer_validation.assembly import _terrain, NGRID

DEC = REPO / "data" / "processed" / "decomp"
DEC.mkdir(parents=True, exist_ok=True)

# IDENTICAL constants to decomp/build_traffic_emission.py (Kandy) ----------------
CLASS_EF = {"motorway": 1.0, "trunk": 1.0, "primary": 0.95, "secondary": 0.70,
            "tertiary": 0.50, "unclassified": 0.35, "residential": 0.30,
            "living_street": 0.25, "service": 0.20}
CLASS_CAP = {"motorway": 1.0, "trunk": 1.0, "primary": 0.8, "secondary": 0.5,
             "tertiary": 0.35, "unclassified": 0.25, "residential": 0.20,
             "living_street": 0.15, "service": 0.15}
CONG_GAIN = 1.6
FINE = 200            # fine raster; block-mean to 64×64


def _class_of(d):
    h = d.get("highway", "residential")
    if isinstance(h, list):
        h = h[0]
    return h if h in CLASS_EF else "residential"


def build(city="xichang"):
    import networkx as nx
    import osmnx as ox
    # city-centred core box (matches {city}_terrain_core.npz + WindNinja library)
    core = REPO / "data" / "processed" / "pinn_inputs" / f"{city}_terrain_core.npz"
    z = np.load(core)
    lat1 = np.asarray(z["lat_grid"])[:, 0].astype(float)
    lon1 = np.asarray(z["lon_grid"])[0, :].astype(float)
    lo, la0, hi, la1 = lon1.min(), lat1.min(), lon1.max(), lat1.max()
    glat = np.linspace(la0, la1, NGRID)
    glon = np.linspace(lo, hi, NGRID)
    print(f"Xichang bbox lon[{lo:.4f},{hi:.4f}] lat[{la0:.4f},{la1:.4f}]")

    ox.settings.overpass_rate_limit = True
    G = ox.graph_from_bbox((lo, la0, hi, la1), network_type="drive")
    G = ox.project_graph(G, to_crs="epsg:4326")
    nodes = {n: d for n, d in G.nodes(data=True)}
    print(f"  graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    DG = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        w = float(d.get("length", 1.0))
        DG.add_edge(u, v, w=w)
    k = min(400, DG.number_of_nodes())
    eb = nx.edge_betweenness_centrality(DG, k=k, weight="w", seed=42, normalized=True)
    bt_max = max(eb.values()) or 1.0
    UG = nx.Graph(DG)
    # Exact closeness runs Dijkstra from every node (O(V·E)) — pathological on
    # metro-scale graphs (e.g. Kathmandu valley). For large graphs estimate
    # closeness from a random sample of k sources (k Dijkstra runs); the
    # relative ranking is preserved and the surface is mean-1 normalised anyway.
    if UG.number_of_nodes() > 5000:
        import random
        rng = random.Random(42)
        srcs = rng.sample(list(UG.nodes()), min(k, UG.number_of_nodes()))
        dsum = {n: 0.0 for n in UG.nodes()}
        dcnt = {n: 0 for n in UG.nodes()}
        for s in srcs:
            for n, dl in nx.single_source_dijkstra_path_length(UG, s, weight="w").items():
                if dl > 0:
                    dsum[n] += dl
                    dcnt[n] += 1
        cc = {n: (dcnt[n] / dsum[n]) if dsum[n] > 0 else 0.0 for n in UG.nodes()}
        print(f"  (sampled closeness: {len(srcs)} sources over {UG.number_of_nodes()} nodes)")
    else:
        cc = nx.closeness_centrality(UG, distance="w")
    cc_max = max(cc.values()) or 1.0
    print(f"  betweenness max={bt_max:.4f}  closeness max={cc_max:.4f}")

    E = np.zeros((FINE, FINE))
    bt_g = np.zeros((FINE, FINE))
    od_g = np.zeros((FINE, FINE))

    def _ij(plat, plon):
        i = np.clip(((plat - la0) / (la1 - la0) * (FINE - 1)).astype(int), 0, FINE - 1)
        j = np.clip(((plon - lo) / (hi - lo) * (FINE - 1)).astype(int), 0, FINE - 1)
        return i, j

    for u, v, d in G.edges(data=True):
        cls = _class_of(d)
        bt = eb.get((u, v), eb.get((v, u), 0.0)) / bt_max
        od = 0.5 * (cc.get(u, 0.0) + cc.get(v, 0.0)) / cc_max
        aadt = 0.75 * bt + 0.25 * od
        cong = bt / (CLASS_CAP[cls] + 1e-6)
        ef = CLASS_EF[cls] * (1.0 + CONG_GAIN * np.clip(cong, 0, 1.5))
        geom = d.get("geometry", None)
        if geom is not None:
            xs, ys = geom.xy
            P = np.column_stack([np.asarray(ys), np.asarray(xs)])
        else:
            a = [nodes[u]["y"], nodes[u]["x"]]
            b = [nodes[v]["y"], nodes[v]["x"]]
            n = max(2, int(np.hypot(b[0] - a[0], b[1] - a[1]) / 0.0004))
            P = np.linspace(a, b, n)
        ii, jj = _ij(P[:, 0], P[:, 1])
        np.add.at(E, (ii, jj), aadt * ef)
        np.add.at(bt_g, (ii, jj), bt)
        np.add.at(od_g, (ii, jj), od)

    # disperse emissions off the road centrelines (physical dispersion footprint,
    # ~150 m) so the surface is a concentration-relevant field, then log-temper the
    # heavy betweenness tail (literature-bounded source) and normalise to mean 1.
    from scipy.ndimage import gaussian_filter
    E = gaussian_filter(E, sigma=3.0)
    bt_g = gaussian_filter(bt_g, sigma=3.0)
    od_g = gaussian_filter(od_g, sigma=3.0)
    Ec = np.log1p(4.0 * E)

    def _block_mean(A):
        bi = np.linspace(0, FINE, NGRID + 1).astype(int)
        out = np.zeros((NGRID, NGRID))
        for a in range(NGRID):
            for b in range(NGRID):
                out[a, b] = A[bi[a]:bi[a + 1], bi[b]:bi[b + 1]].mean()
        return out

    S = _block_mean(Ec)
    S = np.clip(S, 1e-6, None)
    S = S / S.mean()
    bt16, od16 = _block_mean(bt_g), _block_mean(od_g)

    np.savez(DEC / f"S_traffic_{city}.npz", S_traffic=S, lats=glat, lons=glon,
             betweenness=bt16, closeness=od16,
             method="centrality-AADT (betweenness + closeness) × COPERT cong EF, log-tempered")
    print(f"{city} S_traffic: range {S.min():.2f}-{S.max():.2f}  "
          f"core/edge {np.percentile(S,98)/np.percentile(S,15):.2f}×")
    plt.close("all")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--city", default="xichang")
    build(ap.parse_args().city)
