"""
run_pipeline.py — Master pipeline runner for the Kandy PM2.5 Stage 1 project.

Run each step in order, or use flags to run individual stages.
Designed to be the single entry point you run during development.

Usage:
    python run_pipeline.py --all              # Run everything end-to-end
    python run_pipeline.py --step gee         # Submit GEE export jobs
    python run_pipeline.py --step data        # Download data (non-GEE)
    python run_pipeline.py --step features    # Build feature dataset
    python run_pipeline.py --step model       # Train XGBoost
    python run_pipeline.py --step validate    # Validate & generate figures
    python run_pipeline.py --step sanity      # Quick sanity check (no downloads needed)
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import LOG_FORMAT, LOG_DATEFMT, MERGED_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("pipeline")

SRC = Path(__file__).parent / "src" / "stage1_satml"


def run(script: Path, extra_args: list[str] | None = None) -> None:
    """Run a Python script as a subprocess."""
    cmd = [sys.executable, str(script)] + (extra_args or [])
    log.info(f"▶ Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        log.error(f"Script failed with exit code {result.returncode}: {script.name}")
        sys.exit(result.returncode)


def step_gee() -> None:
    """Submit GEE export jobs (primary data acquisition path)."""
    log.info("═══ STEP 0: GEE DATA EXPORTS ═══")
    log.info("Submitting GEE export tasks (DEM, ERA5 CSV, MODIS, TROPOMI) …")
    run(SRC / "data" / "download_gee.py", ["--product", "all"])
    log.info("✅ GEE export jobs submitted. Check Google Drive for results.")


def step_data() -> None:
    """Download all required data (non-GEE fallback path)."""
    log.info("═══ STEP 1: DATA ACQUISITION ═══")
    log.info("Downloading SRTM DEM …")
    run(SRC / "data" / "download_dem.py")

    log.info("Downloading ERA5 reanalysis …")
    run(SRC / "data" / "download_era5.py")

    log.info("Downloading MODIS MAIAC AOD …")
    run(SRC / "data" / "download_modis.py")

    log.info("Downloading TROPOMI products …")
    run(SRC / "data" / "download_tropomi.py")

    log.info("✅ Data acquisition complete.")


def step_features() -> None:
    """Build integrated feature dataset."""
    log.info("═══ STEP 2: FEATURE ENGINEERING ═══")
    run(SRC / "features" / "build_dataset.py")
    log.info("✅ Feature dataset ready.")


def step_model(tune: bool = False, no_shap: bool = False) -> None:
    """Train XGBoost model."""
    log.info("═══ STEP 3: MODEL TRAINING ═══")
    extra = []
    if tune:
        extra.append("--tune")
    if no_shap:
        extra.append("--no-shap")
    run(SRC / "models" / "train_xgboost.py", extra)
    log.info("✅ Model training complete.")


def step_sanity() -> None:
    """Quick sanity check — test feature modules with synthetic data."""
    log.info("═══ SANITY CHECK ═══")

    log.info("Testing topo_features.py …")
    run(SRC / "features" / "topo_features.py")

    log.info("Testing config.py …")
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); import config; print('Config OK:', config.KANDY_CENTER)"],
        cwd=str(Path(__file__).parent),
        capture_output=False,
    )
    if result.returncode == 0:
        log.info("✅ Sanity checks passed.")
    else:
        log.error("❌ Sanity check failed. Check your Python environment.")


def step_validate() -> None:
    """Run validation and generate publication figures."""
    log.info("═══ STEP 4: VALIDATION ═══")
    log.info("Running blocked spatial + temporal CV …")
    # TODO: implement once validation scripts exist
    log.info("⚠️  Validation scripts not yet implemented. Run manually.")


def main():
    parser = argparse.ArgumentParser(description="Kandy PM2.5 Pipeline Runner")
    parser.add_argument("--all",  action="store_true", help="Run all steps end-to-end")
    parser.add_argument("--step", choices=["gee", "data", "features", "model", "validate", "sanity"],
                        help="Run a specific step")
    parser.add_argument("--tune",    action="store_true", help="Enable Optuna tuning in model step")
    parser.add_argument("--no-shap", action="store_true", help="Skip SHAP in model step")
    args = parser.parse_args()

    if args.step == "sanity" or (not args.all and not args.step):
        step_sanity()
        return

    if args.step == "gee":
        step_gee()
        return

    if args.all or args.step == "data":
        step_data()

    if args.all or args.step == "features":
        step_features()

    if args.all or args.step == "model":
        step_model(tune=args.tune, no_shap=args.no_shap)

    if args.all or args.step == "validate":
        step_validate()

    log.info("🎉 Pipeline run complete.")


if __name__ == "__main__":
    main()
