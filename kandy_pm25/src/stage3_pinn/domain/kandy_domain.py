"""
kandy_domain.py — Kandy valley computational domain for Stage 3 PINN.

Kandy Valley PINN domain — 15×15 km at 100m resolution (150×150 grid).
Domain centred on 7.2906°N, 80.6337°E.
Covers: Kandy Lake, Hantana ridge (SW), Knuckles approach (NE),
Peradeniya (WSW), Mahaweli corridor (NNE).
Boundary conditions: Dirichlet from Stage 1 XGBoost output at valley rim.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    KANDY_PINN_BBOX, KANDY_CENTER, LOG_FORMAT, LOG_DATEFMT,
    PINN_GRID_RESOLUTION_M, DOMAIN_LAT_EXTENT_KM, DOMAIN_LON_EXTENT_KM,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("kandy_domain")

# Grid dimensions at 100 m resolution
GRID_EAST_CELLS  = int(DOMAIN_LON_EXTENT_KM * 1000 / PINN_GRID_RESOLUTION_M)
GRID_NORTH_CELLS = int(DOMAIN_LAT_EXTENT_KM * 1000 / PINN_GRID_RESOLUTION_M)


class KandyDomain:
    """
    Kandy valley PINN computational domain.

    Attributes:
        lon_grid   : 2D array of longitude values (N_lat × N_lon)
        lat_grid   : 2D array of latitude values
        x_norm     : Normalised x coordinates in [-1, 1]
        y_norm     : Normalised y coordinates in [-1, 1]
        terrain_mask : Boolean mask True = inside valley (below rim)
        elevation  : DEM elevation in metres (loaded from raster)
    """

    def __init__(
        self,
        dem_path: Optional[Path] = None,
        osm_path: Optional[Path] = None,
    ):
        """
        Initialise the Kandy domain grid.

        Args:
            dem_path : Path to DEM GeoTIFF (30 m SRTM)
            osm_path : Path to OSM road network GeoJSON / Shapefile
        """
        self.bbox   = KANDY_PINN_BBOX
        self.center = KANDY_CENTER
        self.n_lon  = GRID_EAST_CELLS
        self.n_lat  = GRID_NORTH_CELLS

        # Build lat/lon grids
        self.lons = np.linspace(self.bbox["lon_min"], self.bbox["lon_max"], self.n_lon)
        self.lats = np.linspace(self.bbox["lat_min"], self.bbox["lat_max"], self.n_lat)
        self.lon_grid, self.lat_grid = np.meshgrid(self.lons, self.lats)

        # Normalised coordinates for PINN input
        self.x_norm = self._normalise(self.lon_grid, self.bbox["lon_min"], self.bbox["lon_max"])
        self.y_norm = self._normalise(self.lat_grid, self.bbox["lat_min"], self.bbox["lat_max"])

        # Optional DEM and terrain features
        self.elevation    = None
        self.terrain_mask = np.ones((self.n_lat, self.n_lon), dtype=bool)
        self.slope        = None
        self.aspect       = None

        if dem_path and Path(dem_path).exists():
            self._load_dem(dem_path)
        else:
            log.warning("No DEM provided — terrain mask will be all-inclusive")

        # OSM road network (source term spatial structure)
        self.road_density = None
        if osm_path and Path(osm_path).exists():
            self._load_osm_roads(osm_path)

        log.info(
            f"KandyDomain initialised: {self.n_lon}×{self.n_lat} grid "
            f"({self.n_lon * PINN_GRID_RESOLUTION_M / 1000:.0f} km E-W × "
            f"{self.n_lat * PINN_GRID_RESOLUTION_M / 1000:.0f} km N-S) at {PINN_GRID_RESOLUTION_M} m"
        )

    @staticmethod
    def _normalise(arr: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
        """Map [vmin, vmax] → [-1, 1]."""
        return 2.0 * (arr - vmin) / (vmax - vmin) - 1.0

    def to_normalised(self, lon: np.ndarray, lat: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Convert real coordinates to normalised PINN coordinates."""
        x = self._normalise(lon, self.bbox["lon_min"], self.bbox["lon_max"])
        y = self._normalise(lat, self.bbox["lat_min"], self.bbox["lat_max"])
        return x, y

    def to_physical(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Convert normalised PINN coordinates back to real lon/lat."""
        lon = 0.5 * (x + 1.0) * (self.bbox["lon_max"] - self.bbox["lon_min"]) + self.bbox["lon_min"]
        lat = 0.5 * (y + 1.0) * (self.bbox["lat_max"] - self.bbox["lat_min"]) + self.bbox["lat_min"]
        return lon, lat

    def _load_dem(self, dem_path: Path) -> None:
        """Load DEM and compute terrain mask (below valley rim = inside domain)."""
        try:
            import rasterio
            from rasterio.transform import rowcol
        except ImportError:
            log.warning("rasterio not installed — DEM not loaded")
            return

        with rasterio.open(dem_path) as src:
            elevation_raw = src.read(1).astype(np.float32)
            elevation_raw[elevation_raw == src.nodata] = np.nan
            self.elevation = elevation_raw
            log.info(f"DEM loaded: {dem_path.name} ({src.width}×{src.height})")

        # Very rough valley mask: below 750 m = inside valley
        # TODO: replace with proper topographic horizon analysis
        if self.elevation is not None:
            self.terrain_mask = self.elevation < 750.0

    def _load_osm_roads(self, osm_path: Path) -> None:
        """Load OSM road network and rasterise to road kernel density grid."""
        try:
            import geopandas as gpd
        except ImportError:
            log.warning("geopandas not installed — OSM road density not loaded")
            return
        roads = gpd.read_file(osm_path)
        log.info(f"OSM roads loaded: {len(roads)} features from {osm_path.name}")
        # Rasterisation to self.road_density grid is done in source_term.py
        self.road_density = None  # Placeholder

    def flat_inputs(self, t_normalised: float = 0.0) -> np.ndarray:
        """
        Return flattened (N, 3) array of [x, y, t] for all grid points.
        N = n_lon × n_lat. Use for batch PINN forward passes.

        Args:
            t_normalised : Normalised time in [0, 1] (0=start, 1=end of study period)
        """
        x_flat = self.x_norm.ravel()
        y_flat = self.y_norm.ravel()
        t_flat = np.full_like(x_flat, t_normalised)
        return np.column_stack([x_flat, y_flat, t_flat]).astype(np.float32)

    def n_points(self) -> int:
        """Total number of grid points."""
        return self.n_lon * self.n_lat

    @property
    def grid_shape(self) -> Tuple[int, int]:
        """Grid dimensions as (n_lon, n_lat)."""
        return (self.n_lon, self.n_lat)

    @property
    def resolution_m(self) -> int:
        """Grid resolution in metres."""
        return PINN_GRID_RESOLUTION_M

    @property
    def lon_extent_km(self) -> float:
        """Domain extent in the longitude direction (km)."""
        return self.n_lon * PINN_GRID_RESOLUTION_M / 1000.0

    @property
    def lat_extent_km(self) -> float:
        """Domain extent in the latitude direction (km)."""
        return self.n_lat * PINN_GRID_RESOLUTION_M / 1000.0
