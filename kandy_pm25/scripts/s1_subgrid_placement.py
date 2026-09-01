"""S1 -- does the model's own sub-grid field place within-city contrast?

Registered at https://osf.io/bkpyr/ (2026-09-01) BEFORE this ran. Predictions, with their
refutation criteria, are reproduced in PRED below and scored automatically at the end.

THE FINDING THAT OPENED THIS. `S_traffic_kandy.npz` ships `E_fine` at 160x160 (94 m) beside the
16x16 (998 m) surface the shipped product reports on. At the paired botanical-garden microsites
-- 300 m apart, one 998 m pixel -- the shipped field gives 1.000x and raw `E_fine` gives 2.25x,
correctly signed, against 27.5x observed. So the model contains sub-grid structure it discards.

The question is what survives PHYSICS. Emission is not concentration: dispersion smooths, and
the production path additionally (a) log-tempers the emission surface and (b) solves at N=64
(238 m) before aggregating to 998 m. This script separates those three effects, because
"the model cannot resolve it" and "the build throws it away" are different claims with
different fixes.

ADMISSIBILITY (registered). The Elangasinghe transect is held out of ALL fitting -- nothing here
is fitted. Solver parameters are the cross-city calibrated values already in the module;
`s_exp` stays at 1.0 (F.77). This is a pure forward run.

Usage:  .venv/Scripts/python.exe scripts/s1_subgrid_placement.py
Out:    data/processed/modular/s1_subgrid_placement.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from config import KANDY_PINN_BBOX as BB                       # noqa: E402
from src.stage1_satml.decomp import terrain_transport as TT    # noqa: E402

OUT = REPO / "data" / "processed" / "modular" / "s1_subgrid_placement.csv"
DEC = REPO / "data" / "processed" / "decomp"
PINN = REPO / "data" / "processed" / "pinn_inputs"

# The two microsite pairs from Elangasinghe & Shanthini (2008). Both pairs sit inside a single
# 998 m pixel in the shipped product, which is why the shipped ratio is exactly 1.000.
PAIRS = [
    ("botanical garden", (7.2682, 80.5974, 110.0), (7.2707, 80.5963, 4.0)),
    ("girls' HS",        (7.2870, 80.6262, 150.0), (7.2870, 80.6262, 32.5)),
]
# Full transect, for the rank test. obs is PM10 (model is PM2.5) so only ratios are meaningful;
# `cens` marks the four sites censored at 150 and the three binned at 32.5.
SITES = [
    ("1.1", "Kandy bus terminus",       7.2896, 80.6338, 150.0, True),
    ("1.2", "Girls' HS junction",       7.2870, 80.6262, 150.0, True),
    ("1.4", "Kandy Police Station",     7.2928, 80.6337, 150.0, True),
    ("1.7", "Sangaraja Mawatha",        7.2894, 80.6463, 150.0, True),
    ("2.1", "Girls' HS INSIDE grounds", 7.2870, 80.6262, 32.5, False),
    ("2.2", "Pushpadana Girls'",        7.2940, 80.6329, 32.5, False),
    ("2.3", "Trinity College",          7.2999, 80.6376, 32.5, False),
    ("3.1", "Gatambe temple",           7.2676, 80.6008, 230.0, False),
    ("3.2", "Bot.Gardens ENTRANCE",     7.2682, 80.5974, 110.0, False),
    ("4.2", "Katugastota junction",     7.3221, 80.6250, 340.0, False),
    ("5.1", "Gannoruwa school",         7.2851, 80.5895, 15.0, False),
    ("5.5", "Bot.Gardens 300m INSIDE",  7.2707, 80.5963, 4.0, False),
]

PRED = {
    "S1a": ("dispersed 94 m separates the paired sites by > 1.5x", lambda r: r["paired_min"] > 1.5),
    "S1b": ("it recovers < 27.5x -- dispersion damps emission contrast",
            lambda r: r["paired_max"] < 27.5),
    "S1c": ("rank correlation exceeds the 1 km field's rho = +0.44", lambda r: r["rho_fine"] > 0.44),
    "S1d": ("p90/p10 of the dispersed field lands between 1.23x and 63.8x",
            lambda r: 1.23 < r["p90p10_fine"] < 63.8),
}


def midday_forcing() -> tuple:
    """Climatological 11-13 LT wind and BLH -- the transect's own sampling window."""
    blh = pd.read_parquet(REPO / "data/external/kandy/era5_hourly/kandy_era5_blh_hourly.parquet")
    # same UTC+5:30 correction as the wind below
    blh["h"] = (pd.to_datetime(blh.datetime) + pd.Timedelta(hours=5, minutes=30)).dt.hour
    b = float(blh[blh.h.between(11, 13)].blh_m.mean())
    d = pd.read_parquet(REPO / "data/processed/stage1_v3/dataset_v3_hourly.parquet",
                        columns=["datetime_utc", "u10", "v10"])
    # Sri Lanka is UTC+5:30, so the transect's 11-13 LT window is 05:30-07:30 UTC. Filtering on
    # the UTC hour would sample the wrong part of the day entirely.
    lt = pd.to_datetime(d.datetime_utc) + pd.Timedelta(hours=5, minutes=30)
    m = d[lt.dt.hour.between(11, 13)]
    return float(m.u10.mean()), float(m.v10.mean()), b


def grids(n: int, temper: bool) -> tuple:
    """Elevation and emission on an n x n grid. `temper` applies the production log1p squash."""
    ze = np.load(PINN / "kandy_elev_grid_100m.npz")
    elat, elon, Z = ze["lat_grid"][:, 0], ze["lon_grid"][0, :], ze["elev"].astype(float)
    if elat[0] > elat[-1]: elat, Z = elat[::-1], Z[::-1, :]
    if elon[0] > elon[-1]: elon, Z = elon[::-1], Z[:, ::-1]
    tr = np.load(DEC / "S_traffic_kandy.npz")
    Ef, flat, flon = tr["E_fine"].astype(float), tr["fine_lat"], tr["fine_lon"]

    lats = np.linspace(BB["lat_min"], BB["lat_max"], n)
    lons = np.linspace(BB["lon_min"], BB["lon_max"], n)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    pts = np.stack([LA.ravel(), LO.ravel()], 1)
    z = RegularGridInterpolator((elat, elon), Z, bounds_error=False, fill_value=None)(pts).reshape(n, n)
    S = RegularGridInterpolator((flat, flon), Ef, bounds_error=False, fill_value=0.0)(pts).reshape(n, n)
    if temper:
        S = np.log1p(4.0 * np.clip(S, 0, None))
    S = S / (S.max() + 1e-9)
    dx = (BB["lat_max"] - BB["lat_min"]) * 111000.0 / (n - 1)
    return lats, lons, z, S, dx


def at(lats, lons, F, la, lo) -> float:
    return float(F[int(np.abs(lats - la).argmin()), int(np.abs(lons - lo).argmin())])


def spread(F) -> float:
    p = F[F > 0]
    return float(np.percentile(p, 90) / np.percentile(p, 10)) if p.size else np.nan


def main() -> None:
    u, v, blh = midday_forcing()
    print(f"midday (11-13 LT) forcing: u={u:+.3f} v={v:+.3f} m/s, BLH={blh:.0f} m\n")

    rows, fields = [], {}
    for label, n, temper in [("production N=64 tempered", 64, True),
                             ("fine N=160 tempered", 160, True),
                             ("fine N=160 RAW (no log squash)", 160, False)]:
        lats, lons, z, S, dx = grids(n, temper)
        print(f"[{label}]  dx = {dx:.0f} m, emission p90/p10 = {spread(S):.2f}x  ... solving")
        _, _, _, _, C = TT.solve_terrain(u, v, blh, lats=lats, lons=lons, z=z, S=S, dx=dx)
        C = np.clip(C, 0, None)
        fields[label] = (lats, lons, S, C, dx)
        print(f"    solved. concentration p90/p10 = {spread(C):.2f}x")

    # ── where does the contrast go? ────────────────────────────────────────────────────────
    tr = np.load(DEC / "S_traffic_kandy.npz")
    raw = tr["E_fine"].astype(float)
    print("\n=== contrast budget (p90/p10 over positive cells) ===")
    stages = [("1. raw E_fine, 94 m", spread(raw)),
              ("2. + log1p tempering", spread(fields["fine N=160 RAW (no log squash)"][2] * 0 +
                                              fields["fine N=160 tempered"][2])),
              ("3. + dispersion, 94 m", spread(fields["fine N=160 tempered"][3])),
              ("4. + solve at 238 m (production)", spread(fields["production N=64 tempered"][3]))]
    prev = None
    for name, val in stages:
        drop = "" if prev is None else f"   (x{prev / val:.2f} lost at this step)"
        print(f"  {name:<36} {val:8.2f}x{drop}")
        prev = val
        rows.append(dict(kind="contrast_budget", label=name, value=round(val, 3)))

    # aggregate the fine solution to the 998 m reporting grid
    lats, lons, S16, _, _ = grids(16, True)
    la_f, lo_f, _, Cf, _ = fields["fine N=160 tempered"]
    C16 = np.array([[Cf[np.abs(la_f - a).argmin(), np.abs(lo_f - b).argmin()]
                     for b in lons] for a in lats])
    print(f"  {'5. + report at 998 m':<36} {spread(C16):8.2f}x   "
          f"(x{spread(Cf) / spread(C16):.2f} lost at this step)")
    rows.append(dict(kind="contrast_budget", label="5. + report at 998 m",
                     value=round(spread(C16), 3)))

    # ── the paired sites ──────────────────────────────────────────────────────────────────
    print("\n=== paired microsites (support fixed, only location varies) ===")
    ratios = []
    for name, (la1, lo1, o1), (la2, lo2, o2) in PAIRS:
        obs_r = o1 / o2
        line = {"pair": name, "obs_ratio": round(obs_r, 2)}
        for label, (la_, lo_, _, C, _) in fields.items():
            a, b = at(la_, lo_, C, la1, lo1), at(la_, lo_, C, la2, lo2)
            line[label] = round(a / b if b > 0 else np.nan, 3)
        ratios.append(line["fine N=160 tempered"])
        print(f"  {name:<18} observed {obs_r:6.1f}x | "
              + " | ".join(f"{k.split()[0]} {line[k]:.3f}x" for k in fields))
        rows.append(dict(kind="paired", label=name, **{k: v for k, v in line.items() if k != "pair"}))

    # ── the transect rank test ────────────────────────────────────────────────────────────
    from scipy.stats import spearmanr
    obs = np.array([s[4] for s in SITES])
    la_, lo_, _, Cf, _ = fields["fine N=160 tempered"]
    mod_f = np.array([at(la_, lo_, Cf, s[2], s[3]) for s in SITES])
    la6, lo6, _, C6, _ = fields["production N=64 tempered"]
    mod_p = np.array([at(la6, lo6, C6, s[2], s[3]) for s in SITES])
    rho_f, p_f = spearmanr(obs, mod_f)
    rho_p, p_p = spearmanr(obs, mod_p)
    print(f"\n=== transect rank (n=12, 7 distinct obs -- heavy ties, weak by construction) ===")
    print(f"  production 238 m : rho {rho_p:+.3f} (p {p_p:.3f})")
    print(f"  fine       94 m  : rho {rho_f:+.3f} (p {p_f:.3f})")
    rows += [dict(kind="rank", label="production_238m", value=round(float(rho_p), 3)),
             dict(kind="rank", label="fine_94m", value=round(float(rho_f), 3))]

    # ── score the registered predictions ──────────────────────────────────────────────────
    res = dict(paired_min=min(ratios), paired_max=max(ratios),
               rho_fine=float(rho_f), p90p10_fine=spread(Cf))
    print("\n=== REGISTERED PREDICTIONS (osf.io/bkpyr) ===")
    for k, (text, fn) in PRED.items():
        ok = bool(fn(res))
        print(f"  {k}  {'HELD    ' if ok else 'REFUTED '}  {text}")
        rows.append(dict(kind="prediction", label=k, value=int(ok), note=text))

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
