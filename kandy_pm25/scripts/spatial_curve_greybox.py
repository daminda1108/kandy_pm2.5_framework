"""spatial_curve_greybox.py -- E7 for the spatial learning curve (OSF rqn4y, 2026-09-10).

E7 is the grey-box model's spatial prediction at the frame's Medellín sites, and it is taken from
what the model actually DELIVERS, not reconstructed: the time-mean of the shipped additive_v3 field
(pm25_q50) over exactly the frame's analysis window, interpolated bilinearly to each site.

WHY THE DELIVERED FIELD. The headline pattern P = S_emit x (1 + kappa * w(t) * c) varies by hour
through the boundary-layer confinement weight w(t), and the delivered field also carries the
increment split, so the field's spatial ranking is P weighted by accumulation hours. The
registration asks for E7's fixed spatial ranking; the time-mean of the delivered field over the
scoring window is that ranking, with no approximation introduced here.

SITES OUTSIDE THE MODEL GRID get NaN. Nothing is extrapolated. The analysis scores E7 only on the
held-out sites inside the grid, and scores every other estimator on that same subset so that the
comparison stays paired (deviation D-5).

The yearly field files are about 36 million rows each; they are streamed in batches.

Usage: .venv/Scripts/python.exe scripts/spatial_curve_greybox.py
Out:   data/processed/modular/spatial_curve/frame_greybox.csv   (site, greybox, inside_grid)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.interpolate import RegularGridInterpolator

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
SC = REPO / "data" / "processed" / "modular" / "spatial_curve"
FIELD = REPO / "data" / "processed" / "decomp_medellin"
CLUSTER = 66                      # Medellín in the frozen frame
BATCH = 4_000_000


def window() -> tuple[pd.Timestamp, pd.Timestamp]:
    """The analysis window, required to be identical in every frame that holds the cluster."""
    wins = set()
    for sfx in ("", "_s70"):
        f = SC / f"frame_cities{sfx}.csv"
        if f.exists():
            c = pd.read_csv(f).set_index("cluster")
            if CLUSTER in c.index and isinstance(c.loc[CLUSTER, "window_start"], str):
                wins.add((c.loc[CLUSTER, "window_start"], c.loc[CLUSTER, "window_end"]))
    if len(wins) != 1:
        raise SystemExit(f"cluster {CLUSTER} has {len(wins)} distinct windows across frames: {wins}")
    w0, w1 = wins.pop()
    return pd.Timestamp(w0), pd.Timestamp(w1) + pd.Timedelta(days=1)   # [w0, w1 + 1 day)


def main() -> int:
    w0, w1 = window()
    years = range(w0.year, w1.year + 1)
    files = [FIELD / f"medellin_decomp_predictions_{y}_additive_v3.parquet" for y in years]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"field files missing for the window: {missing}")
    print(f"E7 window {w0.date()} .. {(w1 - pd.Timedelta(days=1)).date()} from {[f.name for f in files]}")

    acc = None
    hours = set()
    for f in files:
        for b in pq.ParquetFile(f).iter_batches(batch_size=BATCH,
                                                columns=["time", "lat", "lon", "pm25_q50"]):
            d = b.to_pandas()
            t = pd.to_datetime(d.time)
            if t.dt.tz is not None:
                t = t.dt.tz_convert("UTC").dt.tz_localize(None)
            d = d[(t >= w0) & (t < w1)]
            if d.empty:
                continue
            hours.update(pd.to_datetime(d.time).unique().tolist())
            g = d.groupby(["lat", "lon"]).pm25_q50.agg(["sum", "count"])
            acc = g if acc is None else acc.add(g, fill_value=0)
    if acc is None:
        raise SystemExit("no field rows inside the window")
    acc["mean"] = acc["sum"] / acc["count"]
    lats = np.sort(acc.index.get_level_values("lat").unique().to_numpy())
    lons = np.sort(acc.index.get_level_values("lon").unique().to_numpy())
    grid = acc["mean"].unstack("lon").reindex(index=lats, columns=lons).to_numpy()
    cnt = acc["count"]
    print(f"grid {len(lats)} x {len(lons)} | hours in window {len(hours):,} | "
          f"per-cell count min {int(cnt.min()):,} max {int(cnt.max()):,} | "
          f"NaN cells {int(np.isnan(grid).sum())}")
    if np.isnan(grid).any():
        raise SystemExit("the field grid has empty cells inside the window; refusing to interpolate")

    sites = pd.concat([pd.read_csv(SC / f"frame_sites{sfx}.csv")
                       for sfx in ("", "_s70") if (SC / f"frame_sites{sfx}.csv").exists()])
    sites = sites[sites.cluster == CLUSTER].drop_duplicates("site")
    f_int = RegularGridInterpolator((lats, lons), grid, bounds_error=False, fill_value=np.nan)
    vals = f_int(np.c_[sites.lat.to_numpy(), sites.lon.to_numpy()])
    out = pd.DataFrame({"site": sites.site.to_numpy(), "greybox": vals,
                        "inside_grid": np.isfinite(vals)})
    tmp = SC / "frame_greybox.tmp"
    out.to_csv(tmp, index=False)
    tmp.replace(SC / "frame_greybox.csv")
    print(f"wrote frame_greybox.csv: {len(out)} Medellín sites, {int(out.inside_grid.sum())} inside "
          f"the model grid, E7 range {np.nanmin(vals):.2f} .. {np.nanmax(vals):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
