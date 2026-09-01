"""R2 -- score `A_transport`, the layer that ships with no evidence at all.

Registered at https://osf.io/bkpyr/ (2026-09-01) BEFORE this ran.

WHY. `A_transport` is a whole layer of the production field, shipped as a "scenario" and never
scored. It is the most attackable thing in the paper. Two acceptable outcomes were registered:
score it, or state in the abstract that the headline field excludes it. Continuing to ship an
unscored layer without saying so is not among them.

THE COUNTERFACTUAL. The layer's entire job is to redistribute an emission surface through
terrain-steered advection and dispersion. So the honest no-transport control is that same
emission surface, undispersed. Both are scored the same way against the same held-out stations,
so the only thing that varies is whether transport was applied.

  rho_S   rank correlation of the raw emission surface against station means
  rho_C   rank correlation after the calibrated terrain solver  ( = A_transport applied )

Nothing is fitted here. Solver parameters are the cross-city calibrated values already in the
module. The stations are the same ones the panel has always been scored against.

⚠ This measures the layer's SPATIAL contribution under the stable-calm regime the solver was
calibrated for. It does not test the diurnal timing factor e(t), and it cannot: the panel
scoring is on station means.

Usage:  .venv/Scripts/python.exe scripts/r2_score_atransport.py
Out:    data/processed/modular/r2_atransport.csv
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
    CITIES, SLUG, FINAL_TEN, STABLE_WIND, STABLE_BLH, load_city, load_stations,
)
from src.stage1_satml.decomp.terrain_transport import solve_terrain  # noqa: E402

OUT = REPO / "data" / "processed" / "modular" / "r2_atransport.csv"
CEILING = 0.28          # the upper end of the measured spatial ceiling (F.56/F.58/F.59/F.61)


def rank_at_stations(lats, lons, F, stns, bbox) -> tuple:
    rgi = RegularGridInterpolator((lats, lons), F, bounds_error=False, fill_value=None)
    la = np.clip(stns["lat"].values, bbox[0], bbox[1])
    lo = np.clip(stns["lon"].values, bbox[2], bbox[3])
    pred, obs = rgi(np.stack([la, lo], 1)), stns["pm"].values
    ok = np.isfinite(pred) & np.isfinite(obs)
    if ok.sum() < 4 or np.std(pred[ok]) < 1e-9:
        return np.nan, int(ok.sum())
    return float(spearmanr(pred[ok], obs[ok])[0]), int(ok.sum())


def main() -> None:
    rows = []
    print("R2 -- does A_transport improve spatial rank against held-out stations?\n")
    print(f"  {'city':<12}{'n':>4}{'rho_S':>9}{'rho_C':>9}{'delta':>9}")
    print("  " + "-" * 43)

    for name in FINAL_TEN:
        try:
            fn, pm_col, id_col = CITIES[name]
            grids = load_city(SLUG[name])
            stns = load_stations(REPO / "data" / "processed" / "stage2" / fn, pm_col, id_col)
        except Exception as e:
            print(f"  {name:<12}  skipped: {str(e)[:44]}")
            rows.append(dict(city=name, n=0, rho_S=np.nan, rho_C=np.nan, note=str(e)[:60]))
            continue

        lats, lons, dz, S, dx, bbox = grids
        _, _, _, _, C = solve_terrain(STABLE_WIND, 0.0, STABLE_BLH, lats, lons, dz, S, dx)
        rS, n1 = rank_at_stations(lats, lons, S, stns, bbox)
        rC, n2 = rank_at_stations(lats, lons, C, stns, bbox)
        d = rC - rS
        print(f"  {name:<12}{n2:>4}{rS:>+9.3f}{rC:>+9.3f}{d:>+9.3f}")
        rows.append(dict(city=name, n=n2, rho_S=round(rS, 4), rho_C=round(rC, 4),
                         delta=round(d, 4)))

    df = pd.DataFrame(rows)
    ok = df.dropna(subset=["rho_S", "rho_C"])
    mS, mC = ok.rho_S.median(), ok.rho_C.median()
    md = ok.delta.median()
    wins = int((ok.delta > 0).sum())

    print("  " + "-" * 43)
    print(f"  {'median':<12}{len(ok):>4}{mS:>+9.3f}{mC:>+9.3f}{md:>+9.3f}")
    print(f"\n  A_transport improves rank in {wins} of {len(ok)} cities")
    try:
        st, p = wilcoxon(ok.rho_C, ok.rho_S)
        print(f"  Wilcoxon signed-rank on the paired deltas: p = {p:.3f}  (n={len(ok)})")
    except Exception:
        p = np.nan
        print("  Wilcoxon not computable")

    print("\n=== REGISTERED PREDICTIONS (osf.io/bkpyr) ===")
    r2a = md > 0
    print(f"  R2a  {'HELD    ' if r2a else 'REFUTED '}  including A_transport improves "
          f"held-out station rank correlation (median delta {md:+.3f})")
    # R2b registered as: any improvement is small -- below the 0.2-0.28 measured ceiling.
    # Scored both defensible readings, since the registered wording admits two.
    r2b_reach = mC <= CEILING
    r2b_delta = abs(md) <= CEILING
    print(f"  R2b  {'HELD    ' if (r2b_reach and r2b_delta) else 'REFUTED '}  the improvement is "
          f"small: achieved rho {mC:+.3f} <= {CEILING} is {r2b_reach}; "
          f"|delta| {abs(md):.3f} <= {CEILING} is {r2b_delta}")

    rows.append(dict(city="MEDIAN", n=len(ok), rho_S=round(mS, 4), rho_C=round(mC, 4),
                     delta=round(md, 4),
                     note=f"wins {wins}/{len(ok)}; wilcoxon p={p:.3f}; "
                          f"R2a={'held' if r2a else 'refuted'}; "
                          f"R2b={'held' if (r2b_reach and r2b_delta) else 'refuted'}"))
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
