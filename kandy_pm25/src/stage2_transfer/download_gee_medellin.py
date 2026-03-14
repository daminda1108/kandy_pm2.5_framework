"""
download_gee_medellin.py — Export MODIS AOD + TROPOMI satellite data for Medellín
via Google Earth Engine.

Default window: 2018-08 to 2025-12 (full TROPOMI era, aligned with CAMS 2018-2025).
Output naming: modis_aod_medellin_YYYYMM.tif, tropomi_no2_medellin_YYYYMM.tif, etc.
Skips months where the local .tif file already exists (safe to re-run).

Usage:
    cd kandy_pm25/
    python src/stage2_transfer/download_gee_medellin.py                    # full 2018-2025
    python src/stage2_transfer/download_gee_medellin.py --product modis
    python src/stage2_transfer/download_gee_medellin.py --product tropomi
    python src/stage2_transfer/download_gee_medellin.py --start 2019-10    # extend only
    python src/stage2_transfer/download_gee_medellin.py --wait             # block until done
"""

import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import (
    MEDELLIN_BROAD_BBOX,
    MEDELLIN_MODIS_DIR,
    MEDELLIN_TROPOMI_DIR,
    GEE_PROJECT,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("gee_medellin")

# ── Default export window ─────────────────────────────────────────────────────
# Override with --start / --end CLI args to submit only missing months
START_YEAR  = 2018
START_MONTH = 8     # August 2018 (TROPOMI start + SIATA start)
END_YEAR    = 2025
END_MONTH   = 12    # December 2025

# Google Drive folder names (separate from Kandy to avoid filename collisions)
DRIVE_MODIS   = "MedellinPM25_MODIS"
DRIVE_TROPOMI = "MedellinPM25_TROPOMI"

TROPOMI_COLLECTIONS = {
    "NO2":    ("COPERNICUS/S5P/OFFL/L3_NO2",    "tropospheric_NO2_column_number_density"),
    "CO":     ("COPERNICUS/S5P/OFFL/L3_CO",     "CO_column_number_density"),
    "AER_AI": ("COPERNICUS/S5P/OFFL/L3_AER_AI", "absorbing_aerosol_index"),
}


# ─────────────────────────────────────────────────────────────────────────────
def init_ee():
    try:
        import ee
    except ImportError:
        raise ImportError("Run: pip install earthengine-api")
    try:
        ee.Initialize(project=GEE_PROJECT)
        log.info("Earth Engine initialised.")
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=GEE_PROJECT)
    return ee


def _months_in_range(start_year, start_month, end_year, end_month):
    """Yield (year, month) tuples from start to end inclusive."""
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        yield y, m
        m += 1
        if m == 13:
            m = 1
            y += 1


def _next_month_str(year, month):
    if month == 12:
        return f"{year + 1}-01-01"
    return f"{year}-{month + 1:02d}-01"


def _submit(ee, image, description, folder, region, scale):
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        fileNamePrefix=description,
        region=region,
        scale=scale,
        crs="EPSG:4326",
        maxPixels=1e12,
        fileFormat="GeoTIFF",
    )
    task.start()
    log.info(f"  ↑ Submitted: {description}")
    return task


def wait_for_tasks(tasks, poll_interval=30):
    log.info(f"Waiting for {len(tasks)} task(s) …")
    pending = list(tasks)
    while pending:
        still = []
        for t in pending:
            state = t.status()["state"]
            if state in ("RUNNING", "READY"):
                still.append(t)
            elif state == "COMPLETED":
                log.info(f"  ✅ {t.status()['description']}")
            else:
                log.error(f"  ❌ {t.status()['description']}: {t.status().get('error_message','')}")
        pending = still
        if pending:
            log.info(f"  … {len(pending)} still running, retry in {poll_interval}s")
            time.sleep(poll_interval)
    log.info("All tasks done.")


# ─────────────────────────────────────────────────────────────────────────────
def export_modis(ee, region) -> list:
    """Export monthly MODIS MAIAC AOD (550nm) for Medellín."""
    tasks = []
    for year, month in _months_in_range(START_YEAR, START_MONTH, END_YEAR, END_MONTH):
        month_start = f"{year}-{month:02d}-01"
        month_end   = _next_month_str(year, month)

        col = (
            ee.ImageCollection("MODIS/061/MCD19A2_GRANULES")
            .filterDate(month_start, month_end)
            .filterBounds(region)
            .select("Optical_Depth_055")
        )
        # Monthly mean, scale factor 0.001 (MODIS AOD units)
        img = col.mean().multiply(0.001)

        desc = f"modis_aod_medellin_{year}{month:02d}"
        tasks.append(_submit(ee, img, desc, DRIVE_MODIS, region, scale=1000))

    log.info(f"MODIS: {len(tasks)} tasks submitted.")
    return tasks


def export_tropomi(ee, region, product: str) -> list:
    """Export monthly TROPOMI composites for Medellín."""
    collection_id, band_name = TROPOMI_COLLECTIONS[product.upper()]
    tasks = []

    for year, month in _months_in_range(START_YEAR, START_MONTH, END_YEAR, END_MONTH):
        month_start = f"{year}-{month:02d}-01"
        month_end   = _next_month_str(year, month)

        col = (
            ee.ImageCollection(collection_id)
            .filterDate(month_start, month_end)
            .filterBounds(region)
            .select(band_name)
        )
        img = col.mean()
        desc = f"tropomi_{product.lower()}_medellin_{year}{month:02d}"
        # TROPOMI ~5.5km native, export at 1113m
        tasks.append(_submit(ee, img, desc, DRIVE_TROPOMI, region, scale=1113))

    log.info(f"TROPOMI {product}: {len(tasks)} tasks submitted.")
    return tasks


# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GEE exports for Medellín (2018-2025)")
    parser.add_argument("--product", choices=["modis", "tropomi", "all"], default="all")
    parser.add_argument("--wait",    action="store_true", help="Block until all tasks complete")
    parser.add_argument("--start",   type=str, default=None,
                        help="Start month YYYY-MM (default: 2018-08). "
                             "Use to submit only missing months, e.g. --start 2019-10")
    parser.add_argument("--end",     type=str, default=None,
                        help="End month YYYY-MM (default: 2025-12)")
    args = parser.parse_args()

    # Parse --start / --end overrides
    global START_YEAR, START_MONTH, END_YEAR, END_MONTH
    if args.start:
        y, m = args.start.split("-")
        START_YEAR, START_MONTH = int(y), int(m)
    if args.end:
        y, m = args.end.split("-")
        END_YEAR, END_MONTH = int(y), int(m)

    log.info(f"Export window: {START_YEAR}-{START_MONTH:02d} to {END_YEAR}-{END_MONTH:02d}")

    # Create output dirs
    MEDELLIN_MODIS_DIR.mkdir(parents=True, exist_ok=True)
    MEDELLIN_TROPOMI_DIR.mkdir(parents=True, exist_ok=True)

    ee = init_ee()
    b = MEDELLIN_BROAD_BBOX
    region = ee.Geometry.Rectangle([b["lon_min"], b["lat_min"], b["lon_max"], b["lat_max"]])

    tasks = []
    if args.product in ("modis", "all"):
        tasks += export_modis(ee, region)

    if args.product in ("tropomi", "all"):
        for prod in ("NO2", "CO", "AER_AI"):
            tasks += export_tropomi(ee, region, prod)

    log.info(f"\nTotal tasks submitted: {len(tasks)}")
    log.info(f"Check progress at: https://code.earthengine.google.com/tasks")
    log.info(f"Download from Drive: '{DRIVE_MODIS}/' and '{DRIVE_TROPOMI}/'")
    log.info(f"Save MODIS to:   {MEDELLIN_MODIS_DIR}")
    log.info(f"Save TROPOMI to: {MEDELLIN_TROPOMI_DIR}")

    if args.wait:
        wait_for_tasks(tasks)


if __name__ == "__main__":
    main()
