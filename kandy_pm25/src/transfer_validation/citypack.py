"""citypack.py — per-city configuration for the transfer-validation workstream.

A CityPack bundles everything the Kandy-twin protocol needs to run the additive
decomposition at one analogue city: where its data lives, its frozen Phase-0
constants (local-fraction bracket, scoring window, regime role), and its spatial
domain. Geometry is DERIVED from on-disk artifacts, never hardcoded:

  * domain bbox  ← bounds of the station-footprint terrain NPZ (lat_grid/lon_grid)
  * centre       ← midpoint of that bbox
  * stations     ← the per-station parquet (auto-resolves newest available version)

so a CityPack cannot drift out of sync with the rasters it is paired with, and a
typo'd coordinate is impossible. The frozen scalars (f-bracket, score years, role)
come from docs/transfer_validation_phase0_prereg_2026-06-10.md and must only change
via a dated amendment there.

Per-station parquet schema (gotcha-verified via convcnp_loader.py):
  datetime_utc, location_id, station_id, station_name, provider, sensor_type,
  lat, lon, pm25_raw, pm25 (calibrated obs), c_prior, c_prior_scaled,
  u10, v10, t2m, blh, blh_norm  [+ road_density/ntl_log (v13), ssr_norm/no2_norm (v15)]
Terrain NPZ keys: lat_grid (lat,lon), lon_grid (lat,lon), delta_z (lat,lon).

This module is read-only over the data; it resolves and validates paths and
exposes lazy accessors. It does NOT run any model step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[2]          # → kandy_pm25/
STG2 = REPO / "data" / "processed" / "stage2"
PIN = REPO / "data" / "processed" / "pinn_inputs"
VAND = REPO / "data" / "raw" / "van_donkelaar"

# Van Donkelaar V6 Asia tile (lon 65–145E, lat −10–60N) — covers all S-Asia/China
# panel cities (V6GL02.04, the project's held vintage). Medellin uses the SA tile
# from the AWS satpmdata open bucket, which ships the successor V6GL03 — a minor
# version difference, acceptable for the NEGATIVE CONTROL (the must-fail spatial
# test does not hinge on VanD minor version) and documented here.
VAND_ASIA = VAND / "V6GL02.04.CNNPM25.AS.{year}01-{year}12.nc"
VAND_SA = VAND / "V6GL03.CNNPM25.SA.{year}01-{year}12.nc"

# Per-station parquet version preference (newest schema first).
_PARQUET_VARIANTS = ("_perstation_v15", "_perstation_v13", "_perstation_v14",
                     "_stage3_perstation", "_combined_perstation")


@dataclass
class CityPack:
    """One analogue city's transfer-validation configuration.

    Frozen scalars are Phase-0 pre-registered; geometry is derived on access.
    """
    slug: str
    name: str
    role: str                       # primary | secondary | negative_control | confinement_test | reference
    f_local: float                  # point estimate of the LOCAL fraction
    f_bracket: tuple[float, float]  # admissible range (gate V6)
    score_years: tuple[int, ...]
    # provenance one-liner for the f bracket (kept with the number, audit trail)
    f_basis: str = ""
    # anchor selection mode (prereg §4 + Amendment 2):
    #   "draws"         — R=5 distinct random pairs from the eligible pool
    #   "fixed_longest" — the 2 longest-record stations, deterministic (the city's
    #                     own "FECT pair"; used where only ~2 long-record stations
    #                     exist and the dense network is recent, e.g. Kathmandu)
    anchor_mode: str = "draws"
    # explicit overrides (default None → derive / auto-resolve)
    terrain_npz_name: Optional[str] = None
    notes: str = ""

    # ---- path resolution ------------------------------------------------
    def station_parquet(self) -> Path:
        """Newest available per-station parquet for this city."""
        for v in _PARQUET_VARIANTS:
            p = STG2 / f"{self.slug}{v}.parquet"
            if p.exists():
                return p
        raise FileNotFoundError(
            f"no per-station parquet for {self.slug} (tried {_PARQUET_VARIANTS})")

    def terrain_npz(self) -> Path:
        name = self.terrain_npz_name or f"{self.slug}_terrain_stations.npz"
        return PIN / name

    def road_npz(self) -> Path:
        return PIN / f"{self.slug}_road_kernel_stations_100m.npz"

    def ntl_npz(self) -> Path:
        return PIN / f"{self.slug}_viirs_ntl_stations.npz"

    def vand_tile(self, year: int) -> Optional[Path]:
        """VanD annual tile for the year, or None if not held."""
        tmpl = VAND_SA if self.slug == "medellin" else VAND_ASIA
        p = Path(str(tmpl).format(year=year))
        return p if p.exists() else None

    # ---- derived geometry (lazy; reads the terrain NPZ) -----------------
    def bbox(self) -> dict:
        """Domain bbox derived from the station-footprint terrain raster bounds."""
        import numpy as np
        z = np.load(self.terrain_npz(), allow_pickle=True)
        lat = np.asarray(z["lat_grid"], dtype=float)
        lon = np.asarray(z["lon_grid"], dtype=float)
        return {"lat_min": float(lat.min()), "lat_max": float(lat.max()),
                "lon_min": float(lon.min()), "lon_max": float(lon.max())}

    def centre(self) -> tuple[float, float]:
        b = self.bbox()
        return (0.5 * (b["lat_min"] + b["lat_max"]),
                0.5 * (b["lon_min"] + b["lon_max"]))

    def stations(self):
        """All stations (station_id, lat, lon) — the full network before vaulting."""
        import pandas as pd
        df = pd.read_parquet(self.station_parquet(),
                             columns=["station_id", "lat", "lon"])
        return (df.dropna(subset=["lat", "lon"])
                  .groupby("station_id")[["lat", "lon"]].first()
                  .reset_index())

    # ---- readiness ------------------------------------------------------
    def check(self) -> dict:
        """File-existence + derived-geometry report (no model run). Read-only."""
        rep = {"slug": self.slug, "role": self.role, "f": self.f_local,
               "f_bracket": self.f_bracket, "score_years": self.score_years}
        try:
            rep["station_parquet"] = self.station_parquet().name
            st = self.stations()
            rep["n_stations"] = int(len(st))
        except Exception as e:  # noqa: BLE001 — readiness probe, report not raise
            rep["station_parquet"] = f"MISSING ({e})"
            rep["n_stations"] = -1
        for label, fn in (("terrain", self.terrain_npz), ("road", self.road_npz),
                          ("ntl", self.ntl_npz)):
            rep[label] = "ok" if fn().exists() else "MISSING"
        try:
            b = self.bbox()
            c = self.centre()
            rep["centre"] = (round(c[0], 4), round(c[1], 4))
            rep["bbox"] = {k: round(v, 4) for k, v in b.items()}
            rep["span_km"] = (round(111.0 * (b["lat_max"] - b["lat_min"]), 1),
                              round(111.0 * (b["lon_max"] - b["lon_min"]), 1))
        except Exception as e:  # noqa: BLE001
            rep["centre"] = f"MISSING ({e})"
        vt = self.vand_tile(self.score_years[0])
        rep["vand"] = (vt.name if vt else "NOT HELD (NA tile)")
        return rep


# ─────────────────────────────────────────────────────────────────────────
# REGISTRY — Phase-0 frozen (docs/transfer_validation_phase0_prereg_2026-06-10.md)
# ─────────────────────────────────────────────────────────────────────────
REGISTRY: dict[str, CityPack] = {
    "xichang": CityPack(
        slug="xichang", name="Xichang (Anning R. valley, Sichuan)",
        role="primary", f_local=0.68, f_bracket=(0.55, 0.80),
        score_years=(2022, 2023, 2024, 2025),   # Amendment 2: VanD 2024/25 = 2023 proxy
        f_basis="Sichuan-Basin PMF genus (vehicular+combustion+secondary dominate; "
                "peripheral upland valley less coupled to Chengdu plume). Low confidence.",
        notes="Regime/magnitude-matched primary verdict. CNEMC reference-grade. "
              "Thin spatial scoring (~9 vault stations → wide V4 CI)."),
    "kathmandu": CityPack(
        slug="kathmandu", name="Kathmandu Valley", role="secondary",
        f_local=0.78, f_bracket=(0.65, 0.85),
        score_years=(2024, 2025),               # Amendment 2: dense-network era
        anchor_mode="fixed_longest",            # 2 long-record stations = the KTM "FECT pair"
        f_basis="Mahapatra 2019 WRF-STEM/Chem + CALIPSO: transboundary ~20-25%; "
                "local = vehicles+brick kilns+biomass. Med-High confidence.",
        notes="Spatial statistical power (39 vault stations). Caveats: 2-3x dirtier "
              "than Kandy, brick-kiln season, LCS-heavy (calibrated)."),
    "medellin": CityPack(
        slug="medellin", name="Medellin (Aburra Valley)", role="negative_control",
        f_local=0.80, f_bracket=(0.70, 0.90), score_years=(2019, 2020, 2021, 2022, 2023),
        f_basis="Aburra PMF vehicular-dominated; episodes = canyon-trapped urban "
                "emissions + seasonal wildfire. Medium confidence.",
        notes="Negative control (gotcha #23: terrain-PM ANTI-correlated). Recipe "
              "SHOULD FAIL spatial gate V4 here. Needs VanD NA tile (Phase 4)."),
    "chandigarh": CityPack(
        slug="chandigarh", name="Chandigarh", role="confinement_test",
        f_local=0.70, f_bracket=(0.55, 0.85), score_years=(2019, 2020, 2021, 2022, 2023),
        f_basis="Indo-Gangetic plain edge; not a full recipe run.",
        notes="Confinement SIGN micro-test only (~700 m station relief, the only "
              "network that samples vertical structure). V8 direction, not amplitude."),
    # Reference (not scored; for side-by-side geometry sanity only).
    "kandy": CityPack(
        slug="kandy", name="Kandy (target)", role="reference",
        f_local=0.25, f_bracket=(0.15, 0.50), score_years=(2019, 2020, 2021, 2022, 2023),
        f_basis="World Bank 2022 >50% transboundary + Seneviratne 2017 PMF "
                "(soil/sea-salt/India-influenced biomass) + rural-satellite floor.",
        terrain_npz_name="kandy_terrain_tpi_svf_100m.npz",
        notes="REGIONAL-dominated outlier (f=0.25). Panel cities are LOCAL-dominated "
              "(f 0.6-0.85) — transfer validates machinery at each city's own f, NOT "
              "Kandy's f=0.25. See [[project-transfer-validation-regime-gap]]."),
}


def get(slug: str) -> CityPack:
    if slug not in REGISTRY:
        raise KeyError(f"unknown city '{slug}'. Known: {sorted(REGISTRY)}")
    return REGISTRY[slug]


def _selftest() -> int:
    """Readiness report for every registered city. Run after the build to verify
    all data is wired before any model step. Read-only."""
    import json
    ok = True
    for slug in ("xichang", "kathmandu", "medellin", "chandigarh", "kandy"):
        cp = get(slug)
        rep = cp.check()
        # Only PANEL cities gate the selftest; the reference (kandy) is for geometry
        # sanity and uses the locked decomp's own S_traffic surface, not a _stations
        # road kernel, so its road-kernel absence is expected and non-blocking.
        if cp.role != "reference":
            miss = [k for k in ("terrain", "road", "ntl") if rep.get(k) == "MISSING"]
            if rep["n_stations"] <= 0 or miss:
                ok = False
        print(json.dumps(rep, default=str))
    print("\nSELFTEST", "PASS (panel cities wired)" if ok else "INCOMPLETE (see MISSING above)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
