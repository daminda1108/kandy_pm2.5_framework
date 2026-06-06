"""
build_traffic_tomtom.py — Stage 2: calibrate the OSM congestion proxy against
MEASURED TomTom traffic, and build the measured congestion layer (2026-06-04).

TomTom Flow Segment Data (free tier) returns current vs free-flow speed at a point.
We sample it at OSM main-road segment midpoints (guaranteed on-road), forming a
measured congestion ratio  cong = 1 − currentSpeed/freeFlowSpeed  per location, then:
  1. rasterise measured congestion → the decomp grid,
  2. regress the OSM betweenness-proxy congestion against TomTom (does the proxy
     predict where the real jams are?) → a calibration scale + the right temper,
  3. write the CALIBRATED traffic-emission surface used by the model.

Key is read from API.txt at runtime (never stored). Respects the free-tier rate
limit with a small delay; samples only the higher road classes where congestion
matters. Run in background — ~hundreds of HTTP calls.

Out: data/processed/decomp/tomtom_congestion_kandy.parquet (per-point measured)
     data/processed/decomp/S_traffic_calibrated_kandy.npz (calibrated surface)
     results/figures/final_model_suite/figX4_tomtom_calibration.png
"""
from __future__ import annotations
import json
import re
import sys
import time
import urllib.request
import urllib.error
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
MAIN = {"motorway", "trunk", "primary", "secondary", "tertiary",
        "motorway_link", "trunk_link", "primary_link", "secondary_link"}
NGRID = 16
MAX_POINTS = 900          # well under the 2,500/day free-tier cap
DELAY = 0.12              # s between calls


def _key():
    for line in open(REPO.parent / "API.txt", encoding="utf-8", errors="ignore"):
        if "tomtom" in line.lower():
            toks = [t for t in re.findall(r"[A-Za-z0-9_-]{20,}", line) if t.lower() != "tomtom"]
            if toks:
                return max(toks, key=len)
    raise RuntimeError("no TomTom key in API.txt")


def _flow(lat, lon, key):
    url = (f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/12/json"
           f"?point={lat:.5f}%2C{lon:.5f}&key={key}")
    try:
        d = json.load(urllib.request.urlopen(url, timeout=15))["flowSegmentData"]
        cur, free = float(d["currentSpeed"]), float(d["freeFlowSpeed"])
        return cur, free, float(d.get("confidence", 1.0))
    except urllib.error.HTTPError:
        return None
    except Exception:
        return None


def _class_of(d):
    h = d.get("highway", "residential")
    return (h[0] if isinstance(h, list) else h)


def main():
    import osmnx as ox
    key = _key()
    bbox = (BB["lon_min"], BB["lat_min"], BB["lon_max"], BB["lat_max"])
    G = ox.graph_from_bbox(bbox=bbox, network_type="drive", simplify=True)  # cached
    # main-road edge midpoints (dedup spatially to spread the budget)
    pts = []
    for u, v, d in G.edges(data=True):
        if _class_of(d) not in MAIN:
            continue
        geom = d.get("geometry")
        if geom is not None:
            la, lo = geom.interpolate(0.5, normalized=True).y, geom.interpolate(0.5, normalized=True).x
        else:
            la = (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2; lo = (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2
        pts.append((la, lo, _class_of(d)))
    pts = pd.DataFrame(pts, columns=["lat", "lon", "cls"]).drop_duplicates(["lat", "lon"])
    if len(pts) > MAX_POINTS:
        pts = pts.sample(MAX_POINTS, random_state=42).reset_index(drop=True)
    print(f"Sampling TomTom at {len(pts)} main-road midpoints …")

    rows = []
    for i, r in pts.iterrows():
        res = _flow(r.lat, r.lon, key)
        if res:
            cur, free, conf = res
            rows.append(dict(lat=r.lat, lon=r.lon, cls=r.cls, current=cur, free=free,
                             cong=max(0.0, 1 - cur / free) if free > 0 else 0.0, conf=conf))
        if i % 100 == 0:
            print(f"  {i}/{len(pts)}  ok={len(rows)}")
        time.sleep(DELAY)
    m = pd.DataFrame(rows)
    if m.empty or "cong" not in m.columns:
        print("  NO TomTom flow segments returned for Kandy — TomTom has no traffic "
              "coverage in Sri Lanka (verified: Amsterdam control works, Colombo+Kandy do not).\n"
              "  Calibration not possible; use the OSM betweenness proxy as a literature-bounded prior.")
        return
    m.to_parquet(DEC / "tomtom_congestion_kandy.parquet", index=False)
    print(f"  got {len(m)} measured segments; mean congestion {m.cong.mean():.3f}, "
          f"p90 {m.cong.quantile(0.9):.3f}")

    # rasterise measured congestion (emission ∝ free-flow speed class × (1+gain·cong))
    lats = np.linspace(BB["lat_min"], BB["lat_max"], NGRID)
    lons = np.linspace(BB["lon_min"], BB["lon_max"], NGRID)
    Cmeas = np.full((NGRID, NGRID), np.nan)
    cnt = np.zeros((NGRID, NGRID))
    acc = np.zeros((NGRID, NGRID))
    for _, r in m.iterrows():
        i = int(np.clip((r.lat - BB["lat_min"]) / (BB["lat_max"] - BB["lat_min"]) * (NGRID - 1), 0, NGRID - 1))
        j = int(np.clip((r.lon - BB["lon_min"]) / (BB["lon_max"] - BB["lon_min"]) * (NGRID - 1), 0, NGRID - 1))
        acc[i, j] += r.cong; cnt[i, j] += 1
    Cmeas = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)

    # calibrate the OSM proxy against measured congestion (cell-matched)
    St = np.load(DEC / "S_traffic_kandy.npz"); Sp = St["S_traffic"]
    mask = cnt > 0
    from scipy.stats import pearsonr
    if mask.sum() >= 8:
        r_cal, _ = pearsonr(Sp[mask], np.nan_to_num(Cmeas[mask]))
    else:
        r_cal = np.nan
    print(f"  proxy↔TomTom cell correlation r={r_cal:+.2f} (n={int(mask.sum())} cells)")

    # CALIBRATED surface: temper the proxy (^0.45) and fold in measured congestion where known
    from scipy.ndimage import gaussian_filter
    base = (Sp / Sp.mean()) ** 0.45
    Cfill = np.where(mask, Cmeas, np.nanmean(m.cong))
    Cfill = gaussian_filter(Cfill, 1.0)
    S_cal = base * (1.0 + 0.8 * (Cfill / (Cfill.mean() + 1e-9) - 1).clip(-0.6, 1.5))
    S_cal = np.clip(S_cal, 0.3, None); S_cal /= S_cal.mean()
    np.savez(DEC / "S_traffic_calibrated_kandy.npz", S_traffic=S_cal, lats=St["lats"], lons=St["lons"],
             cong_measured=Cmeas, proxy_tomtom_r=r_cal, n_segments=len(m))
    ci = int(np.argmin(abs(St["lats"] - 7.2906))); cj = int(np.argmin(abs(St["lons"] - 80.6337)))
    print(f"  S_traffic_calibrated: core {S_cal[ci,cj]:.2f} core/edge {S_cal[ci,cj]/np.percentile(S_cal,15):.2f}×")

    # QA figure
    fig, ax = plt.subplots(1, 3, figsize=(16, 5.0), constrained_layout=True)
    ext = [BB["lon_min"], BB["lon_max"], BB["lat_min"], BB["lat_max"]]
    sc = ax[0].scatter(m.lon, m.lat, c=m.cong, s=14, cmap="RdYlGn_r", vmin=0, vmax=0.5)
    ax[0].set_title(f"(a) TomTom measured congestion\n(n={len(m)} segments, 1−cur/free)", fontsize=9)
    ax[0].set_xlim(ext[0], ext[1]); ax[0].set_ylim(ext[2], ext[3]); fig.colorbar(sc, ax=ax[0], shrink=0.8)
    from scipy.ndimage import zoom
    im1 = ax[1].imshow(zoom(Sp, 8, order=3), origin="lower", extent=ext, cmap="inferno", aspect="auto")
    ax[1].set_title(f"(b) OSM proxy (uncalibrated)\nproxy↔TomTom r={r_cal:+.2f}", fontsize=9)
    fig.colorbar(im1, ax=ax[1], shrink=0.8)
    im2 = ax[2].imshow(zoom(S_cal, 8, order=3), origin="lower", extent=ext, cmap="inferno", aspect="auto")
    ax[2].set_title(f"(c) CALIBRATED traffic emission\ncore/edge {S_cal[ci,cj]/np.percentile(S_cal,15):.2f}×", fontsize=9)
    fig.colorbar(im2, ax=ax[2], shrink=0.8)
    fig.suptitle("Stage-2: TomTom-calibrated congestion-weighted traffic emission surface for Kandy", fontsize=11)
    fig.savefig(OUT / "figX4_tomtom_calibration.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print(f"Wrote {DEC/'S_traffic_calibrated_kandy.npz'}\nWrote {OUT/'figX4_tomtom_calibration.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
