"""embedding_spatial_test.py -- do EO foundation-model embeddings break the spatial ceiling?

REGISTERED AT https://osf.io/6udm3/ (project ng2tc) BEFORE THIS WAS WRITTEN.
Pre-registration: docs/prereg_embedding_spatial_2026-09-09.md.

THE BAR, FIXED IN THE REGISTRATION AND NOT NEGOTIABLE HERE:

    benchmark              rho = 0.301   best single free raster, built-up land cover at 2.4 km
    detectable at 80%      0.130         F.105's limit on this frame, 47 cities / 636 stations
    THE BAR                paired median improvement > 0.130 with a bootstrap interval over
                           cities that excludes 0.130

WHY THIS IS WORTH RUNNING AT ALL, given six prior nulls. The embedding null already on record
(F.27) was run on three cities and 33 stations, and this project's own ledger (F.28) puts its
minimum detectable partial correlation at 0.65 to 0.96 -- it could only ever have excluded a large
effect. The F.105 frame resolves 0.130. The question has never been asked where the power is.

WHAT IS BEING TESTED IS INFORMATION, NOT CAPACITY. F.105 already showed that seven model families
cannot beat a single free raster on the assembled covariates. Embeddings are a different
information source, so they test the other half of the claim.

E1  embeddings alone beat the benchmark by more than the detection limit
E2  embeddings ADDED to the 60 existing predictors beat that set by more than the limit
E3  embeddings carry signal independent of the benchmark (partial correlation, pooled)
E4  exploratory: is any skill concentrated in a few bands, as the Quito study reports

Registered expectation: E1 and E2 FAIL, E3 undetectable. Written down so that a failure cannot be
presented afterwards as a prediction, and a pass cannot be presented as expected.

[!] ADMISSIBILITY RISK DECLARED IN THE REGISTRATION. AlphaEarth is not known to ingest ground PM2.5
monitors, but this project has been caught once by a fused product that silently contained the
observations it was pricing (C1/F.95). A PASS is therefore provisional until the training corpus is
checked; a FAILURE needs no such check, since contamination could only inflate a score.

Usage: .venv/Scripts/python.exe scripts/embedding_spatial_test.py [--pull] [--boot 4000]
Out:   data/processed/modular/embedding_spatial_test.{csv,json}
       data/processed/modular/station_embeddings.csv   (cached GEE pull)
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import RidgeCV

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
warnings.filterwarnings("ignore")

MOD = REPO / "data" / "processed" / "modular"
EMB = MOD / "station_embeddings.csv"
OUT = MOD / "embedding_spatial_test.csv"
OUT_JSON = MOD / "embedding_spatial_test.json"

ASSET = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
YEAR = "2023"            # midpoint of the panel's span, fixed in the registration
BUFFER_M = 100           # fixed in the registration
BENCH = "lc_built_2400"
BENCH_RHO = 0.301        # F.105
DETECT = 0.130           # F.105
MIN_STATIONS = 6
SEED = 20260909
DROP = {"city", "band", "src", "station_id", "lat", "lon", "pm"}


def pull_embeddings(d: pd.DataFrame) -> pd.DataFrame:
    """Mean 64-dim embedding in a 100 m buffer around each station, from the 2023 mosaic.

    Chunked: reduceRegions on 636 features at once is the kind of request that returns a memory
    error rather than a result (gotcha #44), so this goes in batches and reports coverage.
    """
    import ee
    ee.Initialize(project="kandypinn")
    img = (ee.ImageCollection(ASSET)
           .filterDate(f"{YEAR}-01-01", f"{int(YEAR) + 1}-01-01").mosaic())
    bands = [f"A{i:02d}" for i in range(64)]
    rows = []
    d = d.reset_index(drop=True)
    for i in range(0, len(d), 80):
        chunk = d.iloc[i:i + 80]
        fc = ee.FeatureCollection([
            ee.Feature(ee.Geometry.Point([float(r.lon), float(r.lat)]).buffer(BUFFER_M),
                       {"row": int(j)})
            for j, r in chunk.iterrows()])
        res = img.select(bands).reduceRegions(fc, ee.Reducer.mean(), 10).getInfo()
        for f in res["features"]:
            p = f["properties"]
            rows.append({"row": p["row"], **{b: p.get(b) for b in bands}})
        print(f"    pulled {min(i + 80, len(d))}/{len(d)}", flush=True)
    e = pd.DataFrame(rows).set_index("row").sort_index()
    e.to_csv(EMB, index=True)
    return e


def loco_rho(X: np.ndarray, y: np.ndarray, city: np.ndarray, cities) -> dict:
    """Leave-one-CITY-out ridge, scored as within-city rank correlation on the held-out city."""
    out = {}
    for c in cities:
        te = city == c
        tr = ~te
        if te.sum() < MIN_STATIONS or tr.sum() < 50:
            continue
        try:
            m = RidgeCV(alphas=np.logspace(-2, 3, 24)).fit(X[tr], y[tr])
            p = m.predict(X[te])
        except Exception:
            continue
        if np.std(p) < 1e-12 or np.std(y[te]) < 1e-12:
            continue
        r = spearmanr(p, y[te]).statistic
        if np.isfinite(r):
            out[c] = float(r)
    return out


def paired(a: dict, b: dict, rng, n_boot: int) -> dict:
    """Median within-city difference, bootstrapped over cities. Never a difference of medians."""
    keys = sorted(set(a) & set(b))
    v = np.array([a[k] - b[k] for k in keys])
    if len(v) < 4:
        return {}
    idx = rng.integers(0, len(v), (n_boot, len(v)))
    m = np.median(v[idx], axis=1)
    lo, hi = np.percentile(m, [2.5, 97.5])
    return dict(n=len(v), median=float(np.median(v)), lo=float(lo), hi=float(hi),
                wins=int((v > 0).sum()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pull", action="store_true", help="re-pull embeddings from GEE")
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    print("=== do EO foundation-model embeddings break the spatial ceiling? ===")
    print(f"    registered at https://osf.io/6udm3/  |  bar: beat {BENCH_RHO} by > {DETECT}\n")

    d = pd.read_csv(MOD / "lur_predictors.csv")
    feats = [c for c in d.columns if c not in DROP and d[c].dtype.kind in "fi"]
    d = d.dropna(subset=[BENCH, "pm", "lat", "lon"]).reset_index(drop=True)
    d = d[d.groupby("city").city.transform("size") >= MIN_STATIONS].reset_index(drop=True)
    print(f"[1] frame: {len(d)} stations, {d.city.nunique()} cities, {len(feats)} existing predictors")

    if a.pull or not EMB.exists():
        print(f"[2] pulling {ASSET} @ {YEAR}, {BUFFER_M} m buffer")
        e = pull_embeddings(d)
    else:
        e = pd.read_csv(EMB, index_col=0)
        print(f"[2] cached embeddings: {EMB.name}")
    bands = [c for c in e.columns if c.startswith("A")]
    e = e.reindex(range(len(d)))
    cov = e[bands[0]].notna().mean()
    print(f"    {len(bands)} dims, coverage {100 * cov:.1f}% of stations")
    if cov < 0.90:
        raise SystemExit("coverage below 90%: reporting a failure to test, not a null")

    d = pd.concat([d, e[bands]], axis=1)
    d = d.dropna(subset=bands).reset_index(drop=True)
    d = d[d.groupby("city").city.transform("size") >= MIN_STATIONS].reset_index(drop=True)

    # within-city standardisation of BOTH sides, exactly as F.105 did
    for c in feats + bands:
        d[c] = d.groupby("city")[c].transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))
    d[feats + bands] = d[feats + bands].fillna(0.0)
    d["z"] = d.groupby("city").pm.transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))

    city = d.city.to_numpy()
    cities = sorted(d.city.unique())
    y = d.z.to_numpy()
    print(f"[3] scoring frame after merge: {len(d)} stations, {len(cities)} cities\n")

    bench = {c: float(spearmanr(d[d.city == c][BENCH], d[d.city == c].z).statistic)
             for c in cities if d[d.city == c][BENCH].std() > 0}
    bench = {k: v for k, v in bench.items() if np.isfinite(v)}

    emb_only = loco_rho(d[bands].to_numpy(), y, city, cities)
    existing = loco_rho(d[feats].to_numpy(), y, city, cities)
    combined = loco_rho(d[feats + bands].to_numpy(), y, city, cities)

    print(f"    {'model':<34}{'median rho':>12}{'cities':>8}")
    for lab, s in (("benchmark raster", bench), ("embeddings alone", emb_only),
                   ("60 existing predictors", existing),
                   ("existing + embeddings", combined)):
        print(f"    {lab:<34}{np.median(list(s.values())):>12.3f}{len(s):>8}")

    e1 = paired(emb_only, bench, rng, a.boot)
    e2 = paired(combined, existing, rng, a.boot)

    print(f"\n=== confirmatory tests, paired within city ===")
    print(f"    {'test':<38}{'paired':>9}{'95% over cities':>22}{'wins':>9}{'> limit':>9}")
    res = {}
    for tag, label, p, in (("E1", "E1 embeddings vs benchmark", e1),
                           ("E2", "E2 +embeddings vs existing", e2)):
        if not p:
            print(f"    {label:<38}   too few cities")
            continue
        passes = bool(p["lo"] > DETECT)
        print(f"    {label:<38}{p['median']:>+9.3f}   [{p['lo']:>+7.3f},{p['hi']:>+7.3f}]"
              f"{p['wins']:>5}/{p['n']}{'PASS' if passes else 'fail':>9}")
        res[tag] = {**p, "passes_bar": passes}

    # E3: partial correlation with the benchmark regressed out, pooled over cities
    parts = []
    for c in cities:
        s = d[d.city == c]
        if len(s) < MIN_STATIONS:
            continue
        pred = emb_only.get(c)
        if pred is None:
            continue
        b = s[BENCH].to_numpy()
        zz = s.z.to_numpy()
        if np.std(b) < 1e-12:
            continue
        rz = zz - np.polyval(np.polyfit(b, zz, 1), b)
        m = RidgeCV(alphas=np.logspace(-2, 3, 24))
        try:
            m.fit(d[d.city != c][bands].to_numpy(), d[d.city != c].z.to_numpy())
            pe = m.predict(s[bands].to_numpy())
        except Exception:
            continue
        rp = pe - np.polyval(np.polyfit(b, pe, 1), b)
        if np.std(rp) < 1e-12 or np.std(rz) < 1e-12:
            continue
        r = spearmanr(rp, rz).statistic
        if np.isfinite(r):
            parts.append(float(r))
    if parts:
        v = np.array(parts)
        idx = rng.integers(0, len(v), (a.boot, len(v)))
        mm = np.median(v[idx], axis=1)
        lo, hi = np.percentile(mm, [2.5, 97.5])
        res["E3"] = dict(n=len(v), median=float(np.median(v)), lo=float(lo), hi=float(hi),
                         excludes_zero=bool(lo > 0))
        print(f"\n    E3 partial rho, benchmark removed  {np.median(v):>+9.3f}"
              f"   [{lo:>+7.3f},{hi:>+7.3f}]   excludes 0: {'YES' if lo > 0 else 'no'}")

    print("\n=== the answer ===")
    passed = [k for k, v in res.items() if v.get("passes_bar")]
    if passed:
        print(f"    {', '.join(passed)} CLEARED the registered bar. The spatial ceiling does not")
        print(f"    hold in the form claimed. [!] PROVISIONAL until the AlphaEarth training corpus")
        print(f"    is checked for ground-monitor ingestion, per the registration.")
    else:
        print(f"    No confirmatory test cleared the bar. On {len(bench)} cities and {len(d)}")
        print(f"    stations, 64-dimensional EO foundation-model embeddings do not beat the best")
        print(f"    single globally available raster by more than {DETECT} in rank correlation.")
        print(f"    The previous embedding null could resolve 0.65; this one resolves {DETECT}.")

    pd.DataFrame([{"city": c, "bench": bench.get(c), "emb": emb_only.get(c),
                   "existing": existing.get(c), "combined": combined.get(c)}
                  for c in cities]).to_csv(OUT, index=False)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(dict(osf="6udm3", asset=ASSET, year=YEAR, buffer_m=BUFFER_M,
                       stations=int(len(d)), cities=int(len(bench)), dims=len(bands),
                       benchmark=BENCH, benchmark_rho=BENCH_RHO, detection_limit=DETECT,
                       median_rho=dict(
                           benchmark=round(float(np.median(list(bench.values()))), 4),
                           embeddings=round(float(np.median(list(emb_only.values()))), 4),
                           existing=round(float(np.median(list(existing.values()))), 4),
                           combined=round(float(np.median(list(combined.values()))), 4)),
                       tests=res, any_passed=bool(passed)), fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
