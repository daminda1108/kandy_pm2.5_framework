"""PHASE 0 — does a sector-weighted emission surface place the increment better?

Plan: docs/learned_pattern_plan_2026-09-04.md §3. This must produce a number BEFORE any work
starts on a learned spatial pattern, because otherwise that work would be benchmarked against a
traffic-and-nightlights proxy in cities that mostly burn biomass, and beating it would mean
nothing.

THE DEFECT UNDER TEST. `city_config.CITIES[slug]["emix"]` declares a per-city source mix and it
feeds ONLY the diurnal timing profile. The SPATIAL surface is the same proxy everywhere. So
Kathmandu asserts 50 per cent kiln and biomass burning in TIME and receives 100 per cent roads
in SPACE; Xichang asserts 70 per cent domestic heating and receives roads. `src/modular/
emission.py` composes a sector-weighted surface from the declared mix and has never been scored.

THE ARMS. All scored identically, against the same held-out station means, on one grid per city.
Nothing is fitted.

  ntl        VIIRS night lights            -- what calibrate_terrain_solver actually uses, and
                                              therefore what the recorded 0.371 refers to
  traffic    road centrality x COPERT EF   -- the PRODUCTION spatial proxy
  sector     emission.compose(emix)        -- the arm under test
  ntl_disp   night lights + terrain solver -- the shipped A_transport construction
  sector_disp sector surface + solver      -- does dispersion still cost rank on a better source

⚠ WHAT THIS CANNOT SETTLE. The weights are declared, not fitted, and cannot be fitted below
Bud4. A sector whose proxy is missing has its weight redistributed, and that is recorded per
city rather than averaged away -- Kathmandu's kilns are continuous combustion and return no
fire detections at all, so its burn sector falls back to a flagged placeholder.

Usage: .venv/Scripts/python.exe scripts/phase0_sector_surface.py
Out:   data/processed/modular/phase0_sector_surface.csv
       data/processed/paper_figures/phase0_sector.json
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
from scipy.stats import spearmanr, wilcoxon

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from calibrate_terrain_solver import (  # noqa: E402
    CITIES as PERSTATION, SLUG, STABLE_WIND, STABLE_BLH, load_city, load_stations,
)
from city_config import CITIES as CFG                                        # noqa: E402
from src.modular.emission import compose, ProxyError                         # noqa: E402
from src.stage1_satml.decomp.terrain_transport import solve_terrain          # noqa: E402
from figdata import emit                                                     # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "data" / "processed" / "modular" / "phase0_sector_surface.csv"

# Every city with station data, a declared source mix, and the proxy surfaces. This is a WIDER
# frame than FINAL_TEN, deliberately: FINAL_TEN was selected on terrain learnability, which is
# a property of the SOLVER and irrelevant to whether an emission surface is well specified.
# Excluding Medellin and Chiang Mai here would drop two of the three cities whose declared mix
# is least traffic-like, which is the question.
FRAME = ["Xichang", "Bazhou", "Baoji", "Taian", "Yichang", "Chandigarh",
         "Kathmandu", "Medellin", "ChiangMai"]


def _on_grid(path: Path, key: str, lats, lons):
    z = np.load(path)
    a = np.asarray(z[key], dtype=float)
    la, lo = np.asarray(z["lats"], float), np.asarray(z["lons"], float)
    if la[0] > la[-1]:
        la, a = la[::-1], a[::-1, :]
    if lo[0] > lo[-1]:
        lo, a = lo[::-1], a[:, ::-1]
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    g = RegularGridInterpolator((la, lo), a, bounds_error=False,
                                fill_value=0.0)(np.stack([LA.ravel(), LO.ravel()], 1))
    return np.clip(g.reshape(len(lats), len(lons)), 0, None)


def rank_at_stations(lats, lons, F, stns, bbox):
    rgi = RegularGridInterpolator((lats, lons), F, bounds_error=False, fill_value=None)
    la = np.clip(stns["lat"].values, bbox[0], bbox[1])
    lo = np.clip(stns["lon"].values, bbox[2], bbox[3])
    pred, obs = rgi(np.stack([la, lo], 1)), stns["pm"].values
    ok = np.isfinite(pred) & np.isfinite(obs)
    if ok.sum() < 4 or np.std(pred[ok]) < 1e-9:
        return np.nan, int(ok.sum())
    return float(spearmanr(pred[ok], obs[ok])[0]), int(ok.sum())


def common_support(stns, footprints):
    """Stations lying inside EVERY proxy's own footprint.

    🔴 WITHOUT THIS THE COMPARISON IS INVALID. The night-lights surface is built over the
    station footprint by `load_city`; the traffic surface is built over the narrower modelling
    box. Interpolating the traffic surface at a station outside its box returns the
    `fill_value` of 0, so an arm gets scored partly on padding rather than on its surface --
    at Chiang Mai that was 21 of 33 stations, at Medellin 7 of 24. This is the same failure as
    gotcha #43, where road density read 0 for every station outside the modelling grid.

    Restricting every arm to the intersection costs sample size and is the only way the arms
    are answering the same question.
    """
    m = np.ones(len(stns), dtype=bool)
    for la, lo in footprints:
        m &= ((stns.lat.values >= la.min()) & (stns.lat.values <= la.max())
              & (stns.lon.values >= lo.min()) & (stns.lon.values <= lo.max()))
    return m


def main() -> int:
    print("PHASE 0 -- sector-weighted emission surface against held-out stations\n")
    print(f"  {'city':<11}{'n':>3}{'ntl':>8}{'traffic':>9}{'sector':>8}"
          f"{'ntl_dsp':>9}{'sec_dsp':>9}   provenance")
    print("  " + "-" * 84)

    rows = []
    for name in FRAME:
        slug = SLUG.get(name)
        cfg = CFG.get(slug, {})
        emix = cfg.get("emix")
        if not emix:
            print(f"  {name:<11}  no emix declared -- skipped")
            continue
        try:
            fn, pm_col, id_col = PERSTATION[name]
            lats, lons, dz, S_ntl, dx, bbox = load_city(slug)
            stns = load_stations(REPO / "data" / "processed" / "stage2" / fn, pm_col, id_col)
        except Exception as e:                                              # noqa: BLE001
            print(f"  {name:<11}  skipped: {str(e)[:52]}")
            continue

        grids, foot = {"ntl": S_ntl}, []
        for key, fname, arr in (("traffic", f"S_traffic_{slug}.npz", "S_traffic"),
                                ("population", f"population_{slug}.npz", "pop"),
                                ("fire", f"fire_{slug}.npz", "fire")):
            p = DEC / fname
            if p.exists():
                z = np.load(p)
                foot.append((np.asarray(z["lats"], float), np.asarray(z["lons"], float)))
                g = _on_grid(p, arr, lats, lons)
                # A proxy that is identically zero is ABSENT, not flat. Kathmandu's fire grid is
                # all zeros because brick kilns are continuous combustion and FIRMS sees none;
                # passing it through would silently weight a sector by nothing.
                if np.nanmax(g) > 0:
                    grids[key] = g
        if "traffic" not in grids:
            print(f"  {name:<11}  no traffic surface -- skipped")
            continue

        # every arm scored on the SAME stations: those inside every proxy's own footprint
        keep = common_support(stns, foot)
        n_all = len(stns)
        stns = stns[keep].reset_index(drop=True)
        if len(stns) < 5:
            print(f"  {name:<11}  only {len(stns)} of {n_all} stations on common support"
                  f" -- skipped")
            continue

        try:
            surf = compose(grids, emix)
        except ProxyError as e:                                             # noqa: BLE001
            print(f"  {name:<11}  compose failed: {str(e)[:48]}")
            continue

        _, _, _, _, C_ntl = solve_terrain(STABLE_WIND, 0.0, STABLE_BLH, lats, lons, dz,
                                          S_ntl, dx)
        _, _, _, _, C_sec = solve_terrain(STABLE_WIND, 0.0, STABLE_BLH, lats, lons, dz,
                                          surf.S / surf.S.max(), dx)

        r = {}
        r["ntl"], n = rank_at_stations(lats, lons, S_ntl, stns, bbox)
        r["traffic"], _ = rank_at_stations(lats, lons, grids["traffic"], stns, bbox)
        r["sector"], _ = rank_at_stations(lats, lons, surf.S, stns, bbox)
        r["ntl_disp"], _ = rank_at_stations(lats, lons, C_ntl, stns, bbox)
        r["sector_disp"], _ = rank_at_stations(lats, lons, C_sec, stns, bbox)

        prov = "; ".join(surf.provenance)
        short = ("PLACEHOLDER burn" if surf.is_placeholder_dependent else "observed")
        if surf.dropped:
            short += f"; dropped {sorted(surf.dropped)}"
        print(f"  {name:<11}{n:>3}{r['ntl']:>+8.3f}{r['traffic']:>+9.3f}{r['sector']:>+8.3f}"
              f"{r['ntl_disp']:>+9.3f}{r['sector_disp']:>+9.3f}   {short}")
        rows.append(dict(city=name, n=n, n_all=n_all, **{k: round(v, 4) for k, v in r.items()},
                         vehic=emix.get("vehic", 0.0), heat=emix.get("heat", 0.0),
                         burn=emix.get("burn", 0.0),
                         weights_used=str({k: round(v, 3) for k, v in surf.weights_used.items()}),
                         placeholder=bool(surf.is_placeholder_dependent),
                         dropped=";".join(sorted(surf.dropped)), provenance=prov))

    d = pd.DataFrame(rows)
    if d.empty:
        print("\n  nothing scored")
        return 1
    ok = d.dropna(subset=["ntl", "traffic", "sector"])
    med = {k: float(ok[k].median()) for k in
           ("ntl", "traffic", "sector", "ntl_disp", "sector_disp")}

    print("  " + "-" * 84)
    print(f"  {'median':<11}{len(ok):>3}{med['ntl']:>+8.3f}{med['traffic']:>+9.3f}"
          f"{med['sector']:>+8.3f}{med['ntl_disp']:>+9.3f}{med['sector_disp']:>+9.3f}")

    print("\n  paired comparisons (Wilcoxon signed-rank, n = %d)" % len(ok))
    tests = {}
    for a, b in (("sector", "traffic"), ("sector", "ntl"), ("ntl_disp", "ntl"),
                 ("sector_disp", "sector")):
        delta = float((ok[a] - ok[b]).median())
        wins = int((ok[a] > ok[b]).sum())
        try:
            p = float(wilcoxon(ok[a], ok[b])[1])
        except Exception:                                                   # noqa: BLE001
            p = float("nan")
        tests[f"{a}_vs_{b}"] = dict(delta=round(delta, 4), wins=wins, p=round(p, 4))
        print(f"    {a:<12} vs {b:<8} median delta {delta:+.3f}   "
              f"better in {wins}/{len(ok)}   p = {p:.3f}")

    # The placeholder stratum is reported separately, never pooled away: a city whose burn
    # sector fell back to the fringe proxy is not evidence about observed fire data.
    obs_only = ok[~ok.placeholder]
    if len(obs_only) >= 3:
        print(f"\n  excluding cities on the PLACEHOLDER burn proxy (n = {len(obs_only)}): "
              f"sector {obs_only.sector.median():+.3f} vs traffic "
              f"{obs_only.traffic.median():+.3f}")

    # ── what this test could have detected ────────────────────────────────────────────────
    # F.92's lesson, applied to our own result: a null without a detection limit converts a
    # limit of the experiment into a property of the world. Computed here rather than typed in
    # afterwards, so re-running the script regenerates it.
    delta = (ok.sector - ok.traffic).values
    sd, n = float(np.std(delta, ddof=1)), len(delta)
    rng = np.random.default_rng(0)
    mde = float("nan")
    for eff in np.arange(0.05, 1.51, 0.05):
        hits = 0
        for _ in range(4000):
            x = rng.normal(eff, sd, n)
            try:
                if wilcoxon(x)[1] < 0.05 and np.median(x) > 0:
                    hits += 1
            except Exception:                                               # noqa: BLE001
                pass
        if hits / 4000 >= 0.80:
            mde = round(float(eff), 2)
            break
    print(f"\n  POWER: with n = {n} cities and a between-city delta sd of {sd:.3f}, the "
          f"smallest\n  improvement this test could have found at 80 per cent power is "
          f"delta rho = {mde:.2f}.")
    print("  That is larger than the total rank correlation of most cities in the frame, so a\n"
          "  null here excludes a transformative gain and says nothing about a moderate one.")

    d.to_csv(OUT, index=False)
    print(f"\n  wrote {OUT.relative_to(REPO)}")

    emit("phase0_sector",
         cities=int(len(ok)),
         rho_ntl=round(med["ntl"], 3),
         rho_traffic=round(med["traffic"], 3),
         rho_sector=round(med["sector"], 3),
         rho_ntl_dispersed=round(med["ntl_disp"], 3),
         rho_sector_dispersed=round(med["sector_disp"], 3),
         sector_vs_traffic_delta=tests["sector_vs_traffic"]["delta"],
         sector_vs_traffic_wins=tests["sector_vs_traffic"]["wins"],
         sector_vs_traffic_p=tests["sector_vs_traffic"]["p"],
         dispersion_cost_delta=tests["ntl_disp_vs_ntl"]["delta"],
         dispersion_cost_wins=tests["ntl_disp_vs_ntl"]["wins"],
         min_detectable_delta=mde,
         delta_sd=round(sd, 3),
         placeholder_cities=int(ok.placeholder.sum()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
