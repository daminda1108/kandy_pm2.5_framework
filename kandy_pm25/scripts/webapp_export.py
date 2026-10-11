"""webapp_export.py — export the PM2.5 Explorer web payload (Kandy + Medellín).

Produces a fully static, client-reconstructable payload from the locked additive_v2
production model. The browser rebuilds any hour's 1 km field exactly from:

    PM(x,y,t) = B(t) + max(T(t) - B(t), 0) * P_local(x,y,t) + min(T(t) - B(t), 0)
    q05/q95   = same split with T05/T95                        (same P_local)

so only ONE gridded time-varying object is shipped (P_local, uint16), plus small
per-hour scalar series and static layers. Wind is the WindNinja library + per-hour
blend weights (JS replays terrain_transport.windninja_wind exactly).

City abstraction (2026-07-12, S4 Medellín showcase): every asset path / feature flag
lives in CITIES[city]; Kandy output is byte-stable at kandy_webapp/data/, Medellín
goes to kandy_webapp/data/medellin/. Medellín extras: the zero-ground-data (VanD)
tier ships as three extra scalar series (Tv,Tv05,Tv95 — SAME P_local by construction,
build_field uses one pattern for both tiers), plus the proving-ground payloads
(stations/showcase/forecast/datavalue) read from results/figures/medellin_showcase/.

Outputs (per city, default d:/ProjectCD/kandy_webapp/data[/medellin]/):
  meta.json                         grid, years, bbox, scales, episodes, credits
  scalars_{year}.json               per-hour T,B,T05,T95,B_lo,B_hi,u10,v10,blh,wspd,
                                     wdir + wind blend (i0,wd0,cs0,wn) + basin/core
                                     [+ Tv,Tv05,Tv95 zero-data tier when available]
  plocal_{year}_{MM}.bin.gz         uint16 P_local, (n_hours_in_month, npx) row-major
  wind_library.bin.gz               int16 U,V (16 dir x 2 spd x 2 regime x 64 x 64)
  static/hillshade.png              shaded relief (bbox-aligned)
  static/layers.json                OSM roads/river/water/places (simplified), landmarks
  static/emission.json              S_traffic contour polylines (normalised)
  static/fields.json                elev16, pop16, S16 on the PM grid
  health.json / fect_{year}.json    Kandy only (exposure+GEMM burden; FECT overlay)
  stations.json / showcase.json /   Medellín only (station reveal, act scorecards,
    forecast.json / datavalue.json    forecast scoreboard, data-value slider)

QA gate (blocking): reconstruct N random (pixel,hour) samples/year from the exported
payload and compare to the source parquet q50/q05/q95 (tol 0.25 ug/m3) — for BOTH
tiers where the vand tier ships; verify the wind blend reproduces windninja_wind()
(tol 0.05 m/s). Run:
    python scripts/webapp_export.py [--city medellin]           # export + QA
    python scripts/webapp_export.py [--city medellin] --qa-only # re-run QA only
"""
from __future__ import annotations
import argparse
import gzip
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from src.stage1_satml.decomp import terrain_transport as tt  # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
STG = REPO / "data" / "processed" / "stage1_v3"
STG2 = REPO / "data" / "processed" / "stage2"
PIN = REPO / "data" / "processed" / "pinn_inputs"
TANC = STG / "T_anchor"
DECM = REPO / "data" / "processed" / "decomp_medellin"
SHOW = REPO / "results" / "figures" / "medellin_showcase"
WEBROOT = Path(r"d:/ProjectCD/kandy_webapp/data")

# P_local is DC-stable (mean 1) but unbounded when the increment T-B is small, so it is
# quantised with a PER-HOUR min/max window (2 floats/hour) rather than a fixed ceiling:
# reconstruction error = (T-B)*(pmax-pmin)/65535, negligible in every regime (episode
# cores AND near-clean hours). No clipping ever.
DEGEN_TB = 0.5             # |T-B| below this -> store P_local=1 (field == B there)

# Curated map labels. Coordinates from the OSM places layer (verified in-bbox).
# k: "city" (primary), "town" (secondary), "sensor" (measurement site marker).
# Hantana FECT placement uses the audited coordinate (7.265 N, 80.625 E — see
# docs/audit_2026-05-29.md E2); Akurana FECT (7.366 N) sits outside the frame and
# is therefore not drawn. NIFS/KOALA label removed per user request 2026-07-05.
KANDY_LANDMARKS = [
    {"n": "Kandy",           "lat": 7.2906,  "lon": 80.6337,  "k": "city"},
    {"n": "Katugastota",     "lat": 7.32208, "lon": 80.62496, "k": "town"},
    {"n": "Peradeniya",      "lat": 7.26421, "lon": 80.59307, "k": "town"},
    {"n": "Kundasale",       "lat": 7.28045, "lon": 80.68446, "k": "town"},
    {"n": "Ampitiya",        "lat": 7.26787, "lon": 80.6663,  "k": "town"},
    {"n": "Pallekele",       "lat": 7.28053, "lon": 80.69607, "k": "town"},
    {"n": "Wattegama",       "lat": 7.35132, "lon": 80.68259, "k": "town"},
    {"n": "Gannoruwa",       "lat": 7.28245, "lon": 80.59253, "k": "town"},
    {"n": "Kiribathkumbura", "lat": 7.26773, "lon": 80.57626, "k": "town"},
    {"n": "Madawala",        "lat": 7.32858, "lon": 80.67351, "k": "town"},
    {"n": "Talatuoya",       "lat": 7.25151, "lon": 80.69036, "k": "town"},
    {"n": "Halloluwa",       "lat": 7.29073, "lon": 80.6071,  "k": "town"},
    {"n": "Ambatenna",       "lat": 7.35089, "lon": 80.61422, "k": "town"},
    {"n": "Hantana sensor",  "lat": 7.2650,  "lon": 80.6250,  "k": "sensor"},
]
KANDY_EPISODES = [
    {"id": "nov2019", "ts": "2019-11-04 08:00",
     "title": "Nov 2019 haze event",
     "note": "Haze event during the 2019 Kandy measurement campaign. North-easterly "
             "inflow carried a high regional background over a calm, shallow boundary "
             "layer. Reconstructed basin mean ~45, city centre ~63 ug/m3.",
     "source": "Senarathna et al. 2024; AGU conference record"},
    {"id": "dec2022", "ts": "2022-12-07 08:00",
     "title": "Dec 2022 nationwide haze",
     "note": "Air quality advisories were issued island-wide (AQI 150-200). "
             "North-east monsoon inflow with night-time stagnation. Reconstructed "
             "basin mean ~56, city centre ~67 ug/m3.",
     "source": "NBRO advisory, Dec 2022"},
    {"id": "mar2023", "ts": "2023-03-01 08:00",
     "title": "Feb-Mar 2023 inter-monsoon haze",
     "note": "Stable inter-monsoon conditions with reduced dispersion, noted in a "
             "CEA advisory. Reconstructed basin mean ~34, city centre ~37 ug/m3.",
     "source": "CEA advisory, Mar 2023"},
]
KANDY_CREDITS = [
    ["Satellite PM2.5 level anchor", "Van Donkelaar / ACAG V6.GL02.04 (WUSTL)"],
    ["Level calibration and reference check", "Central Environmental Authority, Kandy AQMS (AirShare, aq.cea.lk)"],
    ["Independent PM2.5 cross-check", "GHAP, Wei et al."],
    ["Meteorology", "ERA5 / Copernicus (CDS); GEOS-CF (NASA GMAO)"],
    ["Terrain wind", "WindNinja (USDA Forest Service)"],
    ["Basemap vectors", "OpenStreetMap contributors (ODbL)"],
    ["Ground reference (diurnal)", "FECT PurpleAir, Akurana"],
    ["Diurnal/seasonal validation", "Senarathna et al. 2024, Ceylon J. Sci."],
]

# Medellín labels curated from the OSM places pull (osm_medellin/places.geojson).
MEDELLIN_LANDMARKS = [
    {"n": "Medellín",    "lat": 6.24434, "lon": -75.57355, "k": "city"},
    {"n": "Bello",       "lat": 6.33500, "lon": -75.55827, "k": "city"},
    {"n": "Itagüí",      "lat": 6.17244, "lon": -75.60933, "k": "town"},
    {"n": "Envigado",    "lat": 6.17013, "lon": -75.58741, "k": "town"},
    {"n": "Sabaneta",    "lat": 6.15153, "lon": -75.61537, "k": "town"},
    {"n": "La Estrella", "lat": 6.15768, "lon": -75.64339, "k": "town"},
    {"n": "Copacabana",  "lat": 6.34610, "lon": -75.50803, "k": "town"},
    {"n": "El Poblado",  "lat": 6.20062, "lon": -75.56368, "k": "town"},
    {"n": "Belén",       "lat": 6.22588, "lon": -75.60049, "k": "town"},
    {"n": "Robledo",     "lat": 6.27907, "lon": -75.58877, "k": "town"},
    {"n": "Manrique",    "lat": 6.27506, "lon": -75.54589, "k": "town"},
    {"n": "San Javier",  "lat": 6.25627, "lon": -75.62154, "k": "town"},
]

# Officially DECLARED air-quality contingencies (Area Metropolitana del Valle de Aburra),
# used the same way as the Kandy episodes: an external, independently-dated event the
# reconstruction can be checked against. Model values below are read off the shipped
# additive_v2 field, NOT tuned to the declaration.
MEDELLIN_EPISODES = [
    {"id": "mar2019a", "ts": "2019-03-06 09:00",
     "title": "Mar 2019 air-quality alert",
     "note": "The metropolitan authority declared an air-quality alert for 6-8 March 2019: "
             "partial cloud cover suppressed surface heating, the valley failed to mix out "
             "and pollutants accumulated. Reconstructed basin mean over the window ~41, "
             "worst hour ~53 with a peak pixel near 64 ug/m3.",
     "source": "Area Metropolitana del Valle de Aburra, alert declaration, March 2019"},
    {"id": "mar2019b", "ts": "2019-03-26 10:00",
     "title": "Mar 2019 red alert (alerta roja fase 1)",
     "note": "Red alert 22-27 March 2019 across the ten metropolitan municipalities; most "
             "of the 19-20 station network read red, and vehicle restrictions were widened. "
             "Reconstructed basin mean over the window ~36, worst hour ~68 with a peak "
             "pixel near 82 ug/m3.",
     "source": "Area Metropolitana del Valle de Aburra red-alert declaration; press record "
               "(El Tiempo, Semana), March 2019"},
]
MEDELLIN_CREDITS = [
    ["Satellite PM2.5 level anchor", "Van Donkelaar / ACAG V6.GL02.04 (WUSTL)"],
    ["Ground truth (validation)", "SIATA / OpenAQ station network, Área Metropolitana"],
    ["Meteorology", "ERA5-Land / Copernicus; GEOS-CF (NASA GMAO)"],
    ["Terrain wind", "WindNinja (USDA Forest Service)"],
    ["Basemap vectors", "OpenStreetMap contributors (ODbL)"],
]

# Kandy extension years (Phase 5.1, 2026-07-19): the VanD satellite anchor ends 2023,
# so 2024+ come from the driver-anchored tier (`*_drv` products) — level+timing from
# the Medellin-validated driver recipe retargeted onto the locked area-anchored T(t),
# street-scale pattern from the month x hour climatology. Disclosed in the UI via
# meta.tiers; the locked 2019-2023 headline products are untouched.
KANDY_EXT_YEARS = [2024, 2025, 2026]     # 2026 = partial year (to ERA5-Land's edge)


def _kandy_field(y):
    s = "_drv" if y in KANDY_EXT_YEARS else ""
    return DEC / f"kandy_decomp_predictions_{y}_additive_v3{s}.parquet"


def _kandy_b(y):
    s = "_drv" if y in KANDY_EXT_YEARS else ""
    return DEC / f"B_background_hourly_{y}_v2{s}.parquet"


def _kandy_t(y):
    s = "_drv" if y in KANDY_EXT_YEARS else ""
    return TANC / f"T_kandy_hourly_{y}{s}.parquet"


CITIES = {
    "kandy": dict(
        out=WEBROOT,
        years=[2019, 2020, 2021, 2022, 2023] + KANDY_EXT_YEARS,
        title="Kandy PM2.5 Explorer",
        tz="Asia/Colombo",
        core=(7.2906, 80.6337),
        field=_kandy_field,
        vand_field=None,
        bfile=_kandy_b,
        tfile=_kandy_t,
        met="inference",
        # ventilated-hour pattern floor (additive_v3): the increment-split renders
        # T<=B hours perfectly flat, but Medellin ground truth keeps real spatial
        # spread on exactly those hours (flat_hour_residual_fit.py PASS). The floor
        # is a mean-zero pattern amplitude (T-lock exact, no inversion). Kandy value
        # is the cross-city relative form (no local network) — see additive_v3_eps.json.
        eps_floor=DEC / "additive_v3_eps.json",
        # per-year provenance shipped to the UI (see export_meta)
        tiers={"anchored": [2019, 2020, 2021, 2022, 2023], "extension": KANDY_EXT_YEARS},
        tier_note=("2019-2023 take their level from the Van Donkelaar satellite product, scaled by one "
                   "factor (0.80) fitted to the Central Environmental Authority's Kandy station over "
                   "2019 to mid-2021 and checked on its 2022-2023 record (bias about -1%). "
                   "Against that station the 2024-2026 extension reads about 40% LOW: treat its "
                   "level as uncertain. "
                   "2024 onwards are an extension: the yearly level and the daily and "
                   "seasonal timing are modelled from meteorology and a global "
                   "chemistry forecast (a method validated against Medellin's "
                   "monitoring network), while the street-scale pattern is the "
                   "climatological one from 2019-2023. "
                   "The estimator behind this tier under-produced high-pollution hours "
                   "(2026-08-07): a statistical correction, checked by holding out each "
                   "anchored year in turn, restores the frequency and size of episodes "
                   "to within a few percent of the anchored years. That correction fixes "
                   "HOW OFTEN episodes of a given size occur; it does NOT establish that "
                   "they fall on the right hours, and the hour-to-hour ranking is "
                   "unchanged. Treat a specific hour in 2024-2026 as indicative of "
                   "conditions rather than as a reading, and note the interval on these "
                   "years is deliberately wider than on the anchored ones."),
        # B2 thermal valley-circulation wind input — METHOD-TRANSFER PRIOR (5.2,
        # 2026-07-21): form validated at Medellín (r +0.60) + Kathmandu (r +0.67);
        # Kandy params are priors (DEM drainage axis 344.5 deg via the Katugastota
        # outlet, relief-scaled amplitude), NOT locally fitted — no Kandy wind obs.
        # Disclosed on-site; falsifier = one season of local anemometer data.
        # rain source = GPM IMERG V07, NOT ERA5-Land tp (arbitration 2026-07-21:
        # IMERG 0.98x the Sri Lanka DoM representative station; ERA5-Land 2.10x)
        imerg=(REPO / "data/external/tier_c/gpm_imerg", "gpm_imerg_*.csv"),
        wind_calib=REPO / "results/figures/kandy_extension/b2_kandy_wind_prior.json",
        wind_note=("Wind uses a thermal valley-circulation model validated against "
                   "weather stations in two analogue valleys (Medellin, Kathmandu). "
                   "Kandy has no wind record, so its parameters are physical priors "
                   "(valley axis from the terrain, strength scaled by relief) - "
                   "indicative, not locally calibrated."),
        wind_lib=PIN / "windninja_library.npz",
        elev=("npz", PIN / "kandy_elev_grid_100m.npz"),
        pop=DEC / "population_kandy.npz",
        straffic=(DEC / "S_traffic_kandy.npz", "fine_lat", "fine_lon", "E_fine"),
        osm=DEC / "osm_kandy",
        landmarks=KANDY_LANDMARKS, episodes=KANDY_EPISODES, credits=KANDY_CREDITS,
        health=True, fect=True, showcase=False,
        integrity=("Research model. The annual level is the Van Donkelaar (ACAG V6) "
                   "satellite product scaled to the Central Environmental Authority's Kandy "
                   "monitoring station (fitted 2019 to mid-2021, checked on 2022-2023). The "
                   "seasonal and day-to-day structure is checked against that station and "
                   "other records; night-time levels relative to midday are too high. The "
                   "fine within-city pattern is a satellite level surface times terrain "
                   "confinement, not a measured map, and is best read as indicative. "
                   "No attributable-death estimate is given."),
    ),
    "medellin": dict(
        out=Path(r"d:/ProjectCD/medellin_webapp/data"),   # standalone app (2026-07-13)
        years=[2018, 2019, 2020, 2021, 2022, 2023, 2024],  # full ground+met span (v16 rebuild)
        title="Medellín PM2.5 — proving ground",
        tz="America/Bogota",
        core=(6.24434, -75.57355),
        # additive_v3 (ventilated-hour floor) — at Medellín eps0 is the city's OWN fit
        # (5.65) and the improvement is VALIDATED on the withheld network: holdout-6
        # flat-hour RMSE 8.531 -> 8.004 with bias -5.86 -> -5.06, overall unchanged
        # (scripts/score_additive_v3.py). Both tiers share P_local by construction.
        field=lambda y: DECM / f"medellin_decomp_predictions_{y}_additive_v3.parquet",
        vand_field=lambda y: DECM / f"medellin_decomp_predictions_{y}_additive_v3_vand.parquet",
        eps_floor=DECM / "additive_v3_eps.json",
        bfile=lambda y: DECM / f"B_background_hourly_{y}_medellin.parquet",
        tfile=lambda y: DECM / f"T_medellin_hourly_{y}.parquet",
        met="drivers",
        wind_lib=PIN / "medellin_windninja_library.npz",
        elev=("tif", REPO / "data" / "external" / "medellin" / "dem" / "medellin_dem.tif"),
        pop=None,
        straffic=(DEC / "S_traffic_medellin.npz", "lats", "lons", "S_traffic"),
        osm=DEC / "osm_medellin",
        landmarks=MEDELLIN_LANDMARKS, episodes=MEDELLIN_EPISODES, credits=MEDELLIN_CREDITS,
        health=False, fect=False, showcase=True,
        # displayed t2m is lapse-adjusted from the basin-AREA mean (2091 m mean
        # elevation) to the valley floor (~1490 m, Olaya Herrera): +0.0065*(2091-1490)
        # = +3.9 C. Validated vs SKMD METAR 2019-23: raw bias -5.4, residual after
        # adjustment -1.5 C, r 0.88 (scripts/medellin_weather_validation.py).
        t2m_adjust=3.9,
        # B2 thermal valley-circulation wind-input calibration (gate PASS 2026-07-16:
        # 2023 holdout speed r +0.60, diurnal r +0.91, dir45 48.8% vs SKMD METAR).
        # rain = GPM IMERG V07 (arbitration 2026-07-21). At Medellin the shipped value is a
        # BASIN AVERAGE over 1,300-2,800 m of relief, so it exceeds the valley-floor gauge
        # (IDEAM Olaya Herrera ~1,650 mm) by design -- disclosed in the weather panel.
        # ERA5-Land tp is rejected outright: 1.8x IMERG on the SAME box = model wet bias.
        imerg=(REPO / "data/external/medellin/tier_c", "med_gpm_imerg_*.csv"),
        # ground-truth overlay on the diurnal chart (display only — never assimilated)
        network_obs=dict(path=STG2 / "medellin_perstation_v16.parquet",
                         label="SIATA network mean", min_stations=3),
        wind_calib=SHOW / "b2_wind_calibration.json",
        # full weather panel (2026-07-18): d2m + tp from the extended ERA5-Land CSVs
        # (tp de-accumulated from the since-00UTC convention). RH displayed from the
        # lapse-adjusted pair (t2m +3.9 K, dewpoint +1.1 K at ~1.8 K/km): validated
        # vs SKMD — raw-pair bias +13 % RH cancels almost exactly (hourly r 0.78,
        # diurnal r 0.94; scripts/medellin_weather_validation2.py). Rain has NO
        # gauge record in Colombian METAR (p01i all zero) — climatology-consistent
        # reanalysis, disclosed as such.
        era5_csv_dir=REPO / "data" / "external" / "medellin" / "extended_gee" / "drive",
        d2m_adjust=1.1,
        integrity=("Proving-ground reconstruction. Medellín has a dense monitoring "
                   "network, which this site deliberately withholds from the model: "
                   "the fields shown are built the way an unmonitored city's would "
                   "be, then scored against the withheld stations. Medellín is "
                   "local-emission-dominated; Kandy is regional-episodic — the "
                   "comparison proves the machinery and the value of ground data, "
                   "not that every regime is equally predictable. Hourly coverage "
                   "follows the driver archive and is incomplete in 2021-2022."),
    ),
}

CITY = "kandy"
C = CITIES[CITY]
OUT = C["out"]
EPS = 0.0                 # ventilated-hour pattern floor (additive_v3); 0 = plain v2 split


def _setup(city: str):
    global CITY, C, OUT, EPS
    CITY = city
    C = CITIES[city]
    OUT = C["out"]
    # ventilated-hour floor (additive_v3): where a per-city eps file exists AND the
    # field paths point at the v3 products, reconstruct with the floor. eps=0 makes
    # every formula collapse to the plain increment-split (v2), so other cities are
    # byte-identical.
    ef = C.get("eps_floor")
    if ef and Path(ef).exists():
        j = json.loads(Path(ef).read_text())
        # generic "eps0" (written by build_additive_field_v3 for every city), with the
        # legacy per-city key as a fallback so older eps files still load
        EPS = float(j.get("eps0", j.get(f"eps0_{city}", 0.0)))
    else:
        EPS = 0.0
    # point the terrain-transport module at this city's WindNinja library so the
    # QA wind-parity check replays the correct blend
    tt._WN_LIB_PATH = C["wind_lib"]
    tt._WN_LIB = None


# ── helpers ─────────────────────────────────────────────────────────────────
def _gzip_bytes(b: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0) as f:
        f.write(b)
    return buf.getvalue()


def _write(path: Path, data, gz=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, (dict, list)):
        b = json.dumps(data, separators=(",", ":")).encode()
    elif isinstance(data, (bytes, bytearray)):
        b = bytes(data)
    else:
        raise TypeError(type(data))
    if gz:
        b = _gzip_bytes(b)
    path.write_bytes(b)
    return len(b)


def _grid_axes(year=2022):
    d = pd.read_parquet(C["field"](year), columns=["lat", "lon"])
    return np.sort(d.lat.unique()), np.sort(d.lon.unique())


_BLH_CLIM = None


def _blh_climatology(hours):
    """(month, hour) mean BLH from the anchored years' inference grids."""
    global _BLH_CLIM
    if _BLH_CLIM is None:
        frames = []
        for y in (2019, 2020, 2021, 2022, 2023, 2024):
            fp = STG / f"inference_grid_{y}_s12451.parquet"
            if fp.exists():
                d = pd.read_parquet(fp, columns=["datetime_utc", "blh_m"])
                d["h"] = pd.to_datetime(d.datetime_utc, utc=True)
                frames.append(d.groupby("h").blh_m.mean().reset_index())
        d = pd.concat(frames)
        _BLH_CLIM = d.groupby([d.h.dt.month, d.h.dt.hour]).blh_m.mean()
    idx = pd.MultiIndex.from_arrays([hours.dt.month, hours.dt.hour])
    return _BLH_CLIM.reindex(idx).to_numpy()


def _era5land_hourly_rain(e):
    """De-accumulate ERA5-Land total_precipitation (gotcha #60).

    On GEE the ERA5-Land hourly `total_precipitation` ACCUMULATES from 00 UTC and
    resets daily, so the raw hourly value is not per-hour rain (summing it over-counts
    ~12x). Correct hourly rain = tp[h] - tp[h-1] within each UTC day, with the 00 h
    value kept as-is, floored at 0. Returned in METRES (the exporter multiplies by
    1000 for the mm display), matching the inference-grid `tp` convention.
    """
    if "total_precipitation" not in e.columns:
        return np.nan
    d = e.sort_values("h")
    day = d["h"].dt.floor("D")
    prev = d.groupby(day)["total_precipitation"].shift()
    hourly = np.where(d["h"].dt.hour == 0, d["total_precipitation"],
                      (d["total_precipitation"] - prev).fillna(d["total_precipitation"]))
    return pd.Series(np.clip(hourly, 0, None), index=d.index).reindex(e.index)


def _imerg_hourly_rain(hours):
    """GPM IMERG V07 hourly rain in METRES, aligned to `hours` (tz-aware UTC index).

    ARBITRATION (scripts/imerg_rain_arbitration.py, 2026-07-21): IMERG is the shipped
    rain source, NOT ERA5-Land tp. Even correctly de-accumulated, ERA5-Land runs ~2.1x
    (Kandy) / ~3.5x (Medellin) a national-met-service gauge and ~1.8x IMERG on the SAME
    box -- a model wet bias, not just an area-vs-floor effect. IMERG (satellite + gauge
    merged) lands at 0.98x the Sri Lanka DoM representative station (Katugastota) at
    Kandy. IMERG's `precipitation` band is a RATE in mm/hr on 30-min steps, so
    hourly mm = mean of the two rates; /1000 -> metres for the shared writer.
    """
    src = C.get("imerg")
    files = sorted(Path(src[0]).glob(src[1])) if src else []
    if not files:
        return None
    d = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    col = "precipitation" if "precipitation" in d else d.columns[-1]
    d["h"] = pd.to_datetime(d.datetime).dt.tz_localize("UTC").dt.floor("h")
    g = d.groupby("h")[col].agg(["sum", "count"])
    mm = (g["sum"] * 0.5).where(g["count"] == 2,
                                g["sum"] * 0.5 * 2 / g["count"].clip(lower=1))
    return (mm / 1000.0).reindex(hours)


def _met_from_drivers(hours):
    """Met table on the field-hours clock via nearest-merge from the city driver
    CSVs (u10, v10, t2m from ERA5-Land; blh from the zpbl export). No d2m/tp —
    the weather panel for such cities shows temperature + wind + BLH only."""
    from src.transfer_validation import drivers
    from city_config import citypack
    cp = citypack(CITY)
    w = drivers.era5_winds(cp)
    b = drivers.blh(cp)
    w["h"] = pd.to_datetime(w.datetime).dt.tz_localize("UTC")
    b["h"] = pd.to_datetime(b.datetime).dt.tz_localize("UTC")
    base = pd.DataFrame({"h": hours}).sort_values("h")
    m = pd.merge_asof(base, w.sort_values("h")[["h", "u10", "v10", "t2m"]],
                      on="h", direction="nearest", tolerance=pd.Timedelta("3h"))
    m = pd.merge_asof(m, b.sort_values("h")[["h", "blh_m"]],
                      on="h", direction="nearest", tolerance=pd.Timedelta("3h"))
    m = m.set_index("h").interpolate(limit_direction="both")
    if m["t2m"].mean() > 100:          # Kelvin → the scalars writer expects Kelvin
        pass
    else:                              # already Celsius → convert to Kelvin
        m["t2m"] = m["t2m"] + 273.15
    m["blh"] = m["blh_m"]
    # full-weather extension: d2m + hourly rain from the per-year ERA5-Land CSVs
    # (GEE ERA5-Land tp is ACCUMULATED since 00 UTC — de-accumulated here; shipped
    # as metres/hour so the shared writer's x1000-to-mm convention applies).
    if C.get("era5_csv_dir") and Path(C["era5_csv_dir"]).exists():
        frames = [pd.read_csv(f) for f in sorted(Path(C["era5_csv_dir"]).glob(
            f"{CITY}_era5land_*.csv"))]
        e = pd.concat(frames, ignore_index=True)
        e["h"] = pd.to_datetime(e.datetime).dt.tz_localize("UTC")
        e = e.sort_values("h").reset_index(drop=True)
        day = e.h.dt.floor("D")
        tp = e.total_precipitation.to_numpy()
        rain = np.diff(tp, prepend=np.nan)
        newday = day.ne(day.shift()).to_numpy()
        rain[newday] = tp[newday]
        e["tp_hr"] = np.clip(rain, 0, None)
        e = e.set_index("h")
        m["d2m"] = m.index.map(e["dewpoint_temperature_2m"])
        m["tp"] = m.index.map(e["tp_hr"])
        m[["d2m", "tp"]] = m[["d2m", "tp"]].interpolate(limit_direction="both")
    m = _apply_wind_calib(m)
    m["wspd"] = np.hypot(m.u10, m.v10)
    return m


def _prefer_imerg_rain(met):
    """Rain comes from IMERG only; hours IMERG does not cover ship NO rain at all.

    Deliberately NOT falling back to ERA5-Land tp: the arbitration rejected it (2.1x at
    Kandy, 3.5x at Medellin vs the national gauges), and a silent fallback would ship the
    rejected product on exactly the newest year, where nobody would think to check --
    which is what happened on the first run of this change (Kandy 2026 and Medellin 2024
    quietly carried ERA5 numbers ~40% high). An absent value is honest; a wrong one is not.
    """
    if not C.get("imerg"):
        return met
    im = _imerg_hourly_rain(met.index)
    have = im.notna() if im is not None else pd.Series(False, index=met.index)
    before = met["tp"].sum() * 1000.0 if "tp" in met else float("nan")
    met["tp"] = np.where(have, im, np.nan) if im is not None else np.nan
    cov = float(have.mean()) * 100.0
    if cov < 99.5:
        print(f"  rain: IMERG covers only {cov:.0f}% of hours -> the rest ship NO rain "
              f"(ERA5-Land withheld: it reads ~{before:.0f} mm and is rejected)")
    else:
        print(f"  rain: IMERG {cov:.0f}% (annual {np.nansum(met['tp'])*1000:.0f} mm; "
              f"ERA5-Land would have said {before:.0f} mm)")
    return met


def _apply_wind_calib(m):
    """B2 thermal valley-circulation wind input (gate PASS at Medellín 2026-07-16
    + method-transfer PASS at Kathmandu): replace the flat ERA5 synoptic wind with
      u' = g*u - A(lh)*sin(theta),  A(lh) = 2-harmonic diurnal (local hour).
    At cities with wind obs the params are FITTED; at Kandy they are a disclosed
    METHOD-TRANSFER PRIOR (DEM drainage axis + relief-scaled 2-city amplitude —
    scripts/b2_kandy_wind_prior.py). Everything downstream (blend params, wdir
    readout, QA parity on the SHIPPED u/v) follows consistently. Expects a
    tz-aware UTC index + u10/v10 columns; caller recomputes wspd."""
    if not (C.get("wind_calib") and Path(C["wind_calib"]).exists()):
        return m
    p = json.loads(Path(C["wind_calib"]).read_text())["params"]
    lh = (m.index.tz_convert(C["tz"]).hour).to_numpy()
    w_ = 2 * np.pi / 24.0
    A = (p["a0"] + p["a1"] * np.cos(w_ * lh) + p["b1"] * np.sin(w_ * lh)
         + p["a2"] * np.cos(2 * w_ * lh) + p["b2"] * np.sin(2 * w_ * lh))
    th = np.deg2rad(p["theta_deg"])
    u = p["gain_era5"] * m["u10"].to_numpy() - A * np.sin(th)
    v = p["gain_era5"] * m["v10"].to_numpy() - A * np.cos(th)
    m["u10"], m["v10"] = u, v
    print(f"  B2 wind calibration applied (theta {p['theta_deg']} deg, "
          f"gain {p['gain_era5']})")
    return m


def _load_year(year):
    """Return field DataFrame + aligned T,B hourly tables keyed by UTC hour."""
    d = pd.read_parquet(C["field"](year),
                        columns=["time", "lat", "lon", "pm25_q50", "pm25_q05", "pm25_q95"])
    d["h"] = pd.to_datetime(d.time, utc=True)
    B = pd.read_parquet(C["bfile"](year))
    B["h"] = pd.to_datetime(B.datetime_utc, utc=True)
    T = pd.read_parquet(C["tfile"](year))
    T["h"] = pd.to_datetime(T.datetime_utc, utc=True)
    if C["met"] == "inference":
        ig = STG / f"inference_grid_{year}_s12451.parquet"
        if ig.exists():
            m = pd.read_parquet(ig, columns=["datetime_utc", "u10", "v10", "blh_m",
                                             "wind_speed_10m", "t2m", "d2m", "tp"])
            m["h"] = pd.to_datetime(m.datetime_utc, utc=True)
            met = m.groupby("h").agg(u10=("u10", "mean"), v10=("v10", "mean"),
                                     blh=("blh_m", "mean"),
                                     wspd=("wind_speed_10m", "mean"),
                                     t2m=("t2m", "mean"), d2m=("d2m", "mean"),
                                     tp=("tp", "mean"))
        else:
            # extension years: area-mean drivers from the KandyExtGEE pull
            # (ERA5-Land carries d2m + tp, so the weather panel stays complete;
            #  tp is de-accumulated per gotcha #60 by _era5land_hourly_rain)
            e = pd.read_csv(REPO / "data/external/kandy/extended_gee/drive"
                            / f"kandy_era5land_{year}.csv").rename(columns={
                                "u_component_of_wind_10m": "u10",
                                "v_component_of_wind_10m": "v10",
                                "temperature_2m": "t2m",
                                "dewpoint_temperature_2m": "d2m"})
            e["h"] = pd.to_datetime(e.datetime).dt.tz_localize("UTC")
            e["tp"] = _era5land_hourly_rain(e)
            gfp = (REPO / "data/external/kandy/extended_gee/drive"
                   / f"kandy_geoscf_{year}.csv")
            g = pd.read_csv(gfp).rename(columns={"ZPBL": "blh"}) if gfp.exists() \
                else pd.DataFrame(columns=["datetime", "blh"])
            if len(g):
                g["h"] = pd.to_datetime(g.datetime).dt.tz_localize("UTC")
                met = e.merge(g[["h", "blh"]], on="h", how="left")
            else:
                met = e.assign(blh=np.nan)
            # BLH may be absent for the newest year (GEOS-CF GEE latency, gotcha #30).
            # It only sets the wind-regime blend weight and the display value, so fall
            # back to the (month, hour) climatology of the anchored years.
            if met.blh.isna().mean() > 0.5:
                met["blh"] = met["blh"].fillna(
                    pd.Series(_blh_climatology(met["h"]), index=met.index))
                print(f"    {year}: BLH from (month,hour) climatology "
                      f"(GEOS-CF not yet published)")
            met = met.set_index("h")[["u10", "v10", "blh", "t2m", "d2m", "tp"]]
        met = _apply_wind_calib(met)
        met["wspd"] = np.hypot(met.u10, met.v10)
        met = _prefer_imerg_rain(met)
    else:
        hours = pd.to_datetime(np.sort(d.h.unique()), utc=True)
        met = _met_from_drivers(hours)
        met = _prefer_imerg_rain(met)
    # the zero-ground-data (VanD) tier: same B, same P_local — only T differs
    V = None
    if C.get("vand_field"):
        vp = C["vand_field"](year)
        if vp.exists():
            V = pd.read_parquet(vp, columns=["time", "lat", "lon",
                                             "pm25_q50", "pm25_q05", "pm25_q95"])
            V["h"] = pd.to_datetime(V.time, utc=True)
    return d, B.set_index("h"), T.set_index("h"), met, V


def _wind_blend_params(u, v, blh, lib):
    """Replicate terrain_transport.windninja_wind index/weight math (parity-critical).

    Computed from the SAME rounded (u, v, blh) that ship in the scalars, so the shipped
    blend indices/weights are self-consistent with the shipped met (no sector-boundary
    drift between what the browser displays and what it blends)."""
    dirs, speeds = lib["dirs"], lib["speeds"]
    spd = float(np.clip(np.hypot(u, v), 0.2, 8.0))
    dfrom = float(np.degrees(np.arctan2(-u, -v)) % 360.0)
    nd = len(dirs); step = 360.0 / nd
    i0 = int(np.floor(dfrom / step)) % nd
    wd1 = ((dfrom - dirs[i0]) % 360.0) / step
    wd0 = 1.0 - wd1
    s0, s1 = float(speeds[0]), float(speeds[1])
    cs1 = (spd - s0) / (s1 - s0); cs0 = 1.0 - cs1
    wn = float(np.clip((600.0 - blh) / 600.0, 0, 1))
    return {"i0": i0, "wd0": round(wd0, 5), "cs0": round(cs0, 5), "wn": round(wn, 5)}


# ── exporters ───────────────────────────────────────────────────────────────
def export_scalars_and_plocal(year, lats, lons, lib):
    d, B, T, met, V = _load_year(year)
    hours = pd.to_datetime(np.sort(d.h.unique()), utc=True)
    ny, nx = len(lats), len(lons)
    npx = ny * nx
    # pivot field to (hour, pixel) with pixel order = row-major (lat asc, lon asc)
    idx = {(la, lo): i for i, (la, lo) in enumerate(
        [(la, lo) for la in lats for lo in lons])}
    d = d.assign(pix=[idx[(la, lo)] for la, lo in zip(d.lat, d.lon)])

    scal = {"hours_utc": [], "T": [], "B": [], "T05": [], "T95": [],
            "B_lo": [], "B_hi": [], "u10": [], "v10": [], "blh": [],
            "wspd": [], "wdir_from": [], "basin": [], "core": [],
            "t2m": [], "rh": [], "rain": [],
            "pmin": [], "pmax": [],
            "i0": [], "wd0": [], "cs0": [], "wn": []}
    has_vand = V is not None
    if has_vand:
        scal.update({"Tv": [], "Tv05": [], "Tv95": []})
        V = V.assign(pix=[idx[(la, lo)] for la, lo in zip(V.lat, V.lon)])
        vgrp = {h: g for h, g in V.groupby("h")}
    has_weather = ("d2m" in met.columns) and ("tp" in met.columns)
    if not has_weather:
        del scal["rh"], scal["rain"]        # t2m ships; RH/rain need d2m/tp
    core_pix = idx[(lats[np.argmin(np.abs(lats - C["core"][0]))],
                    lons[np.argmin(np.abs(lons - C["core"][1]))])]
    # month -> list of uint16 rows
    month_rows: dict[int, list] = {mm: [] for mm in range(1, 13)}

    grp = {h: g for h, g in d.groupby("h")}
    n_degen = 0
    for h in hours:
        g = grp[h].sort_values("pix")
        q50 = g.pm25_q50.values.astype(float)
        q05 = g.pm25_q05.values.astype(float)
        q95 = g.pm25_q95.values.astype(float)
        Bv = float(B.at[h, "B"]); Blo = float(B.at[h, "B_lo"]); Bhi = float(B.at[h, "B_hi"])
        # INCREMENT-SPLIT reconstruction (matches build_additive_field_v2, 2026-07-09):
        #   q = B + max(Tq-B,0)*P + min(Tq-B,0)
        # The split preserves the spatial mean = Tq for BOTH accumulation and ventilation
        # hours, so all three anchors are simply the spatial means. The unit-mean pattern P
        # is the ACCUMULATION-side shape, recovered from q95 when T95>B (q95 is the
        # highest quantile, so it is on the accumulation side whenever any quantile is);
        # on fully-ventilated hours (T95<=B) the field is flat and P=1.
        # When the zero-data tier ships, P is identical across tiers by construction, so
        # it is recovered from whichever tier has the larger accumulation increment
        # (better conditioning; also covers hours degenerate in one tier only).
        T50 = float(q50.mean()); T95 = float(q95.mean()); T05 = float(q05.mean())
        incA = T95 - Bv
        if has_vand:
            gv = vgrp[h].sort_values("pix")
            v50 = gv.pm25_q50.values.astype(float)
            v05 = gv.pm25_q05.values.astype(float)
            v95 = gv.pm25_q95.values.astype(float)
            Tv50 = float(v50.mean()); Tv95 = float(v95.mean()); Tv05 = float(v05.mean())
            incV = Tv95 - Bv
        else:
            incV = -np.inf
        # floor-aware P recovery: q_top = B + max(max(inc,0),EPS)*P + min(inc,0) - e,
        # e = max(0, EPS-max(inc,0)) -> P = (q_top - B - min(inc,0) + e) / max(max(inc,0),EPS).
        # With EPS=0 this is exactly (q95-B)/inc on accumulation hours (v2). With EPS>0
        # (Kandy v3) the denominator is always >= EPS > 0, so P is ALWAYS recoverable and
        # ventilated hours keep their real pattern instead of collapsing to 1.
        def _recover(qtop, inc):
            a = max(inc, 0.0); u = min(inc, 0.0); e = max(0.0, EPS - a)
            coef = max(a, EPS)
            return (qtop - Bv - u + e) / coef, coef
        if EPS > 0 or max(incA, incV) > DEGEN_TB:
            PA, cA = _recover(q95, incA)
            if has_vand:
                PV, cV = _recover(v95, incV)
                P = PA if cA >= cV else PV
            else:
                P = PA
        else:
            P = np.ones(npx); n_degen += 1

        pmin = float(np.nanmin(P)); pmax = float(np.nanmax(P))
        span = pmax - pmin
        if span < 1e-9:                       # flat P (degenerate hour)
            Pq = np.zeros(npx, dtype=np.uint16)
        else:
            Pq = np.clip(np.round((P - pmin) / span * 65535.0), 0, 65535).astype(np.uint16)
        month_rows[h.month].append(Pq)

        # met + wind blend from the ROUNDED values that ship (self-consistent, parity-safe)
        u = round(float(met.at[h, "u10"]), 3); v = round(float(met.at[h, "v10"]), 3)
        blh = round(float(met.at[h, "blh"]), 1); wspd = round(float(met.at[h, "wspd"]), 3)
        wb = _wind_blend_params(u, v, blh, lib)
        Tv = T50
        _inc = T50 - Bv
        core = (Bv + max(max(_inc, 0.0), EPS) * float(P[core_pix]) + min(_inc, 0.0)
                - max(0.0, EPS - max(_inc, 0.0)))
        scal["hours_utc"].append(int(h.value // 10**9))
        scal["T"].append(round(Tv, 3)); scal["B"].append(round(Bv, 3))
        scal["T05"].append(round(T05, 3)); scal["T95"].append(round(T95, 3))
        scal["B_lo"].append(round(Blo, 3)); scal["B_hi"].append(round(Bhi, 3))
        scal["u10"].append(u); scal["v10"].append(v)
        scal["blh"].append(blh); scal["wspd"].append(wspd)
        scal["wdir_from"].append(round(float(np.degrees(np.arctan2(-u, -v)) % 360), 1))
        # ERA5 surface weather (historical conditions panel): T in deg C, RH via
        # Magnus (Alduchov-Eskridge coefficients), rain as mm within the hour.
        tK = float(met.at[h, "t2m"])
        tc = tK - 273.15 + C.get("t2m_adjust", 0.0)
        scal["t2m"].append(round(tc, 1))
        if has_weather:
            dK = float(met.at[h, "d2m"])
            # lapse-consistent pair: dewpoint gets its own (smaller) lapse adjustment
            # so RH stays physical when t2m is adjusted to the valley floor
            dc = dK - 273.15 + C.get("d2m_adjust", 0.0)
            rh = 100.0 * np.exp(17.625 * dc / (243.04 + dc)) / np.exp(17.625 * tc / (243.04 + tc))
            scal["rh"].append(round(float(np.clip(rh, 0, 100)), 0))
            # rain may legitimately be absent (IMERG not published for this hour — see
            # _prefer_imerg_rain). Emit JSON null, NOT NaN: bare NaN is invalid JSON and
            # would break JSON.parse for the whole payload. The panel omits absent rain.
            tpv = float(met.at[h, "tp"])
            scal["rain"].append(None if not np.isfinite(tpv)
                                else round(max(tpv, 0.0) * 1000.0, 2))
        scal["basin"].append(round(float(np.nanmean(q50)), 3))
        scal["core"].append(round(core, 3))
        scal["pmin"].append(round(pmin, 5)); scal["pmax"].append(round(pmax, 5))
        for k in ("i0", "wd0", "cs0", "wn"):
            scal[k].append(wb[k])
        if has_vand:
            scal["Tv"].append(round(Tv50, 3))
            scal["Tv05"].append(round(Tv05, 3)); scal["Tv95"].append(round(Tv95, 3))

    scal.update(year=year, n_px=npx, n_lat=ny, n_lon=nx)
    nb = _write(OUT / f"scalars_{year}.json", scal)
    tot = nb
    for mm, rows in month_rows.items():
        if not rows:
            continue
        arr = np.stack(rows).astype("<u2")  # (n_hours_in_month, npx)
        tot += _write(OUT / f"plocal_{year}_{mm:02d}.bin.gz", arr.tobytes(), gz=True)
    print(f"  {year}: {len(hours)} h, {n_degen} degenerate (P=1), payload {tot/1e6:.2f} MB")
    return scal


def export_wind_library(lib_raw):
    U = lib_raw["u"].astype(np.float32)   # (16,2,2,64,64)
    V = lib_raw["v"].astype(np.float32)
    amax = float(max(np.abs(U).max(), np.abs(V).max()))
    scale = amax / 32767.0
    Uq = np.clip(np.round(U / scale), -32767, 32767).astype("<i2")
    Vq = np.clip(np.round(V / scale), -32767, 32767).astype("<i2")
    blob = np.stack([Uq, Vq]).tobytes()   # [2,16,2,2,64,64] int16
    nb = _write(OUT / "wind_library.bin.gz", blob, gz=True)
    return {"scale": scale, "shape": list(U.shape), "amax": amax,
            "lats": lib_raw["lats"].round(5).tolist(),
            "lons": lib_raw["lons"].round(5).tolist(),
            "n_bytes": nb}


def _elev_grid():
    """(lat_axis asc, lon_axis asc, elevation 2-D) from the city elevation source."""
    kind, path = C["elev"]
    if kind == "npz":
        ez = np.load(path)
        ela = ez["lat_grid"][:, 0]; elo = ez["lon_grid"][0, :]; Z = ez["elev"].astype(float)
        if ela[0] > ela[-1]:
            ela, Z = ela[::-1], Z[::-1, :]
        if elo[0] > elo[-1]:
            elo, Z = elo[:: -1], Z[:, ::-1]
        return ela, elo, Z
    import rasterio
    with rasterio.open(path) as src:
        assert src.crs and src.crs.to_epsg() == 4326, f"DEM {path} not EPSG:4326"
        Z = src.read(1).astype(float)
        Z = np.where(Z < -1000, np.nan, Z)
        tfm = src.transform
        elo = tfm.c + (np.arange(src.width) + 0.5) * tfm.a
        ela = tfm.f + (np.arange(src.height) + 0.5) * tfm.e
    if ela[0] > ela[-1]:
        ela, Z = ela[::-1], Z[::-1, :]
    # fill nodata with column means (matches the WindNinja DEM-export convention)
    if np.isnan(Z).any():
        col = np.nanmean(Z, axis=0)
        idx = np.where(np.isnan(Z))
        Z[idx] = np.take(col, idx[1])
    return ela, elo, Z


def export_static(lats, lons):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.colors import LightSource
    from PIL import Image
    from scipy.interpolate import RegularGridInterpolator

    # hillshade from the city elevation grid, resampled to the PM bbox
    ela, elo, Z = _elev_grid()
    HS_N = 512
    glat = np.linspace(lats.min(), lats.max(), HS_N)
    glon = np.linspace(lons.min(), lons.max(), HS_N)
    LA, LO = np.meshgrid(glat, glon, indexing="ij")
    zi = RegularGridInterpolator((ela, elo), Z, bounds_error=False,
                                 fill_value=None)((LA, LO))
    ls = LightSource(azdeg=315, altdeg=45)
    # dx/dy from the resampled grid spacing (m); Kandy's 100 m kept verbatim
    if C["elev"][0] == "npz":
        dxm = dym = 100
    else:
        dym = (glat[1] - glat[0]) * 111_320.0
        dxm = (glon[1] - glon[0]) * 111_320.0 * np.cos(np.deg2rad(glat.mean()))
    hs = ls.hillshade(zi, vert_exag=6, dx=dxm, dy=dym)   # 0..1, north-up render
    img = (np.clip(hs, 0, 1) * 255).astype(np.uint8)[::-1]  # PNG top row = north
    (OUT / "static").mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, mode="L").save(OUT / "static" / "hillshade.png")

    # per-pixel fields on the PM grid: elevation, population, S_traffic
    LA16, LO16 = np.meshgrid(lats, lons, indexing="ij")
    elev16 = RegularGridInterpolator((ela, elo), Z, bounds_error=False,
                                     fill_value=None)((LA16, LO16))
    if C["pop"] is not None:
        pop = np.load(C["pop"])
        pla, plo, pgrid = pop["lats"], pop["lons"], pop["pop"].astype(float)
        if pla[0] > pla[-1]:
            pla, pgrid = pla[::-1], pgrid[::-1, :]
        pop16 = RegularGridInterpolator((pla, plo), pgrid, bounds_error=False,
                                        fill_value=0.0)((LA16, LO16))
        pop_out = np.round(pop16, 1).tolist()
    else:
        pop_out = None
    sp, klat, klon, karr = C["straffic"]
    st = np.load(sp)
    Sfl, Sfo, Ef = st[klat], st[klon], st[karr].astype(float)
    if Sfl[0] > Sfl[-1]:
        Sfl, Ef = Sfl[::-1], Ef[::-1, :]
    Slog = np.log1p(4.0 * np.clip(Ef, 0, None)); Slog /= (Slog.max() + 1e-9)
    S16 = RegularGridInterpolator((Sfl, Sfo), Slog, bounds_error=False,
                                  fill_value=0.0)((LA16, LO16))
    _write(OUT / "static" / "fields.json", {
        "lats": lats.round(5).tolist(), "lons": lons.round(5).tolist(),
        "elev": np.round(elev16, 1).tolist(),
        "pop": pop_out,
        "s_traffic": np.round(S16, 4).tolist()})

    # emission contour polylines from the fine surface (for a crisp overlay)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    cs = ax.contour(Sfo, Sfl, Slog, levels=[0.3, 0.5, 0.7, 0.85])
    contours = []
    for lev, segs in zip(cs.levels, cs.allsegs):
        for seg in segs:
            if len(seg) >= 4:
                contours.append({"level": float(lev),
                                 "pts": np.round(seg[::2], 5).tolist()})
    plt.close(fig)
    _write(OUT / "static" / "emission.json", {"contours": contours})

    # OSM vectors (simplify by decimation; keep only what renders well small)
    layers = {}
    for name, keep in [("roads", 3), ("rivers", 1), ("water", 1), ("places", 1)]:
        fp = C["osm"] / f"{name}.geojson"
        if not fp.exists():
            continue
        gj = json.loads(fp.read_text(encoding="utf-8"))
        feats = []
        # road hierarchy rank (r): 3 = trunk/motorway/primary, 2 = secondary,
        # 1 = tertiary/other. Lets the renderer draw a proper visual hierarchy
        # (major roads wider + lighter) instead of one flat weight — the single
        # biggest thing that reads as "amateur map" vs "professional map".
        RANK = {"motorway": 3, "trunk": 3, "primary": 3, "secondary": 2,
                "tertiary": 1, "residential": 1, "unclassified": 1}
        for ft in gj.get("features", []):
            geom = ft.get("geometry") or {}
            gt = geom.get("type"); co = geom.get("coordinates")
            hw = (ft.get("properties") or {}).get("highway", "")
            rank = RANK.get(hw, 1) if name == "roads" else None
            if gt == "Point":
                feats.append({"t": "pt", "c": [round(co[0], 5), round(co[1], 5)],
                              "n": (ft.get("properties") or {}).get("name", "")})
            elif gt in ("LineString", "Polygon", "MultiLineString", "MultiPolygon"):
                def dec(line):
                    return [[round(x, 5), round(y, 5)] for x, y in line[::keep]]
                if gt == "LineString":
                    f = {"t": "ln", "c": dec(co)}
                    if rank: f["r"] = rank
                    feats.append(f)
                elif gt == "Polygon":
                    feats.append({"t": "pg", "c": [dec(r) for r in co]})
                elif gt == "MultiLineString":
                    for line in co:
                        f = {"t": "ln", "c": dec(line)}
                        if rank: f["r"] = rank
                        feats.append(f)
                else:
                    for poly in co:
                        feats.append({"t": "pg", "c": [dec(r) for r in poly]})
        layers[name] = feats
    layers["landmarks"] = [{"n": p["n"], "c": [p["lon"], p["lat"]], "k": p["k"]}
                           for p in C["landmarks"]]
    _write(OUT / "static" / "layers.json", layers)
    print(f"  static: hillshade {HS_N}x{HS_N}, "
          f"{sum(len(v) for v in layers.values())} vectors, "
          f"{len(contours)} contour segs")


def export_health_and_fect():
    hb = pd.read_csv(DEC / "health_burden.csv")
    ew = pd.read_csv(DEC / "exposure_weighting.csv")
    # the current partition (post coherence cap; F.43/F.133), never the retired v1 additive_partition.csv
    _pp = DEC / "kandy_partition_v2.json"
    ap = (pd.DataFrame([{"year": r["year"], "local_pct": 100 * r["local_frac"]}
                        for r in json.load(open(_pp, encoding="utf-8"))["per_year"]]) if _pp.exists() else None)
    health = {"per_year": {}, "burden_note": ""}
    for _, r in ew.iterrows():
        y = int(r.year)
        health["per_year"][y] = {
            "area_mean": round(float(r.area_mean), 2),
            "pop_weighted": round(float(r.dynamic), 2),
            "core": round(float(r.core), 2)}
    for _, r in hb.iterrows():
        y = int(r.year)
        health["per_year"].setdefault(y, {})
        # The attributable-death estimate is WITHDRAWN (thesis Appendix I, ledger F.126 addendum): it needs
        # age-specific mortality, a settled level and propagated uncertainty. Only population is exported.
        health["per_year"][y].update({
            "population": int(r.population),
            "dynamic_exposure": round(float(r.dynamic_exposure), 2)})
        health["burden_note"] = "withdrawn"
    if ap is not None:
        for _, r in ap.iterrows():
            y = int(r.year)
            if y in health["per_year"]:
                health["per_year"][y]["local_pct"] = round(float(r.local_pct), 1)
    _write(OUT / "health.json", health)

    fe = pd.read_parquet(STG / "dataset_v3_hourly.parquet",
                         columns=["datetime_utc", "sensor_id", "pm25_observed"])
    fe["loct"] = pd.to_datetime(fe.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo")
    fe = fe[(fe.sensor_id == 12451)].dropna(subset=["pm25_observed"])
    for y in C["years"]:
        sub = fe[fe.loct.dt.year == y]
        rec = [{"d": d.strftime("%Y-%m-%d"), "h": int(h), "v": round(float(v), 1)}
               for (d, h), v in
               sub.groupby([sub.loct.dt.floor("D"), sub.loct.dt.hour]).pm25_observed.mean().items()]
        # extension years may have little/no FECT coverage (2025 = 1 h) — still write
        # the file so the client fetch never 404s; the panel simply shows no dots.
        _write(OUT / f"fect_{y}.json", {"year": y, "sensor": "Akurana 12451",
                                        "obs": rec})
    print(f"  health.json + FECT overlays ({len(fe):,} obs)")


def export_network_obs():
    """Per-year hourly NETWORK-MEAN observations, in the same shape as the FECT overlay,
    so a monitored city can show its own ground truth beside the reconstruction.

    This is display only — it is the proving ground's whole point (the reveal already
    scores against these). It does NOT feed assimilation, so the holdout stations stay
    holdout; the exporter never reads this file back."""
    src = C.get("network_obs")
    if not src:
        return
    g = pd.read_parquet(src["path"], columns=["datetime_utc", "station_id", "pm25"])
    g = g.dropna(subset=["pm25"])
    g["loct"] = pd.to_datetime(g.datetime_utc, utc=True).dt.tz_convert(C["tz"])
    for y in C["years"]:
        sub = g[g.loct.dt.year == y]
        # network mean per (day, hour): a single robust curve, not 20 noisy ones
        agg = sub.groupby([sub.loct.dt.floor("D"), sub.loct.dt.hour]).pm25.agg(
            ["mean", "count"])
        rec = [{"d": d.strftime("%Y-%m-%d"), "h": int(h), "v": round(float(r["mean"]), 1)}
               for (d, h), r in agg.iterrows() if r["count"] >= src.get("min_stations", 3)]
        _write(OUT / f"fect_{y}.json",
               {"year": y, "sensor": src.get("label", "network mean"), "obs": rec})
    print(f"  network-obs overlays ({len(g):,} station-hours)")


def export_showcase():
    """Medellín proving-ground payloads from the showcase artifacts."""
    # stations: the per-station reveal (model vs measured, roles, coords)
    rv = pd.read_csv(SHOW / "act1_per_station_reveal.csv")
    h6 = json.load(open(SHOW / "holdout6.json"))
    stations = [{"id": str(r.station_id), "lat": round(float(r.lat), 5),
                 "lon": round(float(r.lon), 5), "role": str(r.role),
                 "model": round(float(r.model), 2), "measured": round(float(r.measured), 2),
                 "n": int(r.n)} for _, r in rv.iterrows()]
    _write(OUT / "stations.json", {
        "stations": stations, "holdout6": [str(s) for s in h6["holdout6"]],
        "anchors": [str(s) for s in h6["anchors"]],
        "note": ("Long-term mean, model vs measured, per station. Roles: anchor = "
                 "the 2 elevation-gradient stations the sensor-tier T(t) uses; "
                 "holdout = the fixed 6-station test set (never used by any tier); "
                 "vault = other withheld stations used only for scoring.")})

    # showcase scorecard: Act 0 (zero ground data) vs Act 1 (2-sensor), both test sets
    sc = pd.read_csv(SHOW / "act0_act1_scorecard.csv")
    per_year = pd.read_csv(SHOW / "act_ladder_per_year_level.csv") \
        if (SHOW / "act_ladder_per_year_level.csv").exists() else None
    _write(OUT / "showcase.json", {
        "scorecard": sc.round(3).to_dict(orient="records"),
        "per_year_level": (per_year.round(2).to_dict(orient="records")
                           if per_year is not None else []),
    })

    # forecast scoreboard: daily means for the chart + hourly-based skill stats
    fc = pd.read_csv(STG / "training" / "forecast_series_medellin_2023.csv")
    fc["valid"] = pd.to_datetime(fc["valid"])
    ok = fc.dropna(subset=["obs", "T_fcst", "persist"])
    rmse = lambda a, b: float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))
    r_f = rmse(ok.T_fcst, ok.obs); r_p = rmse(ok.persist, ok.obs)
    r_raw = rmse(ok.raw_fcst, ok.obs) if "raw_fcst" in ok else None
    daily = fc.set_index("valid").resample("D")[["obs", "T_fcst", "persist", "T_anal"]].mean()
    daily = daily.dropna(how="all")
    _write(OUT / "forecast.json", {
        "year": 2023,
        "days": [d.strftime("%Y-%m-%d") for d in daily.index],
        "obs": [None if pd.isna(v) else round(float(v), 2) for v in daily.obs],
        "fcst": [None if pd.isna(v) else round(float(v), 2) for v in daily.T_fcst],
        "persist": [None if pd.isna(v) else round(float(v), 2) for v in daily.persist],
        "skill": {"rmse_forecast": round(r_f, 2), "rmse_persistence": round(r_p, 2),
                  "rmse_raw_geoscf": (round(r_raw, 2) if r_raw is not None else None),
                  "skill_vs_persistence": round(1.0 - r_f / r_p, 2),
                  "n_hours": int(len(ok))},
        "note": ("Day-ahead forecast driven by archived GEOS-CF forecast fields, "
                 "scored against 15 held-out stations (2023). Skill = 1 - "
                 "RMSE(forecast)/RMSE(24h persistence)."),
    })

    # data-value slider payload (produced by medellin_data_value_curve.py --export-webapp)
    dv = json.loads((SHOW / "datavalue_webapp.json").read_text(encoding="utf-8"))
    _write(OUT / "datavalue.json", dv)
    print(f"  showcase: {len(stations)} stations, forecast {len(daily)} days "
          f"(skill +{1 - r_f / r_p:.2f}), datavalue tiers {list(dv['tiers'].keys())}")


# ── QA gate ─────────────────────────────────────────────────────────────────
def qa_gate(lats, lons, lib_raw, wmeta, n_samples=500, tol_pm=0.25, tol_wind=0.05):
    print("\n=== QA GATE ===")
    npx = len(lats) * len(lons)
    rng = np.random.default_rng(7)
    # wind: rebuild from library blob + blend params, compare windninja_wind
    blob = gzip.decompress((OUT / "wind_library.bin.gz").read_bytes())
    UV = np.frombuffer(blob, dtype="<i2").astype(float).reshape([2] + wmeta_shape(wmeta))
    Ulib, Vlib = UV[0] * wmeta["scale"], UV[1] * wmeta["scale"]
    worst_pm = 0.0; worst_wind = 0.0; n_pm = 0
    for year in C["years"]:
        scal = json.loads((OUT / f"scalars_{year}.json").read_text())
        hours = pd.to_datetime(np.array(scal["hours_utc"]) * 10**9, utc=True)
        d = pd.read_parquet(C["field"](year),
                            columns=["time", "lat", "lon", "pm25_q50", "pm25_q05", "pm25_q95"])
        d["h"] = pd.to_datetime(d.time, utc=True)
        idx = {(la, lo): i for i, (la, lo) in enumerate(
            [(la, lo) for la in lats for lo in lons])}
        d["pix"] = [idx[(la, lo)] for la, lo in zip(d.lat, d.lon)]
        has_vand = "Tv" in scal
        if has_vand:
            dv = pd.read_parquet(C["vand_field"](year),
                                 columns=["time", "lat", "lon",
                                          "pm25_q50", "pm25_q05", "pm25_q95"])
            dv["h"] = pd.to_datetime(dv.time, utc=True)
            dv["pix"] = [idx[(la, lo)] for la, lo in zip(dv.lat, dv.lon)]
        # cache month plocal arrays lazily
        pl_cache = {}

        def plocal_row(mm, hi):
            if mm not in pl_cache:
                raw = gzip.decompress((OUT / f"plocal_{year}_{mm:02d}.bin.gz").read_bytes())
                pl_cache[mm] = np.frombuffer(raw, dtype="<u2").reshape(-1, npx)
            return pl_cache[mm][hi]

        # month -> local hour-index mapping
        month_hi = {}
        for gi, h in enumerate(hours):
            month_hi.setdefault(h.month, []).append((gi, h))
        # sample
        sample_gi = rng.choice(len(hours), size=min(n_samples, len(hours)), replace=False)
        for gi in sample_gi:
            h = hours[gi]
            mm = h.month
            # local index within month = position of gi among that month's hours
            local_i = [x[0] for x in month_hi[mm]].index(gi)
            pmin, pmax = scal["pmin"][gi], scal["pmax"][gi]
            span = pmax - pmin
            Prow = pmin + plocal_row(mm, local_i).astype(float) / 65535.0 * span
            Bv = scal["B"][gi]
            g = d[d.h == h].sort_values("pix")
            pj = rng.integers(0, npx)
            gp = g[g.pix == pj]
            if gp.empty:
                continue

            def rec(Tq):                       # floor-aware increment-split reconstruction
                inc = Tq - Bv
                return (Bv + max(max(inc, 0.0), EPS) * Prow[pj] + min(inc, 0.0)
                        - max(0.0, EPS - max(inc, 0.0)))

            tiers = [(scal["T"][gi], scal["T05"][gi], scal["T95"][gi], gp)]
            if has_vand:
                gvp = dv[(dv.h == h) & (dv.pix == pj)]
                if not gvp.empty:
                    tiers.append((scal["Tv"][gi], scal["Tv05"][gi], scal["Tv95"][gi], gvp))
            for Tv_, T05_, T95_, gref in tiers:
                rec_q50 = max(rec(Tv_), 0.0); rec_q05 = max(rec(T05_), 0.0)
                rec_q95 = max(rec(T95_), 0.0)
                e = max(abs(rec_q50 - max(gref.pm25_q50.iloc[0], 0)),
                        abs(rec_q05 - max(gref.pm25_q05.iloc[0], 0)),
                        abs(rec_q95 - max(gref.pm25_q95.iloc[0], 0)))
                worst_pm = max(worst_pm, e); n_pm += 1
            # wind parity (subsample)
            if rng.random() < 0.2:
                i0 = scal["i0"][gi]; i1 = (i0 + 1) % wmeta["shape"][0]
                wd0 = scal["wd0"][gi]; wd1 = 1 - wd0
                cs0 = scal["cs0"][gi]; cs1 = 1 - cs0
                wn = scal["wn"][gi]; wday = 1 - wn

                def blend(A):
                    return sum(wdv * csv * (wn * A[di, si, 0] + wday * A[di, si, 1])
                               for di, wdv in ((i0, wd0), (i1, wd1))
                               for si, csv in ((0, cs0), (1, cs1)))
                Uj = blend(Ulib); Vj = blend(Vlib)
                ref = tt.windninja_wind(scal["u10"][gi], scal["v10"][gi], scal["blh"][gi])
                if ref is not None:
                    worst_wind = max(worst_wind, float(np.abs(Uj - ref[0]).max()),
                                     float(np.abs(Vj - ref[1]).max()))
    print(f"  reconstruction: worst |err| = {worst_pm:.4f} ug/m3  over {n_pm} samples "
          f"(tol {tol_pm})  -> {'PASS' if worst_pm <= tol_pm else 'FAIL'}")
    print(f"  wind blend parity: worst |err| = {worst_wind:.4f} m/s  (tol {tol_wind})  "
          f"-> {'PASS' if worst_wind <= tol_wind else 'FAIL'}")
    ok = worst_pm <= tol_pm and worst_wind <= tol_wind
    print(f"  GATE: {'PASS' if ok else 'FAIL'}")
    return ok


def wmeta_shape(wmeta):
    return wmeta["shape"]


def export_meta(lats, lons, wmeta):
    meta = {
        "title": C["title"],
        "years": C["years"], "tz": C["tz"],
        "grid": {"n_lat": len(lats), "n_lon": len(lons),
                 "lats": lats.round(5).tolist(), "lons": lons.round(5).tolist(),
                 "bbox": [float(lons.min()), float(lats.min()),
                          float(lons.max()), float(lats.max())]},
        "plocal": {"quant": "per-hour min/max in scalars_{year}.json (pmin,pmax)"},
        "eps_floor": round(EPS, 4),           # additive_v3 ventilated-hour floor (0 = v2)
        "wind": wmeta,
        "scale": {"who_it1": 35, "who_it2": 25, "who_it3": 15, "who_aqg5": 5,
                  "episode_pm": 35.0},
        "episodes": C["episodes"], "landmarks":
            [{"n": p["n"], "c": [p["lon"], p["lat"]], "k": p["k"]} for p in C["landmarks"]],
        "credits": C["credits"],
        "integrity": C["integrity"],
    }
    # wind-input provenance shown in the weather panel (honest method-transfer flag)
    if C.get("wind_note"):
        meta["wind_note"] = C["wind_note"]
    # per-year provenance so the UI can flag extension years honestly
    if C.get("tiers"):
        meta["tiers"] = C["tiers"]
        meta["tier_note"] = C.get("tier_note", "")
    _write(OUT / "meta.json", meta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="kandy", choices=sorted(CITIES))
    ap.add_argument("--qa-only", action="store_true")
    ap.add_argument("--skip-qa", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _setup(a.city)
    lats, lons = _grid_axes(C["years"][-2])
    lib_raw = np.load(C["wind_lib"], allow_pickle=True)
    lib = {"dirs": lib_raw["dirs"], "speeds": lib_raw["speeds"],
           "u": lib_raw["u"], "v": lib_raw["v"]}
    global wmeta
    if a.qa_only:
        wmeta = json.loads((OUT / "meta.json").read_text())["wind"]
        ok = qa_gate(lats, lons, lib_raw, wmeta)
        sys.exit(0 if ok else 1)
    print(f"Exporting {C['title']} payload -> {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    wmeta = export_wind_library(lib_raw)
    print("  wind_library.bin.gz written")
    for y in C["years"]:
        export_scalars_and_plocal(y, lats, lons, lib)
    export_static(lats, lons)
    if C["health"] or C["fect"]:
        export_health_and_fect()
    export_network_obs()
    if C["showcase"]:
        export_showcase()
    export_meta(lats, lons, wmeta)
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"  TOTAL payload: {total/1e6:.2f} MB")
    if not a.skip_qa:
        ok = qa_gate(lats, lons, lib_raw, wmeta)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
