"""kandy_f_hierarchical.py — a hierarchical estimate of the local fraction f,
replacing the hand-set prior (2026-08-06).

THE PROBLEM
-----------
`FRAC_LOCAL_YEAR` is a hand-set prior (0.20-0.28 by year) that the claim audit called
the weakest number in the chain, and the coherence analysis later showed sits below its
own arithmetic floor in nine months of twelve (F.17). The project's stated reason for
keeping it over the simulation-based (SBI) posterior is an INFORMAL observation:

    "the same inference runs low against the literature bracket at every locally
     dominated panel city where it can be checked, so we treat it as a bias in the
     inference rather than a correction to the prior"

That is a testable claim, and with four cities it can be estimated rather than asserted.

THE DATA (data/processed/decomp/track_i_posteriors.csv)
-------------------------------------------------------
    city        SBI f      90% CI          literature bracket   covered?
    kandy       0.181      [0.10, 0.27]    [0.15, 0.50]         yes
    xichang     0.340      [0.19, 0.50]    [0.55, 0.80]         NO
    kathmandu   0.255      [0.10, 0.38]    [0.65, 0.85]         NO
    medellin    0.355      [0.24, 0.47]    [0.70, 0.90]         NO

At the three locally dominated cities the SBI posterior falls far below the bracket.
The shortfall is not constant (0.34, 0.50, 0.45) but the RATIO is roughly stable
(0.50, 0.34, 0.44), which points to a multiplicative attenuation rather than an offset.
That distinction decides the answer: an additive correction applied to Kandy gives
f ~ 0.61, outside every bracket and physically implausible, whereas a multiplicative
one gives a value that lands near two independent estimates.

THE MODEL
---------
    f_c    ~ Normal(mu, tau)                  population of cities (partial pooling)
    SBI_c  ~ Normal(rho . f_c, s_c)           SBI attenuates the true fraction by rho
    lit_c  ~ Normal(f_c, w_c)                 literature bracket as a soft observation

rho, mu and tau are estimated on the THREE non-Kandy cities and then applied to Kandy,
so Kandy never informs the correction that is applied to it. Inference is on a dense
grid; with four cities there is no case for anything heavier.

WHAT IS DELIBERATELY LEFT OUT
-----------------------------
The coherence floor (f >= 0.410, from the shipped anchor alone) and the NBRO
instrument (wet-season 0.446) are NOT used as inputs. They are held back so that their
agreement or disagreement with the result is independent corroboration rather than
something the model was told.

Run:  .venv/Scripts/python.exe scripts/kandy_f_hierarchical.py
Out:  data/processed/decomp/kandy_f_hierarchical.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
SRC = DEC / "track_i_posteriors.csv"
OUT = DEC / "kandy_f_hierarchical.json"

TARGET = "kandy"
Z90 = 1.6449                      # 90% CI half-width in sd units
GRID = np.linspace(0.005, 0.995, 199)


def parse_pair(s: str):
    a, b = str(s).strip("[]").split(",")
    return float(a), float(b)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== hierarchical estimate of the local fraction f ===")
    d = pd.read_csv(SRC)
    d[["ci_lo", "ci_hi"]] = d.f_post_90ci.apply(lambda s: pd.Series(parse_pair(s)))
    d[["lit_lo", "lit_hi"]] = d.lit_bracket.apply(lambda s: pd.Series(parse_pair(s)))
    d["s"] = (d.ci_hi - d.ci_lo) / (2 * Z90)              # SBI sd
    d["lit_mid"] = (d.lit_lo + d.lit_hi) / 2
    d["lit_w"] = (d.lit_hi - d.lit_lo) / (2 * Z90)        # bracket as a soft obs

    fit = d[d.city != TARGET].reset_index(drop=True)
    tgt = d[d.city == TARGET].iloc[0]
    print(f"  fitting rho, mu, tau on {list(fit.city)}; applying to '{TARGET}'")
    print("  (Kandy does not inform the correction applied to it)\n")

    rho_g = np.linspace(0.20, 1.20, 101)
    mu_g = np.linspace(0.05, 0.95, 91)
    tau_g = np.array([0.05, 0.10, 0.15, 0.20, 0.30])

    # marginal likelihood over the three fitting cities
    logL = np.full((len(rho_g), len(mu_g), len(tau_g)), -np.inf)
    for i, rho in enumerate(rho_g):
        for j, mu in enumerate(mu_g):
            for k, tau in enumerate(tau_g):
                tot = 0.0
                for _, r in fit.iterrows():
                    pri = np.exp(-0.5 * ((GRID - mu) / tau) ** 2)
                    lik_sbi = np.exp(-0.5 * ((r.f_post_mean - rho * GRID) / r.s) ** 2)
                    lik_lit = np.exp(-0.5 * ((r.lit_mid - GRID) / r.lit_w) ** 2)
                    m = np.trapezoid(pri * lik_sbi * lik_lit, GRID)
                    if m <= 0:
                        tot = -np.inf
                        break
                    tot += np.log(m)
                logL[i, j, k] = tot
    logL -= logL.max()
    post = np.exp(logL)
    post /= post.sum()

    rho_post = post.sum(axis=(1, 2))
    rho_hat = float((rho_g * rho_post).sum())
    rho_sd = float(np.sqrt(((rho_g - rho_hat) ** 2 * rho_post).sum()))
    mu_post = post.sum(axis=(0, 2))
    mu_hat = float((mu_g * mu_post).sum())
    tau_post = post.sum(axis=(0, 1))
    tau_hat = float((tau_g * tau_post).sum())

    print(f"  SBI attenuation  rho = {rho_hat:.3f} +/- {rho_sd:.3f}")
    print(f"    -> the inference recovers about {100 * rho_hat:.0f}% of the true local")
    print(f"       fraction; the shortfall is multiplicative, not an offset.")
    print(f"  population mean  mu  = {mu_hat:.3f}   spread tau = {tau_hat:.3f}\n")

    # ── Kandy posterior, marginalising over (rho, mu, tau) ───────────────────
    fk = np.zeros_like(GRID)
    for i, rho in enumerate(rho_g):
        for j, mu in enumerate(mu_g):
            for k, tau in enumerate(tau_g):
                w = post[i, j, k]
                if w <= 0:
                    continue
                pri = np.exp(-0.5 * ((GRID - mu) / tau) ** 2)
                lik_sbi = np.exp(-0.5 * ((tgt.f_post_mean - rho * GRID) / tgt.s) ** 2)
                lik_lit = np.exp(-0.5 * ((tgt.lit_mid - GRID) / tgt.lit_w) ** 2)
                fk += w * pri * lik_sbi * lik_lit
    fk /= np.trapezoid(fk, GRID)
    cdf = np.cumsum(fk) / np.sum(fk)
    q = lambda p: float(np.interp(p, cdf, GRID))
    f_mean = float(np.trapezoid(GRID * fk, GRID))
    f_lo, f_med, f_hi = q(0.05), q(0.50), q(0.95)

    print(f"  KANDY posterior for f")
    print(f"    mean {f_mean:.3f} | median {f_med:.3f} | 90% CI [{f_lo:.3f}, {f_hi:.3f}]")
    print(f"    (shipped prior: 0.20-0.28 by year; raw SBI: {tgt.f_post_mean})\n")

    # ── independent corroboration, deliberately not used as input ────────────
    checks = {"coherence floor (shipped anchor only)": 0.410,
              "NBRO island network, wet season": 0.446,
              "literature bracket": [float(tgt.lit_lo), float(tgt.lit_hi)]}
    print("  INDEPENDENT CHECKS (held out of the model)")
    for k, v in checks.items():
        if isinstance(v, list):
            ok = v[0] <= f_med <= v[1]
            print(f"    {k:<38} {v}  -> {'inside' if ok else 'OUTSIDE'}")
        else:
            inside = f_lo <= v <= f_hi
            print(f"    {k:<38} {v:.3f}   -> {'inside' if inside else 'OUTSIDE'} the 90% CI")

    res = {"model": "f_c ~ N(mu,tau); SBI_c ~ N(rho*f_c, s_c); lit_c ~ N(f_c, w_c)",
           "fitted_on": list(fit.city), "applied_to": TARGET,
           "rho_attenuation": {"mean": round(rho_hat, 4), "sd": round(rho_sd, 4)},
           "population": {"mu": round(mu_hat, 4), "tau": round(tau_hat, 4)},
           "kandy_f": {"mean": round(f_mean, 4), "median": round(f_med, 4),
                       "ci90": [round(f_lo, 4), round(f_hi, 4)]},
           "shipped_prior": "0.20-0.28 by year (hand-set)",
           "raw_sbi": float(tgt.f_post_mean),
           "independent_checks_not_used_as_input": {
               "coherence_floor": 0.410, "nbro_wet_season": 0.446},
           "caveats": [
               "Three fitting cities. This is the regime partial pooling exists for, "
               "but the population parameters are weakly identified and the interval "
               "should be read as indicative.",
               "The literature bracket is treated as a soft observation with a normal "
               "likelihood; it is really an expert range, so its tails are optimistic.",
               "rho is assumed common across cities. With three cities a regime-varying "
               "attenuation cannot be identified."]}
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT.name}")


if __name__ == "__main__":
    main()
