"""
compare_xgb_ngb_v2.py — Apply pre-reg §5.5 model-selection criterion.

Per OSF pre-registration §5.5:
  "Both trained, both reported. Primary metric uses the better-calibrated
   variant on held-out months (chosen by pre-specified CRPS criterion, §5.5)."

This script loads the two summary tables produced by:
  - train_xgboost_v2.py  → summary_v2.csv          (quantile XGBoost)
  - train_ngboost_v2.py  → summary_ngboost.csv     (NGBoost Student-t)

And applies the pre-specified criterion:
  Primary model = the one with lower CRPS_mean on held-out months
  (ties broken by lower fold_rmse_mean; cov90 must be ∈ [0.85, 0.95])

Writes a consolidated comparison CSV and a short text rationale.

Usage:
  python -m src.stage1_satml.models.compare_xgb_ngb_v2
  python src/stage1_satml/models/compare_xgb_ngb_v2.py

Reference: pre-reg §5.1, §5.5.
"""

import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("compare_v2")

OUT_DIR = PROC_DIR / "stage1_v2" / "training"
XGB_SUMMARY = OUT_DIR / "summary_v2.csv"
NGB_SUMMARY = OUT_DIR / "summary_ngboost.csv"
OUT_COMP    = OUT_DIR / "model_comparison_v2.csv"
OUT_DECISION = OUT_DIR / "model_selection_decision_v2.txt"

# Pre-reg §5.5: cov90 acceptable range
COV90_MIN = 0.85
COV90_MAX = 0.95


def load_summary(path: Path, model_label: str) -> dict | None:
    if not path.exists():
        log.error(f"missing summary: {path}")
        return None
    s = pd.read_csv(path)
    row = s[s["model"] == model_label]
    if len(row) == 0:
        log.error(f"no '{model_label}' row in {path.name}")
        return None
    r = row.iloc[0].to_dict()
    r["source"] = path.name
    return r


def main():
    xgb = load_summary(XGB_SUMMARY, "xgboost_v2")
    ngb = load_summary(NGB_SUMMARY, "ngboost_v2")
    if xgb is None or ngb is None:
        log.error("aborting — both summaries required")
        return

    rows = []
    for label, r in [("xgboost_v2_quantile", xgb), ("ngboost_v2_tfixedf5", ngb)]:
        rows.append({
            "model":        label,
            "rmse_pooled":  r.get("rmse_pooled"),
            "r2_pooled":    r.get("r2_pooled"),
            "bias_pooled":  r.get("bias_pooled"),
            "rmse_mean":    r.get("rmse_mean"),
            "r2_mean":      r.get("r2_mean"),
            "cov90_mean":   r.get("cov90_mean"),
            "crps_mean":    r.get("crps_mean"),
            "pi_width_mean":r.get("pi_width_mean"),
            "n_folds":      r.get("n_folds"),
        })
    comp = pd.DataFrame(rows)
    comp.to_csv(OUT_COMP, index=False)
    log.info(f"wrote {OUT_COMP}")

    log.info("── consolidated comparison ──")
    log.info(comp.to_string(index=False))

    # ── Pre-reg §5.5 decision rule ──
    cov_ok_xgb = COV90_MIN <= xgb["cov90_mean"] <= COV90_MAX
    cov_ok_ngb = COV90_MIN <= ngb["cov90_mean"] <= COV90_MAX
    crps_lower = "xgb" if xgb["crps_mean"] < ngb["crps_mean"] else "ngb"
    rmse_lower = "xgb" if xgb["rmse_mean"] < ngb["rmse_mean"] else "ngb"

    if cov_ok_xgb and not cov_ok_ngb:
        winner = "xgboost_v2_quantile"
        reason = "NGBoost cov90 outside [0.85, 0.95] envelope; XGBoost in range."
    elif cov_ok_ngb and not cov_ok_xgb:
        winner = "ngboost_v2_tfixedf5"
        reason = "XGBoost cov90 outside [0.85, 0.95] envelope; NGBoost in range."
    else:
        # Both in (or both out of) range → use CRPS, tiebreak with RMSE
        if crps_lower == "xgb":
            winner = "xgboost_v2_quantile"
            reason = f"Both cov90 in-range; XGBoost CRPS lower ({xgb['crps_mean']:.3f} vs {ngb['crps_mean']:.3f})."
        else:
            winner = "ngboost_v2_tfixedf5"
            reason = f"Both cov90 in-range; NGBoost CRPS lower ({ngb['crps_mean']:.3f} vs {xgb['crps_mean']:.3f})."

    decision_text = (
        f"Pre-reg §5.5 model-selection decision\n"
        f"=====================================\n\n"
        f"XGBoost quantile: rmse_mean={xgb['rmse_mean']:.3f}  "
        f"cov90={xgb['cov90_mean']:.3f}  crps={xgb['crps_mean']:.3f}\n"
        f"NGBoost T(df=5):  rmse_mean={ngb['rmse_mean']:.3f}  "
        f"cov90={ngb['cov90_mean']:.3f}  crps={ngb['crps_mean']:.3f}\n\n"
        f"cov90 ∈ [{COV90_MIN}, {COV90_MAX}]?\n"
        f"  XGBoost: {'YES' if cov_ok_xgb else 'NO'}\n"
        f"  NGBoost: {'YES' if cov_ok_ngb else 'NO'}\n\n"
        f"Lower CRPS: {crps_lower.upper()}\n"
        f"Lower RMSE: {rmse_lower.upper()}\n\n"
        f"PRIMARY MODEL: {winner}\n"
        f"REASON: {reason}\n"
    )
    OUT_DECISION.write_text(decision_text, encoding="utf-8")
    log.info(f"wrote {OUT_DECISION}")
    log.info("── decision ──")
    for line in decision_text.split("\n"):
        log.info(f"  {line}")


if __name__ == "__main__":
    main()
