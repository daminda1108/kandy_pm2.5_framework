"""srep_external_check.py -- what identifies the representativeness error, other than the model?

THE OBJECTION, from an external reviewer, and the sharpest technical point in the review:

    "You are effectively asking the model to help estimate how wrong its own unresolved spatial
     representation is. If the model systematically underestimates sub-grid variability, the
     estimated s_rep could also be too small. What EXTERNAL information identifies s_rep, rather
     than merely making it internally consistent with the model?"

That is correct as stated. `observation.representativeness_sigma` takes the standard deviation of
the FIELD over the cells around a sensor and calls it the point-versus-area error. The field has no
sub-kilometre structure by construction, so this is a neighbourhood gradient standing in for a
within-cell spread. Nothing in the construction forces the stand-in to be the right size.

WHAT CAN IDENTIFY IT WITHOUT THE MODEL. Wherever two or more instruments fall inside a single model
cell, the spread between them measures the point-versus-area error DIRECTLY. No field is consulted,
no pattern is assumed, and the quantity is exactly the one s_rep is supposed to represent. The
panel contains such cells, and Kandy has its own from the 2004-06 transect.

Both are expressed as a coefficient of variation, so that a city's level divides out and the model
and the observations are compared on the same scale.

    observed    sd of station means inside one cell / that city's mean
    modelled    sd of the field over the sensor's cell neighbourhood / the field mean

WHAT THE ANSWER MEANS EITHER WAY. If the modelled figure matches the observed one, the stand-in is
the right size and the circularity is harmless in practice. If it is smaller, then s_rep is too
small by the measured ratio, the shipped intervals are too narrow at point locations by roughly
that factor, and the thesis must say so with a number rather than a caveat.

⚠ THREE LIMITS ON THE KANDY ARM, stated because they bound what it can carry. The transect is PM10
rather than PM2.5; it is roadside 3-hour sampling from 2004-06 rather than the model's period; and
four of its sites are CENSORED at an upper bound of 150, so their contribution to the spread is a
LOWER bound. Censoring can only make the observed spread look smaller than it is, so it biases the
comparison toward the model and cannot manufacture the conclusion.

Usage: .venv/Scripts/python.exe scripts/srep_external_check.py
Out:   data/processed/modular/srep_external_check.csv
       data/processed/modular/srep_external_check.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
warnings.filterwarnings("ignore")

from src.modular.observation import representativeness_sigma  # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
DEC = REPO / "data" / "processed" / "decomp"
OUT = MOD / "srep_external_check.csv"
OUT_JSON = MOD / "srep_external_check.json"

CELL_DEG = 0.009      # about 1 km of latitude, the model's reporting cell


def cells(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["ci"] = np.floor(d.lat / CELL_DEG).astype(int)
    d["cj"] = np.floor(d.lon / (CELL_DEG / np.cos(np.radians(d.lat)))).astype(int)
    return d


def main() -> None:
    print("=== what identifies s_rep, other than the model itself? ===\n")

    # ── [1] the panel: instruments sharing one model cell ────────────────────────────────
    d = pd.read_csv(MOD / "lur_predictors.csv").dropna(subset=["lat", "lon", "pm"])
    d = cells(d)
    rows = []
    for (city, ci, cj), g in d.groupby(["city", "ci", "cj"]):
        if len(g) < 2:
            continue
        city_mean = float(d[d.city == city].pm.mean())
        if city_mean <= 0:
            continue
        rows.append(dict(source="panel", city=str(city), n_stations=len(g),
                         cell_sd=float(g.pm.std(ddof=1)), city_mean=city_mean,
                         cv_within=float(g.pm.std(ddof=1) / city_mean),
                         spread_ratio=float(g.pm.max() / max(g.pm.min(), 1e-6))))
    P = pd.DataFrame(rows)
    print(f"[1] panel: {len(P)} model cells hold two or more instruments, "
          f"{int(P.n_stations.sum())} stations across {P.city.nunique()} cities")
    print(f"    observed within-cell CV, median {P.cv_within.median():.3f} "
          f"(IQR {P.cv_within.quantile(.25):.3f}-{P.cv_within.quantile(.75):.3f})")
    print(f"    observed within-cell max/min ratio, median {P.spread_ratio.median():.2f}")

    # ── [2] Kandy's own transect ─────────────────────────────────────────────────────────
    e = pd.read_csv(DEC / "elangasinghe_spatial_test.csv")
    e = e[e.inside].copy()
    e["px"] = e.px.astype(str)
    krows = []
    for px, g in e.groupby("px"):
        if len(g) < 2:
            continue
        krows.append(dict(source="kandy_transect", cell=px, n_stations=len(g),
                          n_censored=int(g.cens.sum()),
                          cell_sd=float(g.obs.std(ddof=1)),
                          cell_mean=float(g.obs.mean()),
                          cv_within=float(g.obs.std(ddof=1) / g.obs.mean()),
                          spread_ratio=float(g.obs.max() / max(g.obs.min(), 1e-6))))
    K = pd.DataFrame(krows)
    print(f"\n[2] Kandy transect: {len(K)} model cells hold two or more sites, "
          f"{int(K.n_stations.sum())} sites, {int(K.n_censored.sum())} censored")
    print(f"    observed within-cell CV, median {K.cv_within.median():.3f}  "
          f"[!] censored sites make this a LOWER bound")

    # ── [3] what the model's own estimator returns at those Kandy locations ──────────────
    fld = sorted(DEC.glob("kandy_decomp_predictions_*_additive_v3.parquet"))
    model_cv = np.nan
    mrows = []
    if fld:
        f = pd.read_parquet(fld[-1], columns=["lat", "lon", "pm25_q50"])
        grid = f.groupby(["lat", "lon"]).pm25_q50.mean().reset_index()
        lats = np.sort(grid.lat.unique())
        lons = np.sort(grid.lon.unique())
        field = (grid.pivot(index="lat", columns="lon", values="pm25_q50")
                 .reindex(index=lats, columns=lons).to_numpy())
        fmean = float(np.nanmean(field))
        for _, s in e.iterrows():
            sr = representativeness_sigma(field, lats, lons, float(s.lat), float(s.lon))
            mrows.append(dict(source="model", name=s["name"], s_rep=sr,
                              cv_model=sr / fmean))
        M = pd.DataFrame(mrows)
        model_cv = float(M.cv_model.median())
        print(f"\n[3] the model's own estimator at those same locations "
              f"({fld[-1].name.split('_')[3]})")
        print(f"    field mean {fmean:.2f}, median s_rep {M.s_rep.median():.3f} ug/m3, "
              f"CV {model_cv:.3f}")
    else:
        M = pd.DataFrame()
        print("\n[3] no Kandy field on disk; the model arm is skipped")

    # ── [4] the comparison ───────────────────────────────────────────────────────────────
    print("\n=== the comparison ===")
    print(f"    {'source':<26}{'within-cell CV':>16}{'x the model':>14}")
    out = {}
    for label, cv, note in (("panel instruments", float(P.cv_within.median()), "reference-heavy"),
                            ("Kandy transect", float(K.cv_within.median()), "lower bound")):
        ratio = cv / model_cv if np.isfinite(model_cv) and model_cv > 0 else np.nan
        print(f"    {label:<26}{cv:>16.3f}{ratio:>14.1f}   ({note})")
        out[label] = dict(cv=round(cv, 4), ratio_to_model=round(float(ratio), 2))
    if np.isfinite(model_cv):
        print(f"    {'model s_rep proxy':<26}{model_cv:>16.3f}{1.0:>14.1f}")

    print("\n=== the answer ===")
    r_panel = out["panel instruments"]["ratio_to_model"]
    r_kandy = out["Kandy transect"]["ratio_to_model"]
    if max(r_panel, r_kandy) > 1.5:
        print(f"    The model's representativeness error is TOO SMALL. Instruments sharing a")
        print(f"    single model cell disagree {r_panel:.1f} times more than the field's own")
        print(f"    neighbourhood gradient implies on the panel, and {r_kandy:.1f} times more at")
        print(f"    Kandy, where censoring makes that a lower bound. s_rep is therefore not")
        print(f"    merely internally consistent, it is externally identified and externally")
        print(f"    REFUTED at its current magnitude. A point-level interval built from it is")
        print(f"    too narrow, and the honest statement is that the interval is calibrated for")
        print(f"    an AREAL quantity and understates point-level uncertainty by roughly this")
        print(f"    factor.")
    else:
        print(f"    The stand-in is the right size: observed within-cell spread is "
              f"{r_panel:.1f}x the modelled figure on the panel and {r_kandy:.1f}x at Kandy.")
        print(f"    The circularity is real in construction but small in consequence.")

    allrows = pd.concat([P, K, M], ignore_index=True)
    allrows.to_csv(OUT, index=False)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(dict(cell_deg=CELL_DEG,
                       panel_cells=int(len(P)), panel_stations=int(P.n_stations.sum()),
                       panel_cities=int(P.city.nunique()),
                       panel_cv=round(float(P.cv_within.median()), 4),
                       panel_spread_ratio=round(float(P.spread_ratio.median()), 2),
                       kandy_cells=int(len(K)), kandy_sites=int(K.n_stations.sum()),
                       kandy_censored=int(K.n_censored.sum()),
                       kandy_cv=round(float(K.cv_within.median()), 4),
                       model_cv=None if not np.isfinite(model_cv) else round(model_cv, 4),
                       ratio_panel=r_panel, ratio_kandy=r_kandy,
                       comparison=out), fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
