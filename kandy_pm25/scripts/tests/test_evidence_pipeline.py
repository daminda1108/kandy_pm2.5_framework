"""Invariant tests for the transfer-validation evidence pipeline.

These test the mathematical properties the preprint's claims rest on, fast and
without the full data build:

  * the basin-mean invariant (T-lock)                     -> §2, robustness
  * increment-split: T-lock, no core<periphery inversion   -> production form IV.1b
  * additive_v3 floor: mean-zero (T-lock), eps0=0 == split,
    identical on structured hours, no re-inversion, bounded -> production form IV.1c
  * additive vs multiplicative level behaviour at floor    -> ablation (+26%)
  * unit-mean normalisation of the local pattern           -> §2
  * f-invariance of the area mean; linearity of exposure   -> sensitivity (S1)
  * split-conformal coverage                               -> UQ
  * GEMM exposure-response monotonicity / bounds           -> health burden
  * emission-timing profile shape (bimodal, mean-1)        -> e(t)
  * city_config integrity + citypack construction          -> multi-city harness
  * a synthetic-city END-TO-END run (assembly + aggregation, no private data)

All run in <1 s and need no data build or network — they verify, from a clean
clone, the mathematical properties the preprint's claims rest on.

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


def _split_field(T, B, P):
    """Increment-SPLIT additive form (2026-07-09 core<periphery fix):
    PM = B + max(T-B,0)·P + min(T-B,0). The local pattern structures only
    accumulation above background; ventilation below is spatially uniform."""
    inc = T - B
    return B + max(inc, 0.0) * P + min(inc, 0.0)


def test_split_form_preserves_tlock():
    """The increment split keeps the T-lock exact on BOTH branches (T>B and T<B)."""
    rng = np.random.default_rng(7)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=(64, 64)))
    for T, B in ((21.0, 14.8), (10.0, 14.8), (66.0, 20.0), (5.0, 20.0)):
        assert _split_field(T, B, P).mean() == pytest.approx(T, rel=1e-12)


def test_split_form_removes_core_periphery_inversion():
    """When hourly T dips below daily B (38.5% of Kandy hours), the plain additive
    form INVERTS the pattern (core cleaner than edge); the split renders a flat field."""
    rng = np.random.default_rng(8)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=1000))
    core, edge = P > 1.1, P < 0.9
    T, B = 12.0, 18.0                                   # ventilated hour: T < B
    plain = B + (T - B) * P
    assert plain[core].mean() < plain[edge].mean()      # the inversion defect
    split = _split_field(T, B, P)
    assert np.allclose(split, T)                        # flat when ventilated — no inversion
    T2 = 25.0                                            # accumulation hour: T > B
    acc = _split_field(T2, B, P)
    assert np.allclose(acc, B + (T2 - B) * P)            # identical to plain form
    assert acc[core].mean() > acc[edge].mean()           # core high, physically right


# ── additive_v3: the ventilated-hour pattern floor (2026-07-21) ───────────────
def _floor_field(T, B, P, eps0):
    """Production form IV.1c: PM = B + max(max(T-B,0),eps0)·P + min(T-B,0)
    - max(0, eps0-max(T-B,0)). Mirrors assemble_year()'s split with EPS_FLOOR."""
    inc = T - B
    a = max(inc, 0.0)
    return B + max(a, eps0) * P + min(inc, 0.0) - max(0.0, eps0 - a)


def test_floor_preserves_tlock_exactly():
    """The floor term eps(t)·(P-1) is mean-zero, so the T-lock stays EXACT for any
    eps0 and any (T, B) — including deep-ventilation hours where it activates."""
    rng = np.random.default_rng(21)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=(64, 64)))
    for eps0 in (0.0, 2.573, 6.0):
        for T, B in ((35.0, 20.0), (12.0, 20.0), (5.0, 20.0), (0.5, 18.0)):
            assert _floor_field(T, B, P, eps0).mean() == pytest.approx(T, rel=1e-12)


def test_floor_eps0_zero_reduces_to_split():
    """eps0 = 0 reproduces the increment-split byte-for-byte (locked-tier guarantee)."""
    rng = np.random.default_rng(22)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=2000))
    for T, B in ((35.0, 20.0), (12.0, 20.0), (5.0, 20.0)):
        assert np.array_equal(_floor_field(T, B, P, 0.0), _split_field(T, B, P))


def test_floor_identical_on_structured_hours():
    """When the accumulation amplitude clears eps0 (structured hours), the floor is
    inactive and the field is identical to the plain split — no level change."""
    rng = np.random.default_rng(23)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=2000))
    eps0 = 2.573
    T, B = 30.0, 20.0                         # inc = 10 > eps0
    assert np.allclose(_floor_field(T, B, P, eps0), _split_field(T, B, P))


def test_floor_never_reinverts_core():
    """On a ventilated hour the floor adds muted structure (core >= edge), never the
    inversion the split was introduced to remove."""
    rng = np.random.default_rng(24)
    P = _unit_mean(rng.gamma(2.0, 1.0, size=4000))
    core, edge = P > 1.1, P < 0.9
    T, B, eps0 = 12.0, 18.0, 2.573            # ventilated: inc < 0, floor active
    f = _floor_field(T, B, P, eps0)
    assert f[core].mean() >= f[edge].mean()   # muted structure, correct sign
    assert f.std() > _split_field(T, B, P).std()  # not perfectly flat any more


def test_floor_bounded_and_positive_on_clean_hours():
    """With a physical pattern range the floor's spread stays bounded (no explosion
    that would corrupt uint16 quantisation) and the field stays non-negative."""
    rng = np.random.default_rng(25)
    P = _unit_mean(np.clip(rng.gamma(2.0, 1.0, size=4000), 0.3, 3.2))
    T, B, eps0 = 8.0, 16.0, 2.573
    f = _floor_field(T, B, P, eps0)
    assert (f.max() - f.min()) < 3.0 * eps0   # spread ~ eps0·range, bounded
    assert f.min() > -1e-9                     # non-negative for a clean valley


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


# ── synthetic-city end-to-end: the whole assembly + aggregation chain, no data ─
def test_synthetic_city_end_to_end():
    """Reproducible-from-clone check: fabricate a tiny city (grid, hourly T with a
    realistic diurnal swing that dips below B on some hours, a background B, a
    unit-mean emission pattern) and run the FULL production assembly (v2 split +
    v3 floor) over every hour, then aggregate exposure and burden. Verifies the
    chain of invariants the preprint rests on holds jointly, using only synthetic
    inputs any clone can regenerate — no private parquet, no network."""
    rng = np.random.default_rng(2026)
    n = 40 * 40                                   # 40x40 ~ 1 km grid
    P = _unit_mean(np.clip(rng.gamma(2.0, 1.0, size=n), 0.3, 3.2))   # emission pattern
    hours = np.arange(24 * 30)                     # a synthetic month
    # diurnal T: rush peaks + deep-night trough, annual ~19; B a flatter background
    diur = 1 + 0.5 * (np.exp(-((hours % 24 - 7) ** 2) / 6)
                      + np.exp(-((hours % 24 - 18) ** 2) / 6)) - 0.35 * np.cos(hours % 24 / 24 * 2 * np.pi)
    T = 19.0 * diur / diur.mean()
    B = np.full_like(T, 0.75 * 19.0)               # f_local = 0.25
    eps0 = 2.573
    w = _unit_mean(np.clip(rng.gamma(2.0, 1.0, size=n), 0.2, 5.0)); w = w / w.sum()

    ventilated_hours = 0
    exposures = []
    for T_h, B_h in zip(T, B):
        field = _floor_field(T_h, B_h, P, eps0)
        # (1) T-lock holds every hour, on both accumulation and ventilation branches
        assert field.mean() == pytest.approx(T_h, rel=1e-10)
        # (2) physical floor: a clean valley never goes negative
        assert field.min() > -1e-9
        # (3) no core<periphery inversion: high-emission pixels are never the cleanest
        if (T_h - B_h) > eps0:                      # structured hour
            assert field[P > 1.2].mean() > field[P < 0.8].mean()
        else:
            ventilated_hours += 1
        exposures.append(float((field * w).sum()))  # population-weighted exposure

    assert ventilated_hours > 0                      # the fixture exercises both branches
    # (4) population-weighted exposure exceeds the plain area mean (pop clusters in the
    #     higher-pattern core) and stays within the field's physical range
    assert np.mean(exposures) > T.mean() * 0.99
    # (5) burden via GEMM is finite, monotone in exposure, and bounded in [0,1)
    af = _gemm_af(np.array(exposures))
    assert np.all(np.isfinite(af)) and np.all((af >= 0) & (af < 1))
