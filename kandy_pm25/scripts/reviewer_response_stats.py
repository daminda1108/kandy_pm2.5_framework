"""reviewer_response_stats.py — three statistics the manuscript needs and does not
report (2026-08-06, reviewer points 6, 7 and the level summary).

(A) POWER OF THE EMBEDDING NULL. The paper leans on a partial-correlation null at
    n = 6 to 17 stations and calls it "the most direct" of five lines. A null at that
    sample size is only evidence of absence for effects large enough to have been
    detected. This computes the minimum detectable partial correlation at 80% power,
    so the claim can be stated as "we could have detected rho >= X and did not".

(B) DOES ANY A PRIORI DESCRIPTOR PREDICT THE YICHANG FAILURE? The applicability map
    is only useful for a NEW unmonitored target if a city's failure can be anticipated
    from descriptors known BEFORE scoring. Yichang fails the diurnal axis badly
    (r = -0.33). We test whether any selection-time descriptor separates it from the
    valleys that pass. If none does, the applicability map is descriptive rather than
    predictive on that axis, and the paper must say so rather than imply otherwise.
    The temptation here is to invent a screen that conveniently excludes Yichang after
    the fact; that is the very thing the reviewer is objecting to, so the test is
    pre-specified as "does an existing descriptor separate it", not "can I find one".

(C) LEVEL-BIAS SUMMARY. The paper reports the level range as "-4% to +30%" and calls
    it transferring "well". A range is not a summary; report the median and the spread,
    and what the worst case implies for the burden estimate.

Run:  .venv/Scripts/python.exe scripts/reviewer_response_stats.py
Out:  results/figures/multicity/reviewer_response_stats.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MC = REPO / "results" / "figures" / "multicity"
OUT = MC / "reviewer_response_stats.json"

# AlphaEarth embedding test as reported in the manuscript: (city, n stations,
# partial rho after regressing out the physical pattern, p)
EMB = [("Medellin", 17, 0.066, 0.80), ("Kathmandu", 6, -0.143, 0.79),
       ("Chiang Mai", 10, 0.176, 0.63)]
N_CONTROLS = 1                       # the physical pattern is the single control


def min_detectable_r(n: int, k: int = N_CONTROLS, alpha: float = 0.05,
                     power: float = 0.80) -> float:
    """Smallest |partial correlation| detectable at the given power (Fisher z)."""
    from scipy.stats import norm
    dof = n - 3 - k
    if dof <= 0:
        return float("nan")
    z_crit = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    return float(np.tanh(z_crit / np.sqrt(dof)))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    res = {}

    # ── (A) power of the embedding null ────────────────────────────────────────
    print("=== (A) what the embedding null could have detected ===")
    rows = []
    for city, n, rho, p in EMB:
        rmin = min_detectable_r(n)
        rows.append(dict(city=city, n=n, partial_rho=rho, p=p,
                         min_detectable_r=round(rmin, 3)))
        print(f"  {city:<12} n={n:>3}  partial rho {rho:+.3f} (p={p:.2f})   "
              f"could only have detected |rho| >= {rmin:.2f}")
    res["embedding_power"] = rows
    worst = max(r["min_detectable_r"] for r in rows)
    best = min(r["min_detectable_r"] for r in rows)
    res["embedding_power_verdict"] = (
        f"At these sample sizes the test could only have detected residual partial "
        f"correlations of {best:.2f} to {worst:.2f} at 80% power. The nulls therefore "
        f"exclude only a LARGE independent embedding signal, not a modest one. The line "
        f"should be reported as bounding the effect size, not as evidence of absence, "
        f"and it cannot carry the weight of 'the most direct' of the five lines.")
    print(f"\n  -> {res['embedding_power_verdict']}")

    # ── (B) does any a priori descriptor predict the Yichang failure? ───────────
    print("\n=== (B) is the applicability map predictive, or only descriptive? ===")
    sc = pd.read_csv(MC / "validation_scorecard.csv")
    sc["slug"] = sc.city.map(lambda s: s.split(" (")[0].strip())
    # selection-time descriptors (Appendix E) + the emission mix used to build e(t)
    desc = pd.DataFrame([
        # city,      topo, climate, emission, magnitude, vehic, heat, burn
        ("Xichang",  0.70, 0.54, 0.70, 0.95, 0.30, 0.70, 0.00),
        ("Bazhong",  0.74, 0.42, 0.75, 0.94, 0.45, 0.55, 0.00),
        ("Kathmandu", 0.68, 0.43, 0.52, 0.93, 0.40, 0.10, 0.50),
        ("Medellin", 0.65, 0.53, 0.50, 0.89, 0.85, 0.00, 0.15),
        ("Chiang Mai", 0.70, 0.48, 0.50, 0.72, 0.35, 0.10, 0.55),
        ("Tai'an",   0.66, 0.43, 0.64, 0.49, 0.45, 0.55, 0.00),
        ("Baoji",    0.73, 0.42, 0.71, 0.41, 0.35, 0.65, 0.00),
        ("Yichang",  0.63, 0.43, 0.71, 0.47, 0.45, 0.55, 0.00),
        ("Chandigarh", 0.57, 0.46, 0.59, 0.32, 0.45, 0.15, 0.40),
    ], columns=["city", "topo", "climate", "emission", "magnitude",
                "vehic", "heat", "burn"])
    y = desc[desc.city == "Yichang"].iloc[0]
    print("  Yichang vs the valleys that PASS the diurnal gate, on selection-time "
          "descriptors:")
    passers = desc[desc.city.isin(["Tai'an", "Baoji", "Bazhong", "Xichang"])]
    sep = {}
    for c in ["topo", "climate", "emission", "magnitude", "vehic", "heat", "burn"]:
        lo, hi = passers[c].min(), passers[c].max()
        inside = lo <= y[c] <= hi
        sep[c] = bool(not inside)
        print(f"    {c:<10} Yichang {y[c]:.2f}   passing valleys [{lo:.2f}, {hi:.2f}]"
              f"   {'OUTSIDE (separates)' if not inside else 'inside (does NOT separate)'}")
    n_sep = sum(sep.values())
    res["yichang_screen"] = {"separating_descriptors": [k for k, v in sep.items() if v],
                             "n_separating": n_sep}
    if n_sep == 0:
        res["yichang_verdict"] = (
            "NO selection-time descriptor separates Yichang from the valleys that pass. "
            "Its emission mix is IDENTICAL to Tai'an's and Bazhong's (0.45/0.55/0.00) and "
            "its topographic and climate scores sit inside their range. The diurnal "
            "failure therefore could not have been anticipated from the descriptors the "
            "selection procedure uses. The applicability map is descriptive on the "
            "diurnal axis, not predictive, and the paper must state this rather than "
            "present Yichang as a characterised regime boundary. Constructing a screen "
            "after seeing the score would be post hoc and is deliberately not done here.")
    else:
        res["yichang_verdict"] = (
            f"{n_sep} descriptor(s) place Yichang outside the passing range: "
            f"{[k for k, v in sep.items() if v]}. This is a candidate a priori screen, "
            f"but with one failing city it is a hypothesis, not a validated rule.")
    print(f"\n  -> {res['yichang_verdict']}")

    # ── (C) level-bias summary ─────────────────────────────────────────────────
    print("\n=== (C) level bias: a summary, not a range ===")
    lv = sc.level.dropna()
    res["level"] = {"n": int(len(lv)), "median_signed": round(float(lv.median()), 2),
                    "median_abs": round(float(lv.abs().median()), 2),
                    "iqr": [round(float(lv.quantile(.25)), 2),
                            round(float(lv.quantile(.75)), 2)],
                    "within_10pct": int((lv.abs() <= 10).sum()),
                    "min": round(float(lv.min()), 2), "max": round(float(lv.max()), 2)}
    print(f"  median signed {res['level']['median_signed']:+.1f}%   "
          f"median |bias| {res['level']['median_abs']:.1f}%   "
          f"IQR [{res['level']['iqr'][0]:+.1f}, {res['level']['iqr'][1]:+.1f}]%   "
          f"within +-10% at {res['level']['within_10pct']}/{res['level']['n']} cities")
    # what the worst case does to the burden: GEMM is concave, so scale exposure
    print("  NOTE: the burden scales sub-linearly with exposure under GEMM; a +30% level "
          "error is the relevant worst case and belongs in the health caveat.")

    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
