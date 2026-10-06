"""spatial_curve_dl_tasks.py -- the data side of the deep arms E10/E11 (OSF amendment 26hp8).

Lays out the frozen frame for cross-city training and assigns the five country-grouped folds.
Nothing is standardised here: every scaler is fitted on the training folds inside the training
code, because fitting one here, over every city, would leak the test fold's statistics into the
model that is later scored on it.

FOLDS (registered: "five folds, grouped by country, so that no national network appears on both
sides of a split"). Countries are assigned greedily, largest first, each to the fold that currently
holds the fewest cities; ties break by fold index and country code, so the assignment is fully
deterministic. One fold is necessarily Japan- or Korea-heavy: those two supply most of the frame,
and a country cannot be split across folds by construction.

INPUT PER POINT for both architectures: x_km, y_km (local, per city) and the seven registered
covariates. Targets: PM2.5 at held-out sites, per day (Q2) and as window means (Q1).

SPLITS are the analysis script's own, exported with --export-splits, so E10 and E11 are scored on
exactly the fitting and held-out sets E0-E9 were scored on.

Usage: .venv/Scripts/python.exe scripts/spatial_curve_dl_tasks.py
Out:   data/processed/modular/spatial_curve/dl/{cities,sites,daily,static}.parquet, grids/*.parquet,
       folds.json, splits_*.parquet, MANIFEST.json
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
SC = REPO / "data" / "processed" / "modular" / "spatial_curve"
DL = SC / "dl"
COVARS = ["lc_built_2400", "lc_built_300", "ntl_1000", "pop_1000", "ndvi_1000",
          "road_major_300", "dist_major_km"]
N_FOLDS = 5
FRAMES = {"registered": "", "s70": "_s70"}


def to_km(lat, lon):
    lat0, lon0 = float(np.mean(lat)), float(np.mean(lon))
    return 111.32 * (lon - lon0) * np.cos(np.radians(lat0)), 110.57 * (lat - lat0)


def assign_folds(cities: pd.DataFrame) -> dict[str, int]:
    per = cities.groupby("country").cluster.nunique().sort_values(ascending=False)
    order = sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))
    load = [0] * N_FOLDS
    fold = {}
    for ctry, n in order:
        f = min(range(N_FOLDS), key=lambda i: (load[i], i))
        fold[ctry] = f
        load[f] += n
    return fold


def main() -> int:
    DL.mkdir(parents=True, exist_ok=True)
    (DL / "grids").mkdir(exist_ok=True)

    cities, sites, daily = [], [], []
    for name, sfx in FRAMES.items():
        fc, fs, fd = SC / f"frame_cities{sfx}.csv", SC / f"frame_sites{sfx}.csv", \
            SC / f"frame_daily{sfx}.parquet"
        if not (fc.exists() and fs.exists() and fd.exists()):
            print(f"frame {name}: missing, skipped")
            continue
        c = pd.read_csv(fc)
        c = c[c.primary.astype(bool) | c.secondary.astype(bool) | c.band_arm.astype(bool)]
        c = c.assign(frame=name)
        cities.append(c[["cluster", "country", "band", "sites", "primary", "secondary",
                         "band_arm", "window_start", "window_end", "frame"]])
        s = pd.read_csv(fs)
        sites.append(s[s.cluster.isin(c.cluster)].assign(frame=name))
        d = pd.read_parquet(fd)
        daily.append(d[d.cluster.isin(c.cluster)].assign(frame=name))
    if not cities:
        raise SystemExit("no frame found")
    C = pd.concat(cities, ignore_index=True)
    S = pd.concat(sites, ignore_index=True)
    Dd = pd.concat(daily, ignore_index=True)

    pred = pd.read_csv(SC / "frame_predictors.csv")
    miss = [c for c in COVARS if c not in pred]
    if miss:
        raise SystemExit(f"frame_predictors.csv lacks {miss}; D4 merge has not completed")
    S = S.merge(pred[["site"] + COVARS], on="site", how="left")
    nan_sites = int(S[COVARS].isna().any(axis=1).sum())
    if nan_sites:
        print(f"⚠ {nan_sites} site-frame rows carry a missing covariate; they are kept and flagged")
    S["cov_complete"] = ~S[COVARS].isna().any(axis=1)

    # local coordinates per city (the same site gets the same x,y in every frame)
    xy = []
    for cl, g in S.drop_duplicates("site").groupby("cluster"):
        x, y = to_km(g.lat.to_numpy(), g.lon.to_numpy())
        xy.append(pd.DataFrame({"site": g.site.to_numpy(), "x_km": x, "y_km": y}))
    S = S.merge(pd.concat(xy), on="site", how="left")

    # folds over the UNION of frame cities, so a city keeps its fold in every frame
    uc = C.drop_duplicates("cluster")[["cluster", "country"]]
    folds = assign_folds(uc)
    C["fold"] = C.country.map(folds)
    S = S.merge(C.drop_duplicates("cluster")[["cluster", "fold"]], on="cluster", how="left")

    C.to_parquet(DL / "cities.parquet", index=False)
    S.to_parquet(DL / "sites.parquet", index=False)
    Dd.to_parquet(DL / "daily.parquet", index=False)
    S[["frame", "cluster", "site", "static_mean"]].to_parquet(DL / "static.parquet", index=False)
    (DL / "folds.json").write_text(json.dumps(folds, indent=2), encoding="utf-8")

    n_grid = 0
    for cl in uc.cluster:
        f = SC / "predictors" / f"{cl}_bench_grid.csv"
        if f.exists():
            pd.read_csv(f).to_parquet(DL / "grids" / f"{cl}.parquet", index=False)
            n_grid += 1
    if n_grid < len(uc):
        print(f"⚠ benchmark rasters for {n_grid} of {len(uc)} cities; E10 needs all of them")

    n_split = 0
    for sub in ("analysis", "analysis_s70"):
        for fn in ("splits_q1_primary.parquet", "splits_q2.parquet"):
            f = SC / sub / fn
            if f.exists():
                shutil.copy2(f, DL / f"{sub}_{fn}")
                n_split += 1
    if n_split < 4:
        print(f"⚠ {n_split} of 4 split files present; run the analysis with --export-splits for both "
              f"frames before training")

    fold_tab = C.drop_duplicates("cluster").groupby("fold").agg(
        cities=("cluster", "nunique"), countries=("country", lambda x: sorted(set(x))))
    manifest = dict(registration="OSF rqn4y + amendment 26hp8", covariates=COVARS,
                    folds=folds, fold_summary=fold_tab.reset_index().to_dict("records"),
                    cities=int(uc.cluster.nunique()), sites=int(S.site.nunique()),
                    daily_rows=int(len(Dd)), grids=n_grid, split_files=n_split)
    (DL / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print(json.dumps(manifest, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
