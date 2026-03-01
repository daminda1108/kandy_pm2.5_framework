"""
generate_validation_report.py — Generate Stage 1 validation summary.

Produces a structured report documenting all validation sources,
methodologies, and known limitations for the manuscript Methods section.

Usage:
    python generate_validation_report.py
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import VALIDATION_DIR, TABLES_DIR, LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("validation_report")


def generate_report() -> dict:
    """
    Generate and print the Stage 1 validation summary.
    Also saves as JSON for downstream consumption.
    """
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "generated": datetime.now().isoformat(),
        "training_labels": {
            "source": "CAMS EAC4 reanalysis (primary) + MERRA-2 (secondary)",
            "coverage": "2003-2022 (EAC4) + 2000-2025 (MERRA-2)",
            "resolution": "0.75° (~83km) for EAC4, 0.5° (~55km) for MERRA-2",
            "validation_of_labels": (
                "CAMS validated globally against AERONET; "
                "known to underestimate valley trapping effects"
            ),
        },
        "internal_validation": {
            "method": "Leave-One-Month-Out CV (LOMO)",
            "metric": "R² and RMSE against held-out CAMS labels",
            "note": (
                "Measures CAMS pattern reproduction, not real PM2.5 accuracy. "
                "R² here = 'CAMS reproduction score', not 'PM2.5 accuracy score'."
            ),
        },
        "external_validation": {
            "method": "Annual mean comparison vs van Donkelaar V5.GL.04",
            "coverage": "2000-2022 at 1km resolution",
            "what_it_tests": "PM2.5 magnitude and spatial pattern plausibility",
        },
        "multi_source_agreement": {
            "method": "CAMS-MERRA2 daily agreement",
            "purpose": "Label confidence — high agreement = reliable training day",
            "metric": "Daily absolute difference (μg/m³)",
        },
        "physical_consistency": {
            "checks": [
                "Valley-bottom PM2.5 > ridge PM2.5 on stagnant days",
                "Dry-season mean > wet-season mean",
                "PM2.5 inversely correlated with BLH",
                "No negative predictions",
                "Reasonable range [5-200 μg/m³]",
                "No temporal discontinuities (day-to-day < 60 μg/m³)",
            ],
        },
        "known_limitations": [
            "No ground sensor measurements in Kandy — critical validation gap",
            "Topographic amplification magnitude unverified without sensors",
            "CAMS-MODIS AOD partial information sharing in EAC4 assimilation",
            "Valley-specific PM2.5 peaks may be systematically underestimated",
            "TROPOMI features unavailable pre-2018 (hardware constraint)",
        ],
        "future_validation": (
            "Dr. Bowatte collaboration and/or low-cost sensor deployment. "
            "Real measurement validation pending."
        ),
    }

    # ── Try to load existing results ──────────────────────────────────────
    # LOMO CV results
    lomo_path = TABLES_DIR / "cv_results_lomo.csv"
    if lomo_path.exists():
        lomo = pd.read_csv(lomo_path)
        report["internal_validation"]["lomo_results"] = {
            "mean_r2": round(lomo["r2"].mean(), 3),
            "std_r2": round(lomo["r2"].std(), 3),
            "mean_rmse": round(lomo["rmse"].mean(), 2),
            "months_evaluated": int(len(lomo)),
        }
        log.info(f"  LOMO results loaded: R²={lomo['r2'].mean():.3f}")

    # Van Donkelaar comparison
    vd_path = VALIDATION_DIR / "van_donkelaar_comparison.csv"
    if vd_path.exists():
        vd = pd.read_csv(vd_path)
        report["external_validation"]["results"] = {
            "mean_bias": round(vd["bias"].mean(), 2),
            "years_compared": int(len(vd)),
        }
        log.info(f"  VD comparison loaded: bias={vd['bias'].mean():+.1f}")

    # CAMS-MERRA2 comparison
    cm_path = Path("data/raw/cams/cams_merra2_comparison.csv")
    if cm_path.exists():
        cm = pd.read_csv(cm_path)
        report["multi_source_agreement"]["results"] = {
            "overlap_days": int(len(cm)),
            "correlation": round(cm.iloc[:, 1].corr(cm.iloc[:, 2]), 3),
        }

    # ── Print report ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  STAGE 1 VALIDATION STATUS")
    print("=" * 60)

    for section, content in report.items():
        if section == "generated":
            continue
        print(f"\n[{section.upper()}]")
        if isinstance(content, dict):
            for k, v in content.items():
                if isinstance(v, list):
                    print(f"  {k}:")
                    for item in v:
                        print(f"    - {item}")
                elif isinstance(v, dict):
                    print(f"  {k}:")
                    for kk, vv in v.items():
                        print(f"    {kk}: {vv}")
                else:
                    print(f"  {k}: {v}")
        elif isinstance(content, list):
            for item in content:
                print(f"  - {item}")
        else:
            print(f"  {content}")

    print("\n" + "=" * 60)

    # ── Save ──────────────────────────────────────────────────────────────
    report_path = VALIDATION_DIR / "stage1_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    log.info(f"Report saved → {report_path}")

    return report


if __name__ == "__main__":
    generate_report()
