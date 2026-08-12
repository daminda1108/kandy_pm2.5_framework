"""eps_floor_hierarchical.py — is the ventilated-hour floor eps0 transferable? (W7,
2026-08-06)

THE WEAK POINT
--------------
additive_v3 adds a bounded, mean-zero pattern floor on ventilated hours. Its magnitude
eps0 was fitted at ONE city (Medellin, 5.65 ug/m3) and carried to Kandy in RELATIVE form
-- as a fraction of the city's own mean accumulation amplitude -- giving Kandy 2.573.
That is a transfer from n=1, and the relative normalisation was adopted because it seemed
the more physical of the two, not because it was tested.

`flat_hour_residual_fit.py` already fits each panel city's OWN slope. With three cities the
question becomes answerable: is eps0 a transferable constant in either form, and what does
a proper partial pooling say Kandy's value should be?

METHOD
------
Same machinery as the f-partition pooling (ledger F.21): a normal hierarchical model

    theta_c ~ N(mu, tau),    hat_theta_c ~ N(theta_c, s_c)

fitted by marginal maximum likelihood on tau, with per-city standard errors derived from
the regression t-statistic implied by each city's rank correlation and sample size
(t = rho * sqrt((n-2)/(1-rho^2)), s_c = |theta_c| / t). Cities whose flat-hour structure
is not emission-shaped -- rho near zero -- therefore carry large standard errors and are
shrunk heavily toward the population mean, which is the correct treatment: their slope is
not an estimate of anything.

Run both forms (absolute ug/m3, and relative to mean accumulation) and compare the
between-city spread tau against the within-city uncertainty. If tau dominates in BOTH
forms, eps0 is not a transferable constant and the shipped Kandy value rests on a
normalisation that does not hold -- which is a finding, not a failure, because the gates
show the floor does not degrade any city.

Run:  .venv/Scripts/python.exe scripts/eps_floor_hierarchical.py
Out:  data/processed/decomp/eps_floor_hierarchical.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIT = REPO / "results" / "figures" / "medellin_showcase" / "flat_hour_residual.json"
OUT = REPO / "data" / "processed" / "decomp" / "eps_floor_hierarchical.json"

KANDY_MEAN_INC = 6.465          # Kandy's mean accumulation amplitude (build log)
SHIPPED_KANDY_EPS = 2.573       # = 0.398 x 6.465, the transferred value


def se_from_rho(theta: float, rho: float, n: int) -> float:
    """Standard error of a slope implied by its correlation and sample size."""
    rho, n = abs(float(rho)), int(n)
    if n < 5 or rho <= 1e-4:
        return abs(theta) * 10.0            # unidentified: enormous uncertainty
    t = rho * np.sqrt((n - 2) / max(1e-9, 1 - rho ** 2))
    return abs(theta) / max(1e-6, t)


def fit_tau(theta: np.ndarray, s: np.ndarray) -> tuple:
    """Marginal MLE for (mu, tau) in theta_c ~ N(mu, tau), hat ~ N(theta_c, s_c)."""
    def nll(log_tau):
        tau2 = np.exp(log_tau) ** 2
        v = s ** 2 + tau2
        mu = np.sum(theta / v) / np.sum(1.0 / v)
        return 0.5 * np.sum(np.log(v) + (theta - mu) ** 2 / v)
    grid = np.linspace(np.log(1e-4), np.log(10.0), 4000)
    vals = np.array([nll(g) for g in grid])
    log_tau = grid[int(np.argmin(vals))]
    tau = float(np.exp(log_tau))
    v = s ** 2 + tau ** 2
    mu = float(np.sum(theta / v) / np.sum(1.0 / v))
    se_mu = float(np.sqrt(1.0 / np.sum(1.0 / v)))
    return mu, tau, se_mu


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rep = json.loads(FIT.read_text(encoding="utf-8"))
    cities = [("medellin", rep["eps0_medellin"], rep["spearman"], rep["n_pairs"],
               rep["mean_inc_pos"])]
    for c, d in rep["cross_city"].items():
        cities.append((c, d["own_slope"], d["own_rho"], d["n"], d["mean_inc"]))

    print("=== W7: is the ventilated-hour floor eps0 transferable? ===\n")
    print("  city         own eps0   mean_inc   relative   rho     n")
    for c, sl, rho, n, mi in cities:
        print(f"  {c:<12} {sl:>7.2f}   {mi:>7.2f}   {sl / mi:>8.3f}   {rho:>5.2f}  {n:>6}")

    out = {"cities": [{"city": c, "eps0_abs": sl, "mean_inc": mi,
                       "eps0_rel": round(sl / mi, 4), "rho": rho, "n": n}
                      for c, sl, rho, n, mi in cities]}

    for form, vals in [("absolute (ug/m3)", [c[1] for c in cities]),
                       ("relative (fraction of mean accumulation)",
                        [c[1] / c[4] for c in cities])]:
        theta = np.array(vals, float)
        s = np.array([se_from_rho(t, c[2], c[3]) for t, c in zip(theta, cities)])
        mu, tau, se_mu = fit_tau(theta, s)
        spread = float(theta.max() / max(1e-9, theta.min()))
        ratio = float(tau / np.median(s))
        key = "absolute" if form.startswith("abs") else "relative"
        out[key] = {"values": [round(float(v), 4) for v in theta],
                    "se": [round(float(v), 4) for v in s],
                    "mu": round(mu, 4), "tau": round(tau, 4),
                    "se_mu": round(se_mu, 4), "max_min_ratio": round(spread, 1),
                    "tau_over_median_se": round(ratio, 1)}
        print(f"\n  {form}")
        print(f"    values {np.round(theta, 3).tolist()}  (max/min = {spread:.0f}x)")
        print(f"    population mu = {mu:.3f}, between-city tau = {tau:.3f}")
        print(f"    tau / median within-city SE = {ratio:.0f}"
              f"   -> {'BETWEEN-city variation dominates' if ratio > 3 else 'pooling is informative'}")

    # what the pooling implies for Kandy, in the form the model actually ships
    rel = out["relative"]
    lo, hi = rel["mu"] - 1.645 * rel["tau"], rel["mu"] + 1.645 * rel["tau"]
    k_mu, k_lo, k_hi = (rel["mu"] * KANDY_MEAN_INC, max(0.0, lo) * KANDY_MEAN_INC,
                        hi * KANDY_MEAN_INC)
    out["kandy"] = {"shipped_eps0": SHIPPED_KANDY_EPS,
                    "mean_inc": KANDY_MEAN_INC,
                    "pooled_eps0": round(k_mu, 3),
                    "predictive_90": [round(k_lo, 3), round(k_hi, 3)],
                    "shipped_inside": bool(k_lo <= SHIPPED_KANDY_EPS <= k_hi)}
    print(f"\n  KANDY: shipped eps0 = {SHIPPED_KANDY_EPS} ug/m3")
    print(f"         pooled  eps0 = {k_mu:.2f}  90% predictive [{k_lo:.2f}, {k_hi:.2f}]"
          f"   -> shipped value {'INSIDE' if out['kandy']['shipped_inside'] else 'OUTSIDE'}")

    both_dominated = (out["absolute"]["tau_over_median_se"] > 3
                      and out["relative"]["tau_over_median_se"] > 3)
    rel_better = out["relative"]["max_min_ratio"] < out["absolute"]["max_min_ratio"]
    out["verdict"] = (
        ("eps0 is NOT a transferable constant in either form: between-city variation "
         "dominates within-city uncertainty, so a value fitted at one city predicts "
         "another city's only weakly. " if both_dominated else
         "Between-city variation is comparable to within-city uncertainty; pooling is "
         "informative. ")
        + (f"The RELATIVE normalisation the shipped model uses is "
           f"{'better' if rel_better else 'NOT better'} behaved than the absolute one "
           f"({out['relative']['max_min_ratio']:.0f}x vs "
           f"{out['absolute']['max_min_ratio']:.0f}x spread). ")
        + ("The shipped Kandy value lies inside the pooled predictive interval, so it is "
           "not contradicted -- but it is one draw from a wide distribution rather than a "
           "determined quantity, and should be described that way."
           if out["kandy"]["shipped_inside"] else
           "The shipped Kandy value lies OUTSIDE the pooled predictive interval and "
           "should be revisited."))
    print(f"\n  VERDICT: {out['verdict']}")
    out["note"] = ("The floor's magnitude is weakly determined, but its SAFETY is not in "
                   "question: the no-degrade gates pass at all three cities, the form is "
                   "mean-zero so T-lock is exact, and eps0=0 recovers additive_v2 exactly. "
                   "The consequence is a claim-tier statement, not a code change.")
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT.name}")


if __name__ == "__main__":
    main()
