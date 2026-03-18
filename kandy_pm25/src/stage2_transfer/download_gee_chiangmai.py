"""
download_gee_chiangmai.py — Export MODIS AOD + TROPOMI satellite data for Chiang Mai
via Google Earth Engine.

Default window: 2022-01 to 2022-12 (aligned with Air4Thai station data year).
Output naming: modis_aod_chiangmai_YYYYMM.tif, tropomi_{product}_chiangmai_YYYYMM.tif
Skips months where the local .tif file already exists (safe to re-run).

Usage:
    cd kandy_pm25/
    python src/stage2_transfer/download_gee_chiangmai.py                    # full 2022
    python src/stage2_transfer/download_gee_chiangmai.py --product modis
    python src/stage2_transfer/download_gee_chiangmai.py --product tropomi
    python src/stage2_transfer/download_gee_chiangmai.py --start 2022-05    # subset
    python src/stage2_transfer/download_gee_chiangmai.py --wait             # block until done
"""

import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import (
    CHIANGMAI_BBOX,
    CHIANGMAI_MODIS_DIR,
    CHIANGMAI_TROPOMI_DIR,
    GEE_PROJECT,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("gee_chiangmai")

# ── Default export window ─────────────────────────────────────────────────────
START_YEAR  = 2022
START_MONTH = 1
END_YEAR    = 2022
END_MONTH   = 12

# Google Drive folder names (separate from Kandy and Medellin to avoid collisions)
DRIVE_MODIS   = "ChiangmaiPM25_MODIS"
DRIVE_TROPOMI = "ChiangmaiPM25_TROPOMI"

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
    # Skip if already downloaded locally
    if folder == DRIVE_MODIS:
        local = CHIANGMAI_MODIS_DIR / f"{description}.tif"
    else:
        local = CHIANGMAI_TROPOMI_DIR / f"{description}.tif"
    if local.exists():
        log.info(f"  ⏩ Skip (exists): {description}")
        return None

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
    tasks = [t for t in tasks if t is not None]
    if not tasks:
        log.info("No pending tasks.")
        return
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
    """Export monthly MODIS MAIAC AOD (550nm) for Chiang Mai."""
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
        img = col.mean().multiply(0.001)  # scale factor 0.001 → AOD units
        desc = f"modis_aod_chiangmai_{year}{month:02d}"
        tasks.append(_submit(ee, img, desc, DRIVE_MODIS, region, scale=1000))

    submitted = sum(1 for t in tasks if t is not None)
    log.info(f"MODIS: {submitted} tasks submitted ({12 - submitted} skipped).")
    return tasks


def export_tropomi(ee, region, product: str) -> list:
    """Export monthly TROPOMI composites for Chiang Mai."""
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
        desc = f"tropomi_{product.lower()}_chiangmai_{year}{month:02d}"
        # TROPOMI ~5.5km native, export at 1113m (same as Medellin)
        tasks.append(_submit(ee, img, desc, DRIVE_TROPOMI, region, scale=1113))

    submitted = sum(1 for t in tasks if t is not None)
    log.info(f"TROPOMI {product}: {submitted} tasks submitted.")
    return tasks


# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GEE exports for Chiang Mai (2022)")
    parser.add_argument("--product", choices=["modis", "tropomi", "all"], default="all")
    parser.add_argument("--wait",    action="store_true", help="Block until all tasks complete")
    parser.add_argument("--start",   type=str, default=None, help="Start month YYYY-MM")
    parser.add_argument("--end",     type=str, default=None, help="End month YYYY-MM")
    args = parser.parse_args()

    global START_YEAR, START_MONTH, END_YEAR, END_MONTH
    if args.start:
        y, m = args.start.split("-")
        START_YEAR, START_MONTH = int(y), int(m)
    if args.end:
        y, m = args.end.split("-")
        END_YEAR, END_MONTH = int(y), int(m)

    log.info(f"Export window: {START_YEAR}-{START_MONTH:02d} to {END_YEAR}-{END_MONTH:02d}")

    CHIANGMAI_MODIS_DIR.mkdir(parents=True, exist_ok=True)
    CHIANGMAI_TROPOMI_DIR.mkdir(parents=True, exist_ok=True)

    ee = init_ee()
    # CHIANGMAI_BBOX = (minlon, minlat, maxlon, maxlat)
    b = CHIANGMAI_BBOX
    region = ee.Geometry.Rectangle([b[0], b[1], b[2], b[3]])

    tasks = []
    if args.product in ("modis", "all"):
        tasks += export_modis(ee, region)

    if args.product in ("tropomi", "all"):
        for prod in ("NO2", "CO", "AER_AI"):
            tasks += export_tropomi(ee, region, prod)

    n_submitted = sum(1 for t in tasks if t is not None)
    log.info(f"\nTotal tasks submitted: {n_submitted}")
    log.info(f"Check progress at: https://code.earthengine.google.com/tasks")
    log.info(f"Download from Drive: '{DRIVE_MODIS}/' and '{DRIVE_TROPOMI}/'")
    log.info(f"Save MODIS to:   {CHIANGMAI_MODIS_DIR}")
    log.info(f"Save TROPOMI to: {CHIANGMAI_TROPOMI_DIR}")

    if args.wait:
        wait_for_tasks(tasks)


if __name__ == "__main__":
    main()
