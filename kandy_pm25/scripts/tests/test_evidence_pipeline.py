"""Invariant tests for the transfer-validation evidence pipeline.

These test the mathematical properties the preprint's claims rest on, fast and
without the full data build:

  * the basin-mean invariant (T-lock)                     -> §2, robustness
  * additive vs multiplicative level behaviour at floor    -> ablation (+26%)
  * unit-mean normalisation of the local pattern           -> §2
  * f-invariance of the area mean; linearity of exposure   -> sensitivity (S1)
  * split-conformal coverage                               -> UQ
  * GEMM exposure-response monotonicity / bounds           -> health burden
  * emission-timing profile shape (bimodal, mean-1)        -> e(t)
  * city_config integrity + citypack construction          -> multi-city harness

Run:  python -m pytest scripts/tests -q
"""
import numpy as np
import pytest


# ── core additive-model invariants (pure math, no data) ──────────────────────
def _unit_mean(pattern):
    return pattern / pattern.mean()


def test_basin_mean_invariant_tlock():
    """mean(B + [T-B]·P) == T for any unit-mean P and any B (the T-lock)."""
    rng = np.random.default_rng(0)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=(64, 64)))
    for T in (10.0, 21.0, 66.0):
        for f in (0.1, 0.25, 0.8):
            B = (1 - f) * T
            field = B + (T - B) * P
            assert field.mean() == pytest.approx(T, rel=1e-12)


def test_area_mean_invariant_to_f():
    """Area mean is exactly invariant to the local fraction f (sensitivity S1)."""
    rng = np.random.default_rng(1)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=2000))
    T = 21.04
    means = [(( (1 - f) * T) + (T - (1 - f) * T) * P).mean() for f in np.linspace(0.1, 0.4, 7)]
    assert np.allclose(means, T, rtol=1e-12)


def test_population_weighted_exposure_linear_in_f():
    """E_w = T·[1 + f·(P_w-1)] — exposure is exactly linear in f (S1 basis)."""
    rng = np.random.default_rng(2)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=5000))
    w = _unit_mean(rng.gamma(2.0, 1.0, size=5000)); w = w / w.sum()   # weights sum to 1
    Pw = float((P * w).sum())          # pop-weighted pattern excess
    T = 21.0
    for f in (0.15, 0.25, 0.35):
        B = (1 - f) * T
        E_direct = float(((B + (T - B) * P) * w).sum())
        E_formula = T * (1 + f * (Pw - 1))
        assert E_direct == pytest.approx(E_formula, rel=1e-10)


def test_multiplicative_inflates_level_at_core():
    """At core/floor stations (P>1) multiplicative T·P exceeds additive B+[T-B]·P."""
    T, f = 40.0, 0.5
    B = (1 - f) * T
    P_core = 1.8                        # a floor/core station where pattern > 1
    additive = B + (T - B) * P_core
    multiplicative = T * P_core
    assert multiplicative > additive     # the +26%-type inflation direction


def test_unit_mean_normalisation():
    rng = np.random.default_rng(3)
    P = _unit_mean(rng.random(1000) + 0.1)
    assert P.mean() == pytest.approx(1.0, rel=1e-12)


# ── split-conformal coverage ─────────────────────────────────────────────────
def test_split_conformal_coverage():
    """A split-conformal 90% interval covers ~90% on exchangeable data."""
    rng = np.random.default_rng(4)
    cal = np.abs(rng.normal(size=4000))                 # calibration residual magnitudes
    q = np.quantile(cal, 0.90)
    test = np.abs(rng.normal(size=20000))
    cov = float((test <= q).mean())
    assert 0.87 <= cov <= 0.93


# ── GEMM health exposure-response (constants mirror health_burden.py) ─────────
def _gemm_af(pm, theta=0.143, alpha=1.6, mu=15.5, nu=36.8, c0=2.4):
    z = np.clip(pm - c0, 0, None)
    rr = np.exp(theta * np.log1p(z / alpha) / (1.0 + np.exp(-(z - mu) / nu)))
    return (rr - 1.0) / rr


def test_gemm_monotonic_and_bounded():
    pm = np.linspace(0, 80, 400)
    af = _gemm_af(pm)
    assert af[0] == pytest.approx(0.0, abs=1e-9)         # AF=0 at/below counterfactual
    assert np.all(np.diff(af) >= -1e-12)                 # monotonically non-decreasing
    assert np.all((af >= 0) & (af < 1))                  # attributable fraction in [0,1)
    assert 0.10 < _gemm_af(np.array([21.0]))[0] < 0.30   # Kandy-level AF ~0.18


# ── emission-timing profile e(t) ─────────────────────────────────────────────
def test_emission_profile_shape():
    from src.stage1_satml.decomp.emission_profile import emission_profile
    e = emission_profile()
    assert e.shape == (24,)
    assert np.all(e > 0)
    assert e.mean() == pytest.approx(1.0, rel=1e-6)      # normalised to mean 1
    # bimodal: morning (6-9) and evening (17-20) exceed the deep-night min (0-4)
    night = e[0:5].mean()
    assert e[6:10].max() > night and e[17:21].max() > night


# ── city_config integrity + citypack construction ────────────────────────────
def test_city_config_entries_valid():
    from city_config import CITIES, cfg, citypack, e_profile
    required = {"name", "cen", "tz", "utm", "box", "dem", "years", "f", "emix"}
    for slug, c in CITIES.items():
        assert required <= set(c), f"{slug} missing keys: {required - set(c)}"
        latmin, latmax, lonmin, lonmax = c["box"]
        assert latmin < latmax and lonmin < lonmax, f"{slug} bad box"
        assert 0.0 <= c["f"] <= 1.0, f"{slug} f out of range"
        assert abs(sum(c["emix"].values()) - 1.0) < 1e-6, f"{slug} emix must sum to 1"
    # the multi-city harness must be able to build a pack + timing profile
    cp = citypack("medellin")
    assert cp.slug == "medellin" and 0 < cp.f_local <= 1
    assert e_profile("medellin").shape == (24,)


def test_medellin_present_and_tropical():
    from city_config import CITIES
    assert "medellin" in CITIES
    lat = CITIES["medellin"]["cen"][0]
    assert 0 < lat < 12          # tropical latitude (Colombia)
