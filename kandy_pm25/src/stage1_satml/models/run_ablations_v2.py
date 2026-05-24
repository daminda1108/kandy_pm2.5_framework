"""
run_ablations_v2.py — Pre-reg §6 ablation sweeps for Stage 1 v2 XGBoost.

Wraps `train_xgboost_v2.run_pipeline` with different feature subsets and
emits a single consolidated comparison table.

Pre-reg coverage:
  §6.4 Feature ablation by mechanistic group (drop one group at a time)
  §6.5 Reanalysis ablation (no-CAMS, no-GEOS, neither, both)

Outputs (under data/processed/stage1_v2/training/):
  summary_v2_<suffix>.csv      — one per ablation (re-uses train_xgboost_v2 schema)
  ablation_comparison_v2.csv   — consolidated long-form table for the paper

Usage:
  python -m src.stage1_satml.models.run_ablations_v2
  python src/stage1_satml/models/run_ablations_v2.py
  python src/stage1_satml/models/run_ablations_v2.py --include reanalysis
  python src/stage1_satml/models/run_ablations_v2.py --include groups
  python src/stage1_satml/models/run_ablations_v2.py --smoke

Reference: pre-reg §6.4, §6.5.
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, LOG_FORMAT, LOG_DATEFMT
from src.stage1_satml.models.train_xgboost_v2 import (
    run_pipeline, select_features, FEATURE_GROUPS,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("run_ablations_v2")

OUT_DIR = PROC_DIR / "stage1_v2" / "training"
OUT_COMPARISON = OUT_DIR / "ablation_comparison_v2.csv"

# ─────────────────────────────────────────────────────────────────────────────
# Ablation catalog
# ─────────────────────────────────────────────────────────────────────────────

GROUP_NAMES = {
    "A": "ventilation", "B": "valley_transport", "C": "wet_scavenging",
    "D": "source_column", "E": "reanalysis_priors", "F": "climate_modes",
    "G": "temporal",
}

REANALYSIS_ABLATIONS: list[tuple[str, str, list[str] | None, list[str] | None]] = [
    # (suffix, label, drop_groups, drop_features)
    ("",                       "v2.1_full_features",  None,    None),
    ("_no_cams",               "no_cams_only",        None,    ["cams_pm25_raw", "prior_disagreement"]),
    ("_no_geos",               "no_geos_only",        None,    ["geos_cf_pm25_raw", "prior_disagreement"]),
    ("_no_reanalysis",         "no_reanalysis",       ["E"],   None),
    ("_no_prior_disagreement", "no_prior_disagree",   None,    ["prior_disagreement"]),
]

GROUP_ABLATIONS: list[tuple[str, str, list[str] | None, list[str] | None]] = [
    ("_drop_A_vent",     "drop_A_ventilation",      ["A"], None),
    ("_drop_B_valley",   "drop_B_valley_transport", ["B"], None),
    ("_drop_C_wet",      "drop_C_wet_scavenging",   ["C"], None),
    ("_drop_D_source",   "drop_D_source_column",    ["D"], None),
    ("_drop_F_climate",  "drop_F_climate_modes",    ["F"], None),
    ("_drop_G_temporal", "drop_G_temporal",         ["G"], None),
    # A drop-station ablation, also informative:
    ("_drop_STATION",    "drop_station_latlonelev", ["STATION"], None),
]


def all_ablations(include: str = "all") -> list[tuple[str, str, list[str] | None, list[str] | None]]:
    if include == "reanalysis":
        return REANALYSIS_ABLATIONS
    if include == "groups":
        return GROUP_ABLATIONS
    # Default: reanalysis first (deduped on "" full run), then groups
    return REANALYSIS_ABLATIONS + GROUP_ABLATIONS


# ─────────────────────────────────────────────────────────────────────────────
# Run one ablation
# ─────────────────────────────────────────────────────────────────────────────

def one_ablation(suffix: str, label: str, drop_groups: list[str] | None,
                 drop_features: list[str] | None, smoke: bool, force: bool) -> dict:
    feats = select_features(drop_groups=drop_groups, drop_features=drop_features)
    log.info(f"── ablation '{label}'  suffix='{suffix}'  n_features={len(feats)} ──")
    t0 = time.time()
    summary = run_pipeline(feature_cols=feats, suffix=suffix, smoke=smoke,
                           force=force, quiet=True)
    elapsed = time.time() - t0

    # Pull xgboost_v2 row from the summary
    xgb_row = summary[summary["model"] == "xgboost_v2"]
    if len(xgb_row) == 0:
        log.warning(f"  no xgboost_v2 row in summary for {label}")
        return {"label": label, "n_features": len(feats), "elapsed_s": elapsed}

    r = xgb_row.iloc[0]
    out = {
        "label":             label,
        "suffix":            suffix or "_full",
        "n_features":        len(feats),
        "drop_groups":       ",".join(drop_groups) if drop_groups else "",
        "drop_features":     ",".join(drop_features) if drop_features else "",
        "xgb_pooled_rmse":   r.get("rmse_pooled"),
        "xgb_pooled_r2":     r.get("r2_pooled"),
        "xgb_pooled_bias":   r.get("bias_pooled"),
        "xgb_fold_rmse":     r.get("rmse_mean"),
        "xgb_fold_r2":       r.get("r2_mean"),
        "xgb_cov90":         r.get("cov90_mean"),
        "xgb_pi_width":      r.get("pi_width_mean"),
        "n_pooled":          r.get("n_pooled"),
        "n_folds":           r.get("n_folds"),
        "elapsed_s":         elapsed,
    }
    log.info(f"  '{label}': pooled_rmse={out['xgb_pooled_rmse']:.2f}  "
             f"pooled_r2={out['xgb_pooled_r2']:+.3f}  cov90={out['xgb_cov90']:.2f}  "
             f"n_feat={len(feats)}  wall={elapsed:.0f}s")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include", choices=["all", "reanalysis", "groups"], default="all",
                    help="which ablation set to run (default: all)")
    ap.add_argument("--smoke", action="store_true",
                    help="3-fold smoke for each ablation (~5 min total)")
    ap.add_argument("--force", action="store_true", default=True,
                    help="overwrite outputs (default true; pass --no-force to skip)")
    ap.add_argument("--no-force", dest="force", action="store_false")
    args = ap.parse_args()

    plan = all_ablations(args.include)
    log.info(f"running {len(plan)} ablations  include={args.include}  smoke={args.smoke}")

    rows: list[dict] = []
    t0 = time.time()
    for suffix, label, drop_groups, drop_features in plan:
        try:
            row = one_ablation(suffix, label, drop_groups, drop_features,
                               smoke=args.smoke, force=args.force)
            rows.append(row)
        except Exception as e:
            log.error(f"  ablation '{label}' FAILED: {type(e).__name__}: {e}")
            rows.append({"label": label, "suffix": suffix, "ERROR": str(e)})

    log.info(f"all ablations done in {time.time()-t0:.0f}s")

    comp = pd.DataFrame(rows).sort_values("xgb_pooled_rmse", na_position="last")
    comp.to_csv(OUT_COMPARISON, index=False)
    log.info(f"wrote {OUT_COMPARISON}  ({len(comp)} rows)")

    # ── pretty print ──
    log.info("\n── ablation comparison (sorted by xgb pooled RMSE) ──")
    log.info(f"  {'label':<30}  {'n_feat':>6}  {'rmse':>6}  {'r2':>6}  {'bias':>6}  {'cov90':>6}")
    for _, r in comp.iterrows():
        if "ERROR" in r and not pd.isna(r.get("ERROR", float("nan"))):
            log.info(f"  {r['label']:<30}  ERROR: {r['ERROR']}")
            continue
        log.info(f"  {r['label']:<30}  {int(r['n_features']):>6}  "
                 f"{r['xgb_pooled_rmse']:>6.2f}  {r['xgb_pooled_r2']:>+6.3f}  "
                 f"{r['xgb_pooled_bias']:>+6.2f}  {r['xgb_cov90']:>6.2f}")

    # ── Δ vs full ──
    full = comp[comp["label"] == "v2.1_full_features"]
    if len(full):
        full_rmse = float(full.iloc[0]["xgb_pooled_rmse"])
        log.info(f"\n── Δ RMSE vs full v2.1 (baseline {full_rmse:.2f}) ──")
        for _, r in comp.iterrows():
            if r["label"] == "v2.1_full_features":
                continue
            if pd.isna(r.get("xgb_pooled_rmse", float("nan"))):
                continue
            d = r["xgb_pooled_rmse"] - full_rmse
            pct = 100 * d / full_rmse
            log.info(f"  {r['label']:<30}  ΔRMSE = {d:+.2f}  ({pct:+.1f}%)")


if __name__ == "__main__":
    main()
