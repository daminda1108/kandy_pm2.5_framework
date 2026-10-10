"""
download_gee_drive_outputs.py — Download completed GEE exports from Google Drive.

Uses the existing EE OAuth credentials (which include Drive scope) — no extra auth needed.

Downloads:
  BogotaTierC_Data/      → data/external/bogota/geos_cf/
  MexicoCityTierC_Data/  → data/external/mexico_city/geos_cf/
  SourceCityTerrain_Data/ → data/external/{city}/dem/

Usage:
    python scripts/download_gee_drive_outputs.py              # all folders
    python scripts/download_gee_drive_outputs.py --folder BogotaTierC_Data
    python scripts/download_gee_drive_outputs.py --list       # list without downloading
"""

import argparse
import io
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger("drive_dl")

ROOT = Path(__file__).parents[1]

FOLDER_MAP = {
    # PVAF v15 source set Drive folders (amendment 10i, 2026-05-24).
    # Note: GEE tasks submitted with "datong" prefix actually target the
    # Jincheng-area bbox (Nominatim disambiguation; see download_cnemc_v15.py).
    # We map datong_* outputs to the jincheng/ local folder (2026-05-26 rename).
    **{
        f"{city.capitalize()}_v15_GEE": {
            "local_dir": None,
            "extensions": [".csv"],
            "route_by_prefix": {
                f"{city}_geos_cf_":      ROOT / f"data/external/{local_slug}/geos_cf",
                f"{city}_era5land_":     ROOT / f"data/external/{local_slug}/era5_land_gee",
                f"{city}_u_compon_":     ROOT / f"data/external/{local_slug}/era5_land_gee",
                f"{city}_zpbl_":         ROOT / f"data/external/{local_slug}/zpbl_gee",
                f"{city}_gpm_":          ROOT / f"data/external/{local_slug}/gpm",
                # v15.1 additions (TROPOMI NO2 + ERA5 ssr, 2026-05-26)
                f"{city}_era5_ssr_":     ROOT / f"data/external/{local_slug}/era5_ssr_hourly",
                f"{city}_tropomi_no2_":  ROOT / f"data/external/{local_slug}/tropomi_no2_daily",
            },
        }
        for city, local_slug in [
            ("xichang", "xichang"),
            ("bazhou",  "bazhou"),
            ("datong",  "jincheng"),   # GEE submitted as datong_*, route to jincheng/
            ("baoji",   "baoji"),
            ("yichang", "yichang"),
            ("taian",   "taian"),
            ("chandigarh", "chandigarh"),
        ]
    },
    "SourceCityTerrain_Data": {
        "local_dir": None,
        "extensions": [".tif"],
        "route_by_prefix": {
            **{f"{c}_": ROOT / f"data/external/{c}/dem"
               for c in ("xichang","bazhou","jincheng","baoji","yichang","taian","chandigarh")},
        },
    },
    "VIIRS_NTL_Data": {
        "local_dir": ROOT / "data/external/viirs_ntl",
        "extensions": [".tif"],
    },
    # Forecast backtest (F-M0, 2026-07-10): archived GEOS-CF FORECAST area-mean driver
    # CSVs (gee_export_geoscf_forecast.py) for the M2 rolling-origin backtest.
    # Kandy-model ladder rung (2026-10-10): GEOS-CF daily area means per ladder city
    # (pull_kandy_model_priors.py --submit).
    "KANDYMODEL_LADDER": {
        "local_dir": ROOT / "data/processed/modular/kandy_model_rung/raw",
        "extensions": [".csv"],
    },
    "GEOSCF_FCST": {
        "local_dir": ROOT / "data/external/geoscf_forecast",
        "extensions": [".csv"],
    },
    # Medellín deliverable (2026-07-14): extended drivers — GEOS-CF PM25+ZPBL 2025-26 +
    # ERA5-Land u10/v10/t2m/d2m/tp 2018-2026 (full weather panel + reconstruction span).
    "MedellinExtGEE": {
        "local_dir": ROOT / "data/external/medellin/extended_gee/drive",
        "extensions": [".csv"],
    },
    # Kandy extension tier (Phase 5.1, 2026-07-19): area-mean GEOS-CF PM25+ZPBL +
    # ERA5-Land u10/v10/t2m/d2m/tp 2024-2026 for the driver-anchored post-VanD tier.
    "KandyExtGEE": {
        "local_dir": ROOT / "data/external/kandy/extended_gee/drive",
        "extensions": [".csv"],
    },
    # IMERG gap-fill (rain arbitration, 2026-07-21): the years the on-disk IMERG
    # archive was missing, so both apps can ship rain on their newest year instead
    # of withholding it. Land beside the existing IMERG CSVs so they concatenate.
    "MedellinIMERG": {
        "local_dir": ROOT / "data/external/medellin/tier_c",
        "extensions": [".csv"],
    },
    "KandyIMERG": {
        "local_dir": ROOT / "data/external/tier_c/gpm_imerg",
        "extensions": [".csv"],
    },
    # SERENDIB CNEMC panel met (cnemc_met_export.py): daily GEOS-CF + ERA5 + ERA5-Land
    # driver series at 199 panel-city centroids, for the full-panel Track-T gate.
    "cnemc_met": {
        "local_dir": ROOT / "data/processed/cnemc_panel/met_raw",
        "extensions": [".csv"],
    },
    # SERENDIB Track-S satellite covariates (cnemc_covar_export.py): NTL/NO2/SO2/FIRMS
    # at panel centroids — emission-mix proxies (EDGAR-free) + activity level.
    "cnemc_covar": {
        "local_dir": ROOT / "data/processed/cnemc_panel/covar_raw",
        "extensions": [".csv"],
    },
    # station-level covariates (cnemc_covar_export.py --level stations): NTL/NO2/SO2/
    # FIRMS/elev at the 1565 panel stations — the WITHIN-city PatternNet covariates.
    "cnemc_covar_stn": {
        "local_dir": ROOT / "data/processed/cnemc_panel/covar_stn_raw",
        "extensions": [".csv"],
    },
    # OpenAQ-extended (2026-05-10 data pivot) — gee_export_extended.py outputs
    "KathmanduExtended_Data": {
        "local_dir": None,
        "extensions": [".csv"],
        "route_by_prefix": {
            "kathmandu_blh_":       ROOT / "data/external/kathmandu/extended_gee/blh",
            "kathmandu_geos_cf_":   ROOT / "data/external/kathmandu/extended_gee/geos_cf",
            "kathmandu_era5_land_": ROOT / "data/external/kathmandu/extended_gee/era5_land",
        },
    },
    "ChiangmaiExtended_Data": {
        "local_dir": None,
        "extensions": [".csv"],
        "route_by_prefix": {
            "chiangmai_blh_":       ROOT / "data/external/chiangmai/extended_gee/blh",
            "chiangmai_geos_cf_":   ROOT / "data/external/chiangmai/extended_gee/geos_cf",
            "chiangmai_era5_land_": ROOT / "data/external/chiangmai/extended_gee/era5_land",
        },
    },
    "MedellinExtended_Data": {
        "local_dir": None,
        "extensions": [".csv"],
        "route_by_prefix": {
            "medellin_blh_":       ROOT / "data/external/medellin/extended_gee/blh",
            "medellin_geos_cf_":   ROOT / "data/external/medellin/extended_gee/geos_cf",
            "medellin_era5_land_": ROOT / "data/external/medellin/extended_gee/era5_land",
        },
    },
    # Stage 1 v3 hourly RECAP additions (2026-05-20)
    "KandyV3_Data": {
        "local_dir": None,
        "extensions": [".csv"],
        "route_by_prefix": {
            "kandy_era5_ssr_":      ROOT / "data/external/kandy/era5_ssr_hourly",
            "kandy_tropomi_no2_":   ROOT / "data/external/kandy/tropomi_no2_daily",
        },
    },
}


def _get_drive_service():
    import json
    from ee import oauth as ee_oauth
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds_path = Path.home() / ".config/earthengine/credentials"
    with open(creds_path) as f:
        raw = json.load(f)

    creds = Credentials(
        token=None,
        refresh_token=raw["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=ee_oauth.CLIENT_ID,
        client_secret=ee_oauth.CLIENT_SECRET,
        scopes=raw.get("scopes", ["https://www.googleapis.com/auth/drive"]),
    )
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    log.info("Drive API initialised")
    return service


def _find_folder_ids(service, folder_name: str) -> list[str]:
    """ALL Drive folders with this name, not just the first.

    Drive permits duplicate folder names, and GEE will happily write successive
    exports into different same-named folders. Returning only files[0] silently
    lost files: the 2026-07-21 IMERG gap-fill put med_gpm_imerg_2024 in a second
    'MedellinIMERG' folder, and the download reported success while that year
    never arrived. Scan every match.
    """
    resp = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)",
        pageSize=25,
    ).execute()
    files = resp.get("files", [])
    if not files:
        log.warning("Drive folder not found: %s", folder_name)
        return []
    ids = [f["id"] for f in files]
    if len(ids) > 1:
        log.info("Found %d Drive folders named '%s' — scanning all: %s",
                 len(ids), folder_name, ", ".join(ids))
    else:
        log.info("Found Drive folder '%s': %s", folder_name, ids[0])
    return ids


def _list_files(service, folder_id: str, extensions: list[str]) -> list[dict]:
    ext_q = " or ".join(f"name contains '{e}'" for e in extensions)
    query = f"'{folder_id}' in parents and trashed=false and ({ext_q})"
    results, token = [], None
    while True:
        resp = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, size)",
            pageSize=100,
            pageToken=token,
        ).execute()
        results.extend(resp.get("files", []))
        token = resp.get("nextPageToken")
        if not token:
            break
    return results


def _download_file(service, file_id: str, dest_path: Path):
    from googleapiclient.http import MediaIoBaseDownload

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, request, chunksize=8 * 1024 * 1024)
    done = False
    while not done:
        _, done = dl.next_chunk()
    dest_path.write_bytes(buf.getvalue())
    size_mb = dest_path.stat().st_size / 1e6
    log.info("  saved: %s (%.1f MB)", dest_path.name, size_mb)


def download_folder(service, folder_name: str, cfg: dict, list_only: bool = False):
    log.info("=== %s ===", folder_name)
    folder_ids = _find_folder_ids(service, folder_name)
    if not folder_ids:
        return 0

    files, seen = [], set()
    for fid in folder_ids:
        for f in _list_files(service, fid, cfg["extensions"]):
            if f["name"] not in seen:      # first copy wins if duplicated across folders
                seen.add(f["name"])
                files.append(f)
    log.info("  %d file(s) found", len(files))

    downloaded = 0
    for f in sorted(files, key=lambda x: x["name"]):
        name = f["name"]
        size_mb = int(f.get("size", 0)) / 1e6

        # Determine local destination
        dest_dir = cfg.get("local_dir")
        if cfg.get("route_by_prefix"):
            for prefix, d in cfg["route_by_prefix"].items():
                if name.startswith(prefix):
                    dest_dir = d
                    break
        if dest_dir is None:
            log.warning("  no route for file: %s — skipping", name)
            continue

        dest_path = dest_dir / name

        if list_only:
            status = "EXISTS" if dest_path.exists() else "MISSING"
            log.info("  [%-7s] %s (%.1f MB)", status, name, size_mb)
            continue

        if dest_path.exists():
            log.info("  skip (exists): %s", name)
            continue

        log.info("  downloading: %s (%.1f MB)", name, size_mb)
        _download_file(service, f["id"], dest_path)
        downloaded += 1

    return downloaded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", choices=list(FOLDER_MAP) + ["all"], default="all",
                        help="Which Drive folder to download")
    parser.add_argument("--list",   action="store_true", help="List files without downloading")
    args = parser.parse_args()

    service = _get_drive_service()

    folders = list(FOLDER_MAP) if args.folder == "all" else [args.folder]
    total = 0
    for folder_name in folders:
        n = download_folder(service, folder_name, FOLDER_MAP[folder_name], list_only=args.list)
        total += n

    if not args.list:
        log.info("\nTotal downloaded: %d file(s)", total)
        log.info("Next steps:")
        log.info("  1. python scripts/gee_export_source_city_terrain.py --build")
        log.info("  2. python scripts/merge_source_city_geos_cf.py  (once ERA5 ready)")


if __name__ == "__main__":
    main()
