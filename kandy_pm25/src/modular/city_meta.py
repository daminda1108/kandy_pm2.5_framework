"""One source of truth for per-city panel metadata (band, instrument class, cluster).

Why this exists (2026-09-25 verification pass): every ladder script merged its band and
reference fraction from ``openaq_manifest.csv``, which holds OpenAQ cities only. The 11 CNEMC
cities therefore carried ``band = NaN`` and, because ``NaN >= 0.5`` is False, were classed as
low-cost-sensor cities, although CNEMC is a regulatory reference network. Band-stratified
results silently covered OpenAQ cities only, while pooled results included CNEMC.

``city_meta()`` merges both sources, recomputes the band from latitude and refuses on any
disagreement, and refuses when a requested city has no metadata.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

MOD = Path(__file__).resolve().parents[2] / "data" / "processed" / "modular"

# Absolute-latitude band edges used by the panel draw (draw_validation_sample.py).
BAND_EDGES = ((15.0, "deep_tropical"), (23.5, "tropical"), (35.0, "subtropical"))


def band_from_lat(lat: float) -> str:
    a = abs(float(lat))
    for edge, name in BAND_EDGES:
        if a < edge:
            return name
    return "temperate"


def city_meta(cities=None, mod_dir: Path = MOD) -> pd.DataFrame:
    """Return one row per city: city, src, country, lat, lon, band, frac_reference, cls, cluster.

    ``cluster`` is the resampling cluster of the two-level bootstrap: the country for an
    OpenAQ city, and ``"CNEMC"`` for every CNEMC city (one national network).
    CNEMC stations are regulatory monitors, so ``frac_reference = 1.0``.
    """
    man = pd.read_csv(mod_dir / "openaq_manifest.csv")
    man = man[man.status == "OK"] if "status" in man else man
    oa = pd.DataFrame({
        "city": man.cluster.astype(str), "src": "OpenAQ", "country": man.country,
        "lat": man.lat, "lon": man.lon, "band_stored": man.band,
        "frac_reference": man.frac_reference.astype(float)})

    smp = pd.read_csv(mod_dir / "validation_sample.csv")
    cn = smp[smp.src == "CNEMC"]
    cn = pd.DataFrame({
        "city": cn.slug.astype(str), "src": "CNEMC", "country": cn.country,
        "lat": cn.lat, "lon": cn.lon, "band_stored": cn.band, "frac_reference": 1.0})

    m = pd.concat([oa, cn], ignore_index=True)
    if m.city.duplicated().any():
        raise ValueError(f"duplicate city ids in metadata: {m.city[m.city.duplicated()].tolist()}")

    m["band"] = m.lat.map(band_from_lat)
    bad = m[m.band_stored.notna() & (m.band_stored != m.band)]
    if len(bad):
        raise ValueError("stored band disagrees with latitude:\n" + bad.to_string())
    m = m.drop(columns="band_stored")

    if m.frac_reference.isna().any():
        raise ValueError(f"missing reference fraction: {m.city[m.frac_reference.isna()].tolist()}")
    m["cls"] = np.where(m.frac_reference >= 0.5, "reference", "LCS")
    m["cluster"] = np.where(m.src == "CNEMC", "CNEMC", m.country.astype(str))

    if cities is not None:
        want = pd.Index(pd.Series(list(cities)).astype(str).unique())
        missing = want.difference(m.city)
        if len(missing):
            raise ValueError(f"no metadata for cities: {sorted(missing)}")
        m = m[m.city.isin(want)]
    return m.reset_index(drop=True)


def attach_meta(df: pd.DataFrame, cols=("band", "frac_reference", "cls", "cluster", "src"),
                city_col: str = "city") -> pd.DataFrame:
    """Merge metadata onto ``df`` (overwriting any existing columns of the same names) and
    refuse if any row is left without a band."""
    cols = list(cols)
    out = df.drop(columns=[c for c in cols if c in df.columns])
    meta = city_meta(out[city_col].astype(str).unique())[["city", *cols]]
    out = out.assign(**{city_col: out[city_col].astype(str)}).merge(
        meta, left_on=city_col, right_on="city", how="left",
        suffixes=("", "_meta"))
    if city_col != "city":
        out = out.drop(columns="city")
    assert out.band.notna().all(), "attach_meta left rows without a band"
    return out
