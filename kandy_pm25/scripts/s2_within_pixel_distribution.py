"""S2 -- a within-pixel distribution for the shipped 1 km field.

Registered at https://osf.io/bkpyr/ (2026-09-01) BEFORE this ran.

WHY. The shipped parquet carries `pm25_q50/q05/q95/blo/bhi`, every one of which is uncertainty
on the AREAL MEAN. There is no within-pixel quantity at all, so the question the whole project
exists to answer -- "is it bad where I live?" -- is structurally unanswerable.

WHAT S1 CHANGED. S1 (F.89) refuted the idea that a finer grid would let the model say WHICH
corner of a cell is dirty: at 94 m the paired microsites still read 1.135x against 27.5x
observed. The contrast exists (18.7x at 998 m after dispersion) but it is in the wrong places.
That kills a pointwise product and leaves a distributional one intact, because a distribution
does not need placement. "This cell spans roughly this range" is defensible where "it is worse
at your corner" is not. S2 builds only the defensible claim.

CONSTRUCTION. The model is additive: PM = B + increment, and B is spatially uniform by
construction. So only the increment may be structured:

    PM_fine = B(t)  +  increment_cell(t) * w_fine ,      mean(w_fine) = 1 within each cell

The unit mean of w inside every cell makes the cell mean EXACTLY preserved -- this is the same
gauge argument as C1/C4 in the specification, applied one level down. S2c tests it rather than
assuming it, because a construction requirement that is never checked is a construction hope.

`w` comes from the dispersed 94 m field of S1, normalised within each coarse cell.

⚠ WHAT THIS IS NOT. It does not say where in the cell the high values are. It says how wide the
distribution inside the cell is. Given F.89 that distinction is the whole product.

Usage:  .venv/Scripts/python.exe scripts/s2_within_pixel_distribution.py
Out:    data/processed/modular/s2_within_pixel.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from config import KANDY_PINN_BBOX as BB                       # noqa: E402
from src.stage1_satml.decomp import terrain_transport as TT    # noqa: E402
from s1_subgrid_placement import grids, midday_forcing, SITES   # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "data" / "processed" / "modular" / "s2_within_pixel.csv"
YEAR = 2023
P1_TOL = 0.05           # the specification's T1 gate on basin-mean drift

# Observed within-city spread by SUPPORT, from the three Kandy datasets (CONTEXT.md section 4).
# Only Elangasinghe is available per site; the other two are published spreads only, so S2b is
# tested per-site for the first and spread-to-spread for the rest. Stated, not glossed.
OBSERVED = [
    ("Elangasinghe 2008", "3 h kerbside, 1.5 m", 85.0, True),
    ("Wickramasinghe 2011", "8 h area-representative", 4.0, False),
    ("Premasiri 2010 (NBRO)", "24 h fixed sites", 3.0, False),
]


def main() -> None:
    # ── the shipped field and its background ──────────────────────────────────────────────
    f = pd.read_parquet(DEC / f"kandy_decomp_predictions_{YEAR}_additive_v3.parquet")
    b = pd.read_parquet(DEC / f"B_background_hourly_{YEAR}_v2.parquet")
    bcol = next(c for c in b.columns if c.lower().startswith("b"))
    f["time"] = pd.to_datetime(f.time)
    b = b.reset_index() if b.index.name else b
    tcol = next(c for c in b.columns if "time" in c.lower() or "date" in c.lower())
    b[tcol] = pd.to_datetime(b[tcol])
    bmap = dict(zip(b[tcol], b[bcol]))

    # midday hours, matching S1 and the transect's own window. The parquet is UTC and Sri Lanka
    # is UTC+5:30, so 11-13 LT is 05:30-07:30 UTC -- filtering on the UTC hour would sample the
    # evening rush instead. Same trap S1 hit.
    f["h"] = (f.time + pd.Timedelta(hours=5, minutes=30)).dt.hour
    mid = f[f.h.between(11, 13)].copy()
    mid["B"] = mid.time.map(bmap)
    mid = mid.dropna(subset=["B"])
    cell = mid.groupby(["lat", "lon"]).agg(pm=("pm25_q50", "mean"), B=("B", "mean")).reset_index()
    lats = np.sort(cell.lat.unique()); lons = np.sort(cell.lon.unique())
    PM = cell.pivot(index="lat", columns="lon", values="pm").values
    Bv = float(cell.B.mean())
    inc = np.clip(PM - Bv, 0, None)
    print(f"shipped {YEAR} midday field: {PM.shape[0]}x{PM.shape[1]} cells, "
          f"mean {PM.mean():.2f}, B {Bv:.2f}, increment mean {inc.mean():.2f}")
    print(f"between-pixel p90/p10 = {np.percentile(PM,90)/np.percentile(PM,10):.3f}x")

    # ── the 94 m weight field ─────────────────────────────────────────────────────────────
    u, v, blh = midday_forcing()
    fl, flo, zf, S, dx = grids(160, True)
    _, _, _, _, C = TT.solve_terrain(u, v, blh, lats=fl, lons=flo, z=zf, S=S, dx=dx)
    C = np.clip(C, 0, None)
    print(f"94 m dispersed field: p90/p10 {np.percentile(C[C>0],90)/np.percentile(C[C>0],10):.2f}x")

    # map each fine cell to its coarse cell
    fi = np.abs(fl[:, None] - lats[None, :]).argmin(1)
    fj = np.abs(flo[:, None] - lons[None, :]).argmin(1)

    rows, within = [], []
    drift = []
    for ci in range(len(lats)):
        for cj in range(len(lons)):
            sub = C[np.ix_(fi == ci, fj == cj)]
            if sub.size < 4 or sub.mean() <= 0:
                continue
            w = sub / sub.mean()                       # unit mean within the cell, by construction
            vals = Bv + inc[ci, cj] * w                # only the increment is structured
            drift.append(float(vals.mean() - PM[ci, cj]))
            within.append((np.percentile(vals, 90) / np.percentile(vals, 10),
                           vals.max() / max(vals.min(), 1e-9), vals.min(), vals.max(),
                           lats[ci], lons[cj], vals))

    p90p10 = np.array([w[0] for w in within])
    maxmin = np.array([w[1] for w in within])
    md = float(np.max(np.abs(drift)))
    print(f"\n{len(within)} cells with a within-cell distribution")
    print(f"  within-pixel p90/p10 : median {np.median(p90p10):.3f}x  "
          f"(p90 of cells {np.percentile(p90p10,90):.3f}x)")
    print(f"  within-pixel max/min : median {np.median(maxmin):.3f}x")
    print(f"  max cell-mean drift  : {md:.2e} ug/m3   (P1 gate {P1_TOL})")

    between = float(np.percentile(PM, 90) / np.percentile(PM, 10))
    rows += [dict(kind="summary", label="between_pixel_p90p10", value=round(between, 4)),
             dict(kind="summary", label="within_pixel_p90p10_median",
                  value=round(float(np.median(p90p10)), 4)),
             dict(kind="summary", label="within_pixel_maxmin_median",
                  value=round(float(np.median(maxmin)), 4)),
             dict(kind="summary", label="max_cell_mean_drift", value=float(md)),
             dict(kind="summary", label="n_cells", value=len(within))]

    # ── S2b: do kerbside sites sit high in their own cell's predicted distribution? ───────
    print("\n=== S2b: where do the transect sites fall in their OWN cell's distribution? ===")
    cellmap = {(round(w[4], 4), round(w[5], 4)): w[6] for w in within}
    qs = []
    for sid, name, la, lo, obs, cens in SITES:
        ci = int(np.abs(lats - la).argmin()); cj = int(np.abs(lons - lo).argmin())
        key = (round(lats[ci], 4), round(lons[cj], 4))
        if key not in cellmap:
            continue
        # the site's OBSERVED value expressed as a quantile of the predicted within-cell spread,
        # after rescaling observation to the cell's own level (obs is PM10, model PM2.5 -- only
        # the RELATIVE position is meaningful, which is exactly what a quantile is)
        d = cellmap[key]
        rel = obs / np.mean([s[4] for s in SITES])
        pred_rel = d / d.mean()
        q = float((pred_rel <= rel).mean())
        qs.append((name, obs, cens, q))
        print(f"  {name:<26} obs {obs:>6.1f}  quantile in cell {q:5.2f}"
              + ("   [censored]" if cens else ""))
        rows.append(dict(kind="site_quantile", label=name, value=round(q, 3), note=f"obs={obs}"))

    kerb = np.mean([q for _, o, _, q in qs if o >= 100])
    quiet = np.mean([q for _, o, _, q in qs if o < 40])
    print(f"\n  mean quantile, high-obs kerbside sites (>=100): {kerb:.2f}")
    print(f"  mean quantile, low-obs quiet sites      (<40) : {quiet:.2f}")

    # ── registered predictions ────────────────────────────────────────────────────────────
    s2a = float(np.median(p90p10)) > between
    s2b = kerb > quiet
    s2c = md <= P1_TOL
    print("\n=== REGISTERED PREDICTIONS (osf.io/bkpyr) ===")
    print(f"  S2a  {'HELD    ' if s2a else 'REFUTED '}  within-pixel spread "
          f"({np.median(p90p10):.3f}x) exceeds between-pixel ({between:.3f}x)")
    print(f"  S2b  {'HELD    ' if s2b else 'REFUTED '}  kerbside sites sit higher in their cell's "
          f"distribution than quiet ones ({kerb:.2f} vs {quiet:.2f})")
    print(f"  S2c  {'HELD    ' if s2c else 'REFUTED '}  cell mean preserved "
          f"(max drift {md:.2e} <= {P1_TOL})")
    for k, ok in [("S2a", s2a), ("S2b", s2b), ("S2c", s2c)]:
        rows.append(dict(kind="prediction", label=k, value=int(ok)))

    print("\n=== observed spread by support (context; only the first is per-site) ===")
    for nm, sup, sp, per_site in OBSERVED:
        print(f"  {nm:<24} {sup:<26} {sp:>6.1f}x" + ("" if per_site else "   [spread only]"))
        rows.append(dict(kind="observed", label=nm, value=sp, note=sup))

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
