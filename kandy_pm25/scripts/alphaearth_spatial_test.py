"""alphaearth_spatial_test.py — do EO foundation-model embeddings carry within-city
spatial signal the physics pattern misses?

Pre-registered in docs/data_and_ml_frontier_2026-07-25.md. Gates G1-G4 fixed BEFORE
results were seen. Prior art constrains this: Track-S already showed the within-city
pattern is NOT learnable from hand-picked public covariates (roads/NTL/EDGAR,
rho~0.14). This tests a different INFORMATION source, not more capacity:
GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL (AlphaEarth) — 64-dim, 10 m, Sentinel-1 radar +
Sentinel-2 optical + Landsat + ERA5-Land + GEDI canopy compressed per pixel.

G1 (this script): at a monitored city, do the embeddings predict WITHHELD per-station
    annual means under leave-one-station-out, and do they carry signal INDEPENDENT of
    the physics pattern (partial correlation with the physics pattern regressed out)?
    Bar: LOSO Spearman rho >= 0.50 AND partial rho significantly > 0.
G2/G3 (only if G1 passes): blend and re-score; replicate at >=2 of 3 further cities.

Honest note: embeddings are ANNUAL, so this can only ever inform the SPATIAL pattern,
never the temporal anchor.

Out: results/figures/medellin_showcase/alphaearth_spatial_test.{csv,txt}
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xichang_paper_figures as xf

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "figures" / "medellin_showcase"
ASSET = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
SCALE = 10                      # native embedding resolution (m)


def sample_embeddings(st, years, buffer_m=500):
    """Mean 64-dim embedding in a buffer around each station, averaged over years.

    A buffer (not a point) because the target is a ~1 km grid cell's character: a
    single 10 m pixel would describe the rooftop the sensor sits on, not its
    neighbourhood. 500 m radius ~ the sub-kilometre neighbourhood scale.
    """
    import ee
    ee.Initialize(project="kandypinn")
    col = ee.ImageCollection(ASSET)
    imgs = [ee.Image(col.filterDate(f"{y}-01-01", f"{y+1}-01-01").mosaic()) for y in years]
    emb = ee.ImageCollection(imgs).mean()          # multi-year mean embedding
    feats = [ee.Feature(ee.Geometry.Point([float(r.lon), float(r.lat)]).buffer(buffer_m),
                        {"sid": str(sid)}) for sid, r in st.iterrows()]
    fc = ee.FeatureCollection(feats)
    red = emb.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=SCALE) \
        if hasattr(emb, "reduceRegions") else None
    if red is None:
        red = emb.reduceRegion  # fallback path below
    try:
        got = red.getInfo()["features"]
        rows = []
        for f in got:
            p = f["properties"]
            rows.append({"station_id": p.pop("sid"), **p})
        return pd.DataFrame(rows).set_index("station_id")
    except Exception:
        # per-station fallback (slower but robust across API versions)
        rows = []
        for sid, r in st.iterrows():
            g = ee.Geometry.Point([float(r.lon), float(r.lat)]).buffer(buffer_m)
            v = emb.reduceRegion(ee.Reducer.mean(), g, SCALE, maxPixels=1e9).getInfo()
            rows.append({"station_id": str(sid), **v})
        return pd.DataFrame(rows).set_index("station_id")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    # kathmandu has 39 held-out stations -> materially more power than Medellin's 17,
    # which is the one cheap way to firm up (or overturn) the n=17 null
    ap.add_argument("--city", default="medellin")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    city = a.city
    xf._setup(city)
    st, _ = xf._stations_split()
    hf = OUT / "holdout6.json"
    anchors = set(json.load(open(hf))["anchors"]) if (city == "medellin" and hf.exists()) else set()
    from city_config import cfg
    years = [y for y in cfg(city)["years"] if 2017 <= y <= 2025]

    # ── observed per-station annual means (the target) + the physics pattern ──────
    obs = pd.concat([xf._obs(y) for y in years], ignore_index=True)
    om = obs.groupby("station_id").pm25.agg(["mean", "count"])
    om = om[om["count"] >= 2000]                     # need a stable annual mean
    # physics pattern at each station = the shipped model's per-station annual mean
    dec = REPO / "data" / "processed" / f"decomp_{city}"
    fp = dec / f"{city}_decomp_predictions_{years[len(years)//2]}_additive_v2.parquet"
    if not fp.exists():
        fp = dec / f"{city}_decomp_predictions_{years[len(years)//2]}_additive_v3.parquet"
    d = pd.read_parquet(fp, columns=["lat", "lon", "pm25_q50"])
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    Z = d.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon") \
         .reindex(index=lats, columns=lons).values
    phys = {}
    for sid in om.index:
        if sid not in st.index:
            continue
        r = st.loc[sid]
        if not (lats.min() <= r.lat <= lats.max() and lons.min() <= r.lon <= lons.max()):
            continue
        phys[sid] = float(Z[int(np.abs(lats - r.lat).argmin()),
                            int(np.abs(lons - r.lon).argmin())])
    ids = [s for s in om.index if s in phys and s not in anchors]   # withheld only
    print(f"withheld in-box stations with a stable annual mean: {len(ids)}")

    E = sample_embeddings(st.loc[[i for i in ids]], years)
    bands = [c for c in E.columns if c.startswith("A")] or list(E.columns)
    E = E[bands].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    ids = [i for i in ids if i in E.index]
    X = E.loc[ids].to_numpy(float)
    y = om.loc[ids, "mean"].to_numpy(float)
    p = np.array([phys[i] for i in ids])
    print(f"design: n={len(ids)} stations x {X.shape[1]} embedding dims")

    # ── G1: leave-one-station-out ridge on the embeddings ────────────────────────
    from sklearn.linear_model import RidgeCV
    from sklearn.preprocessing import StandardScaler
    from scipy.stats import spearmanr
    pred = np.full(len(y), np.nan)
    for k in range(len(y)):
        tr = np.arange(len(y)) != k
        sc = StandardScaler().fit(X[tr])
        m = RidgeCV(alphas=np.logspace(-1, 4, 24)).fit(sc.transform(X[tr]), y[tr])
        pred[k] = m.predict(sc.transform(X[k:k + 1]))[0]
    rho_emb = spearmanr(pred, y).statistic
    rho_phys = spearmanr(p, y).statistic
    # partial: does the embedding prediction explain obs beyond the physics pattern?
    def resid(a, b):
        b1 = np.column_stack([np.ones_like(b), b])
        return a - b1 @ np.linalg.lstsq(b1, a, rcond=None)[0]
    pr = spearmanr(resid(pred, p), resid(y, p))
    lines = ["AlphaEarth embeddings vs the physics pattern — G1 at " + city.upper() + "",
             "=" * 70,
             f"stations (withheld, in-box, stable mean): n = {len(ids)}",
             f"embedding dims: {X.shape[1]}   asset: {ASSET} @ {SCALE} m",
             "",
             f"  LOSO embedding-only   Spearman rho = {rho_emb:+.3f}",
             f"  physics pattern       Spearman rho = {rho_phys:+.3f}",
             f"  PARTIAL (physics regressed out) rho = {pr.statistic:+.3f}  p = {pr.pvalue:.3f}",
             ""]
    g1a = rho_emb >= 0.50
    g1b = (pr.statistic > 0) and (pr.pvalue < 0.10)
    lines.append(f"G1a  LOSO rho >= 0.50            : {'PASS' if g1a else 'FAIL'}")
    lines.append(f"G1b  independent signal (partial): {'PASS' if g1b else 'FAIL'}")
    lines.append("")
    if g1a and g1b:
        lines.append("VERDICT G1 PASS -> proceed to G2 (blend) and G3 (cross-city).")
    else:
        lines.append("VERDICT G1 FAIL -> record as a further independent null; the")
        lines.append("information-ceiling claim strengthens. Do NOT proceed to G2.")
    pd.DataFrame({"station_id": ids, "obs": y, "phys": p, "emb_loso": pred}) \
        .to_csv(OUT / f"alphaearth_spatial_test_{city}.csv", index=False)
    txt = "\n".join(lines)
    (OUT / f"alphaearth_spatial_test_{city}.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
