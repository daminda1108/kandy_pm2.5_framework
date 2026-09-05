"""campaign_power.py -- what could the proposed Kandy campaign actually detect?

COMPUTED BEFORE DEPLOYMENT, AND BEFORE THE REGISTRATION IS WRITTEN. Every number here depends
only on the design's site counts and on alpha, never on any measurement, so it can be fixed in
advance. That is the whole point: this project has a null that cost four months because nobody
wrote down what the experiment could see before running it.

THE AWKWARD PART, WHICH THE REGISTRATION MUST LEAD WITH. The panel study that produced the
spatial nulls had 46 cities and could still only resolve an improvement of 0.130 in rank
correlation. A campaign in ONE city has far fewer independent units, so its headline spatial test
is weaker, not stronger, than the study it is meant to follow up. The physics tests are the
opposite: they are directional predictions with large expected effects and a handful of sites is
enough.

FOUR TESTS, and their power differs by more than an order of magnitude.

  H1  SPATIAL RANK. Does a campaign-informed pattern beat the best single free raster
      (benchmark rho = 0.309)? Two correlations measured on the SAME sites against the SAME
      observations, so this is a dependent-correlation comparison, not two independent ones.
      Steiger's z via Fisher r-to-z, which is what gives it any power at all at this n.
  H2  WITHIN-CELL RATIO. The paired triplets measure a ratio directly. Power here is set by
      measurement precision and by how many hours are averaged, NOT by the number of sites,
      which is why 3 triplets suffice where 3 sites never would for a correlation.
  H3  VERTICAL GRADIENT. Concentration against height above the valley floor, 5 sites. Tiny n,
      but the model's own confinement term predicts a large effect.
  H4  DRAINAGE SINK. A directional prediction: the nocturnal maximum sits down-valley of the
      core. A sign test on paired site-nights, where n is NIGHTS and not sites.

Usage: python scripts/campaign_power.py
Out:   data/processed/decomp/campaign_power.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
OUT = DEC / "campaign_power.json"

POWER = 0.80
ALPHA = 0.05
BENCHMARK_RHO = 0.309      # built-up land cover at 2.4 km, from the 46-city frame
# How strongly a campaign-informed pattern would correlate with the benchmark predictor. Both
# are spatial surfaces over the same city, so they are far from independent. Registered as a
# RANGE because it cannot be known in advance, and the detection limit is reported across it.
R_PRED_PRED = [0.5, 0.7, 0.85]


def z(r):
    return np.arctanh(np.clip(r, -0.999999, 0.999999))


def mde_single(n, alpha=ALPHA, power=POWER, sided=2):
    """Smallest |rho| distinguishable from zero."""
    se = 1.0 / np.sqrt(max(n - 3, 1))
    return float(np.tanh((norm.ppf(1 - alpha / sided) + norm.ppf(power)) * se))


def mde_dependent(n, r12, r_pp, alpha=ALPHA, power=POWER, sided=1):
    """Smallest rho_2 that beats rho_1 = r12, both measured on the same n sites.

    Steiger's test for two dependent correlations sharing one variable. The shared variable is
    the observation, and r_pp is how much the two PREDICTORS agree with each other. High r_pp
    means the comparison is between near-identical predictors, which paradoxically INCREASES
    power for the difference, because the shared noise cancels.
    """
    zc = norm.ppf(1 - alpha / sided) + norm.ppf(power)
    lo, hi = r12, 0.9999
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        rm = 0.5 * (r12 + mid)
        # Steiger 1980 covariance of two dependent correlations sharing a variable
        f = (1 - r_pp) / (2 * (1 - rm ** 2))
        h = (1 - f * rm ** 2) / (1 - rm ** 2)
        se = np.sqrt(max(2 * (1 - r_pp) * h / max(n - 3, 1), 1e-12))
        if (z(mid) - z(r12)) / se >= zc:
            hi = mid
        else:
            lo = mid
    return float(hi)


def mde_slope(n, alpha=ALPHA, power=POWER, sided=1):
    """Smallest |correlation| between concentration and height detectable with n transect sites."""
    return mde_single(n, alpha, power, sided)


def mde_sign(n_nights, alpha=ALPHA, power=POWER, sided=1):
    """Smallest proportion above 0.5 detectable by a sign test over n paired nights."""
    se = 0.5 / np.sqrt(n_nights)
    return float(0.5 + (norm.ppf(1 - alpha / sided) + norm.ppf(power)) * se)


def ratio_precision(n_hours, cv_site=0.35, n_pairs=3):
    """Relative precision on a within-cell RATIO, from hours averaged rather than sites.

    A ratio of two co-located means. With `cv_site` the hour-to-hour coefficient of variation at
    a site, the standard error of a log ratio is sqrt(2) * cv / sqrt(n_hours), pooled over pairs.
    This is why the paired stratum is powerful with only three locations.
    """
    se_log = np.sqrt(2.0) * cv_site / np.sqrt(max(n_hours, 1) * max(n_pairs, 1))
    return float(np.exp(1.96 * se_log))


def main() -> None:
    with open(DEC / "sensor_design_summary.json", encoding="utf-8") as fh:
        S = json.load(fh)

    # Sites available to FIT a spatial pattern. The receptor stratum is held out by design and
    # the paired offsets are within-cell replicates, not independent locations, so neither
    # counts toward the number of distinct places a spatial model can learn from.
    n_fit = S["n_design"] + S["n_vertical"] + S["n_anchor"]
    n_pair_loc = S["n_paired"] // 3
    n_all_loc = n_fit + n_pair_loc + S["n_receptor"]

    print("=== what the proposed campaign could detect, computed before deployment ===\n")
    print(f"    distinct locations that can FIT a spatial pattern : {n_fit}")
    print(f"    paired triplet LOCATIONS (within-cell replicates) : {n_pair_loc}")
    print(f"    receptor sites, HELD OUT of fitting               : {S['n_receptor']}")
    print(f"    all distinct locations if nothing were held out   : {n_all_loc}")

    print(f"\n--- H1  spatial rank: can the campaign beat the free raster? ---")
    print(f"    benchmark rho = {BENCHMARK_RHO} (built-up land cover at 2.4 km, 46 cities)")
    h1 = {}
    for n in (n_fit, n_all_loc):
        row = {}
        print(f"    n = {n} sites")
        print(f"      a correlation distinguishable from ZERO      : "
              f"|rho| >= {mde_single(n):.3f}")
        row["vs_zero"] = round(mde_single(n), 3)
        for rpp in R_PRED_PRED:
            m = mde_dependent(n, BENCHMARK_RHO, rpp)
            row[f"vs_benchmark_rpp{rpp}"] = round(m, 3)
            print(f"      beats the benchmark, predictors agree {rpp:.2f}  : "
                  f"rho >= {m:.3f}  (a gain of {m - BENCHMARK_RHO:+.3f})")
        h1[str(n)] = row

    print(f"\n--- H2  within-cell ratio: the paired triplets ---")
    h2 = {}
    for hours in (168, 720, 2160):
        p = ratio_precision(hours, n_pairs=n_pair_loc)
        h2[str(hours)] = round(p, 3)
        print(f"      {hours:>5} h averaged ({hours/24:>5.0f} d): a ratio is resolved to "
              f"about a factor of {p:.3f}")
    print(f"      the model predicts {S['pair_contrast_hi']:.2f}x; one Kandy observation at "
          f"300 m suggests 27.5x")
    print(f"      -> the two hypotheses are separated by orders of magnitude, so this test is "
          f"decisive within weeks")

    print(f"\n--- H3  vertical gradient: {S['n_vertical']} transect sites ---")
    m3 = mde_slope(S["n_vertical"])
    print(f"      |correlation| with height detectable : >= {m3:.3f}")
    print(f"      transect spans {S['vertical_zaf_lo']:.0f} to {S['vertical_zaf_hi']:.0f} m, so "
          f"only a STRONG confinement effect is visible. Registered as such.")

    print(f"\n--- H4  drainage sink: a sign test over paired site-NIGHTS ---")
    h4 = {}
    for nights in (30, 90, 180, 365):
        p = mde_sign(nights)
        h4[str(nights)] = round(p, 3)
        print(f"      {nights:>4} nights: detectable if the sink is higher on >= "
              f"{100*p:.1f}% of them")
    print(f"      n is NIGHTS, not sites, which is why this is the best-powered physics test")

    out = dict(
        computed_before_deployment=True,
        alpha=ALPHA, power=POWER, benchmark_rho=BENCHMARK_RHO,
        n_fit=n_fit, n_pair_locations=n_pair_loc, n_receptor_heldout=S["n_receptor"],
        n_all_locations=n_all_loc,
        h1_spatial=h1, h2_ratio_precision=h2,
        h3_vertical_mde=round(m3, 3), h4_sign_test=h4,
        r_pred_pred_range=R_PRED_PRED,
        panel_detection_limit_for_comparison=0.130,
    )
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n-> {OUT.name}")
    print("\n[!] The headline spatial test is the WEAKEST of the four. A 46-city panel resolved "
          "0.130; one city with tens of sites cannot match that, and the registration says so "
          "in advance rather than discovering it afterwards.")


if __name__ == "__main__":
    main()
