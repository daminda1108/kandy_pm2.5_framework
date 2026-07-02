"""city_config.py — per-city configuration for the generalised production+validation
pipeline (the Xichang treatment, applied to any monitored analogue city).

Each entry carries the city-specific data the model needs swapped: domain box,
timezone, UTM zone, DEM, score years, local-fraction f, confinement κ, and the
emission-timing source mix (vehicular vs residential/biomass). The transfer_validation
CityPack is built from this (no edit to the frozen registry).
"""
from __future__ import annotations
import numpy as np
from src.transfer_validation.citypack import CityPack

# emission profiles (local hour 0..23), each normalised to mean 1 downstream
E_TRAFFIC = np.array([0.40, 0.30, 0.25, 0.25, 0.35, 0.60, 1.00, 1.65, 1.75, 1.45,
                      1.25, 1.20, 1.20, 1.20, 1.25, 1.35, 1.50, 1.70, 1.60, 1.35,
                      1.00, 0.75, 0.55, 0.45])
E_HEATING = np.array([0.55, 0.45, 0.40, 0.40, 0.45, 0.65, 0.95, 1.10, 0.95, 0.75,
                      0.65, 0.65, 0.70, 0.70, 0.80, 0.95, 1.25, 1.65, 2.05, 2.15,
                      2.00, 1.55, 1.00, 0.70])
# agricultural/biomass burning: afternoon-peaked (fires lit midday→evening; Crippa AWB)
E_BURNING = np.array([0.30, 0.25, 0.20, 0.20, 0.25, 0.35, 0.55, 0.80, 1.05, 1.25,
                      1.45, 1.60, 1.75, 1.85, 1.90, 1.85, 1.70, 1.45, 1.15, 0.90,
                      0.70, 0.55, 0.45, 0.35])


def emission_profile(vehic, heat, burn):
    e = vehic * E_TRAFFIC + heat * E_HEATING + burn * E_BURNING
    return e / e.mean()


CITIES = {
    "xichang": dict(
        name="Xichang", cen=(27.894, 102.264), tz="Asia/Shanghai", utm="EPSG:32648",
        box=(27.770, 27.950, 102.160, 102.360), dem="xichang_srtm_dem.tif",
        years=list(range(2020, 2026)), f=0.68, kappa=0.05, regime="local-dominated",
        emix=dict(vehic=0.30, heat=0.70, burn=0.0),
        labels=[("Qionghai\nLake", 27.805, 102.295, "lake"),
                ("LUSHAN\n(2317 m)", 27.82, 102.225, "mtn")],
        inset=(97, 108, 22, 34, "SICHUAN")),
    "chiangmai": dict(
        name="Chiang Mai", cen=(18.809, 98.980), tz="Asia/Bangkok", utm="EPSG:32647",
        box=(18.719, 18.899, 98.890, 99.070), dem="chiangmai_dem.tif",
        years=list(range(2021, 2026)), f=0.40, kappa=0.08,
        regime="transboundary biomass-smoke (Kandy analog)",
        emix=dict(vehic=0.35, heat=0.10, burn=0.55),     # March burning season
        labels=[("Ping R.\nvalley", 18.79, 98.99, "lake"),
                ("Doi Suthep\n(1676 m)", 18.81, 98.92, "mtn")],
        inset=(97.5, 100.5, 17.5, 20.5, "N. THAILAND")),
    "bazhou": dict(
        name="Bazhong (Sichuan)", cen=(31.858, 106.762), tz="Asia/Shanghai", utm="EPSG:32648",
        box=(31.768, 31.948, 106.672, 106.852), dem="bazhou_srtm_dem.tif",
        years=list(range(2019, 2026)), f=0.58, kappa=0.06, regime="local-dominated valley",
        emix=dict(vehic=0.45, heat=0.55, burn=0.0),
        labels=[("Ba R.", 31.86, 106.76, "lake")],
        inset=(103, 110, 28, 34, "SICHUAN")),
    "chandigarh": dict(
        name="Chandigarh", cen=(30.744, 76.769), tz="Asia/Kolkata", utm="EPSG:32643",
        box=(30.654, 30.834, 76.679, 76.859), dem="chandigarh_srtm_dem.tif",
        years=list(range(2019, 2026)), f=0.30, kappa=0.02,
        regime="Indo-Gangetic plain, flat, transboundary haze",
        emix=dict(vehic=0.45, heat=0.15, burn=0.40),     # Oct–Nov stubble burning
        labels=[("Shivalik foothills", 30.81, 76.82, "mtn")],
        inset=(74, 80, 28, 33, "N. INDIA")),
    "kathmandu": dict(
        name="Kathmandu Valley", cen=(27.717, 85.324), tz="Asia/Kathmandu", utm="EPSG:32645",
        box=(27.620, 27.800, 85.240, 85.420), dem="kathmandu_srtm_30m.tif",
        years=[2024, 2025], f=0.78, kappa=0.11,           # closed intermontane bowl
        regime="intermontane bowl, local-dominated (brick kilns + traffic)",
        emix=dict(vehic=0.40, heat=0.10, burn=0.50),      # brick kilns + garbage/biomass (Nov–Apr)
        labels=[("Bagmati R.", 27.690, 85.310, "lake"),
                ("Shivapuri hills\n(~2700 m)", 27.795, 85.360, "mtn")],
        inset=(84, 87, 26.5, 29.5, "NEPAL")),
    "baoji": dict(
        name="Baoji (Wei R. valley, Shaanxi)", cen=(34.348, 107.193), tz="Asia/Shanghai",
        utm="EPSG:32648", box=(34.272, 34.406, 107.041, 107.421), dem="baoji_srtm_dem.tif",
        years=list(range(2019, 2026)), f=0.62, kappa=0.06, regime="local-dominated valley",
        emix=dict(vehic=0.35, heat=0.65, burn=0.0),       # N. China winter heating
        labels=[("Wei R.", 34.35, 107.19, "lake")],
        inset=(104, 111, 32, 37, "SHAANXI")),
    "taian": dict(
        name="Tai'an (foot of Mt Tai, Shandong)", cen=(36.188, 117.106), tz="Asia/Shanghai",
        utm="EPSG:32650", box=(36.100, 36.257, 117.001, 117.211), dem="taian_srtm_dem.tif",
        years=list(range(2019, 2026)), f=0.58, kappa=0.06, regime="local-dominated valley",
        emix=dict(vehic=0.45, heat=0.55, burn=0.0),
        labels=[("Mt Tai\n(1545 m)", 36.25, 117.10, "mtn")],
        inset=(114, 120, 34, 38, "SHANDONG")),
    "yichang": dict(
        name="Yichang (Yangtze valley, Hubei)", cen=(30.686, 111.333), tz="Asia/Shanghai",
        utm="EPSG:32649", box=(30.552, 30.812, 111.233, 111.491), dem="yichang_srtm_dem.tif",
        years=list(range(2019, 2026)), f=0.60, kappa=0.06, regime="local-dominated valley",
        emix=dict(vehic=0.45, heat=0.55, burn=0.0),
        labels=[("Yangtze R.", 30.69, 111.29, "lake")],
        inset=(109, 114, 29, 32, "HUBEI")),
    "medellin": dict(
        name="Medellín (Aburrá Valley, Colombia)", cen=(6.244, -75.581), tz="America/Bogota",
        utm="EPSG:32618", box=(6.150, 6.390, -75.680, -75.460), dem="medellin_dem.tif",
        years=list(range(2019, 2024)), f=0.80, kappa=0.06,
        regime="tropical Andean valley (traffic-dominated)",
        emix=dict(vehic=0.85, heat=0.0, burn=0.15),   # equatorial: traffic + some industry, no heating
        labels=[("R. Medellín", 6.24, -75.57, "lake")],
        inset=(-79, -72, 2, 9, "COLOMBIA")),
}


def cfg(slug):
    return CITIES[slug]


def citypack(slug):
    c = CITIES[slug]
    return CityPack(slug=slug, name=c["name"], role="primary", f_local=c["f"],
                    f_bracket=(max(c["f"] - 0.15, 0.1), min(c["f"] + 0.15, 0.9)),
                    score_years=tuple(c["years"]), anchor_mode="draws",
                    terrain_npz_name=f"{slug}_terrain_core.npz")


def e_profile(slug):
    return emission_profile(**CITIES[slug]["emix"])
