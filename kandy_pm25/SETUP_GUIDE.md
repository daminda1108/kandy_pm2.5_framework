# 🚀 SETUP GUIDE — Kandy PM2.5 Dual-Track Research Project
## *(Updated: GEE is now the primary data source)*

---

## Your First 30 Minutes

---

## Step 1: Install Python Dependencies

```bash
cd d:\ProjectCD\kandy_pm25
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Also install GEE packages:
```bash
pip install earthengine-api geemap
```

---

## Step 2: Authenticate Google Earth Engine (One-Time)

```bash
earthengine authenticate
```

This opens a browser window → sign in with your GEE-registered Google account → paste the token back into the terminal.

Test it works:
```bash
python -c "import ee; ee.Initialize(); print('GEE OK')"
```

---

## Step 3: Quick Sanity Check

```bash
python run_pipeline.py --step sanity
```
Expected: `✅ Sanity checks passed.`

---

## Step 4: Export Data from GEE → Google Drive

This submits GEE export tasks that run in Google's cloud. They appear in the [GEE Task Manager](https://code.earthengine.google.com/tasks).

```bash
# Export everything: MODIS AOD, TROPOMI, ERA5, DEM, WorldCover, NDVI (2019–2025)
python src/stage1_satml/data/download_gee.py --start 2019 --end 2025

# Or export just the fast CSV path first (ERA5 point time series — fastest)
python src/stage1_satml/data/download_gee.py --product csv_timeseries

# Export just the static layers (DEM, land cover) — always do this early
python src/stage1_satml/data/download_gee.py --product dem
```

> **⏱ Expected export times:**
> | Product | Export Time |
> |---------|-------------|
> | ERA5 CSV (7 years) | 5–15 min |
> | DEM + static | 5–10 min |
> | MODIS AOD (7 years) | 30–90 min |
> | TROPOMI x3 (7 years) | 60–180 min |

Check progress at: https://code.earthengine.google.com/tasks

---

## Step 5: Download Files from Google Drive → Local

Once tasks complete, download the folders from Google Drive to:
```
d:\ProjectCD\kandy_pm25\data\raw\
  era5_csv\           ← ERA5 point CSVs (era5_point_kandy_YYYY.csv)
  dem\                ← DEM GeoTIFFs (srtm_elevation_30m.tif etc.)
  modis_aod\          ← MODIS AOD monthly GeoTIFFs
  tropomi\            ← TROPOMI monthly GeoTIFFs
  land_cover\         ← ESA WorldCover GeoTIFF
```

> 💡 **Tip**: You can use [Google Drive for Desktop](https://www.google.com/drive/download/) to sync the folder automatically.

---

## Step 6: Process GEE Exports → Feature Tables

```bash
# Process everything
python src/stage1_satml/data/process_gee_exports.py

# Or process ERA5 CSVs only (fastest first step — do this while downloading the rest)
python src/stage1_satml/data/process_gee_exports.py --step era5_csv
```

This creates `.parquet` files in `data/processed/features/`.

---

## Step 7: Build the Master ML Dataset

```bash
python src/stage1_satml/features/build_dataset.py
```

Creates `data/processed/merged/dataset_daily.parquet` with all features merged.

---

## Step 8: Add Ground Truth PM2.5 (When Available)

Place CSV files in `data/raw/ground_truth/` with columns `date, pm25`:
```csv
date,pm25
2022-01-01,35.2
2022-01-02,42.1
```

Sources:
- **CEA Kandy**: https://www.cea.lk/web/
- **cleanair.lk**: https://www.cleanair.lk/
- **Dr. Gayan Bowatte**: (approach once model is working)

The pipeline picks these up automatically — no code changes needed.

---

## Step 9: Train Your First Model

```bash
python src/stage1_satml/models/train_xgboost.py         # Standard training
python src/stage1_satml/models/train_xgboost.py --tune  # + Optuna hyperparameter search
```

---

## Quick Reference — GEE Products

| What | GEE Collection | Resolution | Years |
|------|---------------|-----------|-------|
| MODIS MAIAC AOD | `MODIS/061/MCD19A2_GRANULES` | 1 km | 2019–2025 |
| TROPOMI NO₂ | `COPERNICUS/S5P/OFFL/L3_NO2` | ~1 km | 2019–2025 |
| TROPOMI CO | `COPERNICUS/S5P/OFFL/L3_CO` | ~1 km | 2019–2025 |
| TROPOMI AER_AI | `COPERNICUS/S5P/OFFL/L3_AER_AI` | ~1 km | 2019–2025 |
| ERA5-Land Daily | `ECMWF/ERA5_LAND/DAILY_AGGR` | 11 km | 2019–2025 |
| SRTM DEM 30m | `USGS/SRTMGL1_003` | 30 m | static |
| ESA WorldCover | `ESA/WorldCover/v200` | 10 m | 2021 |
| VIIRS NTL | `NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG` | 500 m | 2023 |
| NDVI | `MODIS/061/MOD13A2` | 1 km | 2019–2025 |

---

## File Map

```
kandy_pm25/
├── run_pipeline.py                   ← 🚀 Master runner
├── config.py                         ← All settings, paths, constants
├── requirements.txt                  ← Python packages
│
├── src/stage1_satml/
│   ├── data/
│   │   ├── download_gee.py           ← ⭐ PRIMARY: GEE export jobs
│   │   ├── process_gee_exports.py    ← ⭐ Convert Drive exports → features
│   │   ├── download_era5.py          ← Alt: Direct CDS API download
│   │   ├── download_modis.py         ← Alt: Direct NASA download
│   │   ├── download_tropomi.py       ← Alt: Direct Copernicus download
│   │   └── download_dem.py           ← Alt: Direct SRTM download
│   ├── features/
│   │   ├── topo_features.py          ← ⭐ VVC, KFP, TII, DSC, RWP
│   │   ├── meteo_features.py         ← ERA5 processing (CDS path)
│   │   ├── satellite_features.py     ← MODIS + TROPOMI (direct path)
│   │   └── build_dataset.py          ← Merge all → parquet
│   └── models/
│       └── train_xgboost.py          ← XGBoost + SHAP + Optuna
│
├── data/raw/
│   ├── era5_csv/                     ← ERA5 point CSVs from GEE
│   ├── dem/                          ← SRTM GeoTIFFs from GEE
│   ├── modis_aod/                    ← MODIS GeoTIFFs from GEE
│   ├── tropomi/                      ← TROPOMI GeoTIFFs from GEE
│   ├── land_cover/                   ← ESA WorldCover from GEE
│   └── ground_truth/                 ← PM2.5 validation CSVs (manual)
│
└── data/processed/
    ├── features/                     ← Processed feature parquets
    └── merged/dataset_daily.parquet  ← Final ML dataset
```

---

## Parallel Learning Track (Start NOW)

| Week | Topic | Link |
|------|-------|------|
| This week | PyTorch basics | [pytorch.org/tutorials](https://pytorch.org/tutorials/beginner/blitz/tensor_tutorial.html) |
| Week 2 | What is a PINN? | [sciml.ai book](https://book.sciml.ai) Ch. 1-3 |
| Week 3 | GEE Python API | [developers.google.com/earth-engine/guides](https://developers.google.com/earth-engine/guides) |
| Week 4 | First PINN (dy/dx = -y) | [deepxde.readthedocs.io](https://deepxde.readthedocs.io/) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ee.Initialize()` fails | Run `earthengine authenticate` in terminal |
| GEE task fails ("Too many pixels") | Reduce date range or clip region tighter |
| CSV has no data | Check `.geo` column — GEE sometimes exports geometry-only rows |
| MODIS all NaN | Apply date filter: MAIAC only available 2000-present; check tile coverage |
| ERA5 CDS download fails | Fall back to GEE CSV path — same data, easier access |

---

*Last updated: 2026-02-20 | Project: Kandy PM2.5 Dual-Track Research*
