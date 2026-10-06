"""Tests for src/modular/city_meta.py and src/modular/runlog.py (verification pass 2026-09-25).

The defect these guard: band and instrument class were merged from an OpenAQ-only manifest, so
the 11 CNEMC cities were unbanded and classed as low-cost-sensor cities in every ladder output.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.modular.city_meta import attach_meta, band_from_lat, city_meta  # noqa: E402
from src.modular.runlog import DropLog                                   # noqa: E402


def test_band_edges():
    assert band_from_lat(7.29) == "deep_tropical"      # Kandy
    assert band_from_lat(-14.99) == "deep_tropical"
    assert band_from_lat(15.0) == "tropical"
    assert band_from_lat(23.49) == "tropical"
    assert band_from_lat(23.5) == "subtropical"
    assert band_from_lat(35.0) == "temperate"


def test_every_city_has_band_class_cluster():
    m = city_meta()
    assert m[["band", "cls", "cluster"]].notna().all().all()
    assert not m.city.duplicated().any()


def test_cnemc_is_reference_one_cluster_and_banded():
    m = city_meta()
    cn = m[m.src == "CNEMC"]
    assert len(cn) == 11
    assert (cn.cls == "reference").all()
    assert (cn.cluster == "CNEMC").all()
    assert set(cn.band) == {"tropical", "subtropical", "temperate"}   # none deep-tropical


def test_no_cnemc_city_is_deep_tropical():
    """Why the deep-tropical headline did not move when the labels were fixed."""
    m = city_meta()
    assert not ((m.src == "CNEMC") & (m.band == "deep_tropical")).any()


def test_refuses_unknown_city():
    with pytest.raises(ValueError, match="no metadata"):
        city_meta(["not_a_city"])


def test_attach_meta_overwrites_stale_labels():
    df = pd.DataFrame({"city": ["city044", "city044"], "band": [None, None],
                       "cls": ["LCS", "LCS"], "x": [1, 2]})
    out = attach_meta(df)
    assert (out.band == "temperate").all()           # Beijing
    assert (out.cls == "reference").all()
    assert list(out.x) == [1, 2]


def test_droplog_strict_raises_on_error(tmp_path):
    d = DropLog("t")
    d.skip("a", "too few days")
    d.report(tmp_path / "ok.json")                    # skips alone do not raise
    try:
        raise RuntimeError("boom")
    except RuntimeError as e:
        d.error("b", e)
    with pytest.raises(SystemExit):
        d.report(tmp_path / "err.json")
    assert (tmp_path / "err.json").exists()
