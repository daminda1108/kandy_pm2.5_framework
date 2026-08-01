"""kandy_forecast_ood_widening.py — the OOD interval-widening factor for the
Kandy live forecast panel (2026-07-27).

WHY THIS EXISTS
---------------
The live Kandy forecast (`kandy_webapp/live/kandy_live.py`) drives a frozen
quantile GBM whose q05/q95 heads were fitted IN-REGIME, on the locked 2019-2023
Kandy anchor. Kandy itself is regime-OOD with respect to every panel city the
method was validated on (regional/transboundary-dominated, f_local ~= 0.25, vs a
panel that is local-emission-dominated), and the one place we can MEASURE what
that costs is the sensorless daily anchor: its nominal 90% interval covers only
70.7% of the FECT record (`data/processed/decomp/kandy_anchor_free_t.csv`,
n=1215 days).

An un-widened forecast interval would therefore understate its own uncertainty in
exactly the direction that matters for a public, health-adjacent display that
nobody in Kandy can check against a local monitor.

WHAT IT COMPUTES
----------------
The scalar k that inflates the deviations of the interval edges about the median,

    [ med - k*(med - lo),  med + k*(hi - med) ],

until empirical coverage on that record reaches the nominal 0.90. Two independent
derivations are reported and must agree:

  (a) direct search over k on the observed coverage curve;
  (b) split-conformal style: k = 1 + q_0.90 of the normalised nonconformity score
      s_i = max( (lo_i - y_i)/(med_i - lo_i), (y_i - hi_i)/(hi_i - med_i) ).

Both are distribution-free. A Gaussian-equivalent factor (1.6449 / z where
Phi(z) - Phi(-z) = 0.707) is printed for reference ONLY -- it is larger (~1.56),
because the residuals are not Gaussian, and we do not use it: the point is to
report the measured deficit, not a modelled one.

TRANSFER DISCLOSURE (state this wherever the widened interval is shown)
-----------------------------------------------------------------------
k is measured on the DAILY sensorless anchor and applied to the HOURLY
forecast anchor. Those are different models. It is the only OOD coverage deficit
that has ever been measured at Kandy -- there is no local hourly record to
calibrate against -- so the factor is a disclosed transfer, of the same status as
the B2 wind prior and the eps-floor: a bound taken from the nearest measurable
thing, not a Kandy-fitted quantity.

Run:  .venv/Scripts/python.exe scripts/kandy_forecast_ood_widening.py
Out:  data/processed/decomp/kandy_forecast_ood_widening.json  (consumed by the
      live runner via kandy_webapp/live/model/pack.json)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "processed" / "decomp" / "kandy_anchor_free_t.csv"
OUT = REPO / "data" / "processed" / "decomp" / "kandy_forecast_ood_widening.json"
NOMINAL = 0.90


def main() -> None:
    d = pd.read_csv(SRC).dropna(subset=["pm25_obs", "pred", "pi_lo", "pi_hi"])
    y = d.pm25_obs.to_numpy(float)
    med = d.pred.to_numpy(float)
    lo = d.pi_lo.to_numpy(float)
    hi = d.pi_hi.to_numpy(float)

    def coverage(k: float) -> float:
        return float(np.mean((y >= med - k * (med - lo)) & (y <= med + k * (hi - med))))

    cov1 = coverage(1.0)

    ks = np.arange(1.0, 4.0005, 0.0005)
    cov = np.array([coverage(k) for k in ks])
    hit = np.argmax(cov >= NOMINAL)
    k_search = float(ks[hit])

    lo_gap = np.maximum(med - lo, 1e-9)
    hi_gap = np.maximum(hi - med, 1e-9)
    s = np.maximum((lo - y) / lo_gap, (y - hi) / hi_gap)
    k_conformal = float(1.0 + np.quantile(s, NOMINAL))

    k_gauss = float(1.6449 / norm.ppf(0.5 + cov1 / 2.0))

    if abs(k_search - k_conformal) > 0.02:
        raise SystemExit(f"derivations disagree: search {k_search} vs conformal {k_conformal}")

    # round UP to 2 dp: rounding down would ship an interval narrower than the one
    # that was actually measured to reach nominal coverage.
    k = float(np.ceil(max(k_search, k_conformal) * 100.0) / 100.0)

    out = {
        "k": k,
        "nominal": NOMINAL,
        "measured_coverage_unwidened": round(cov1, 4),
        "coverage_at_k": round(coverage(k), 4),
        "k_direct_search": round(k_search, 3),
        "k_conformal": round(k_conformal, 3),
        "k_gaussian_equivalent_not_used": round(k_gauss, 3),
        "n_days": int(len(d)),
        "source": str(SRC.relative_to(REPO)).replace("\\", "/"),
        "basis": (
            "Kandy sensorless daily anchor: nominal 90% interval covers "
            f"{cov1:.1%} of the local record (n={len(d)} days). k is the inflation "
            "of the interval edges about the median that restores 90% coverage."
        ),
        "transfer_note": (
            "Measured on the DAILY sensorless anchor, applied to the HOURLY forecast "
            "anchor -- a disclosed transfer, not a Kandy-fitted quantity. It is the "
            "only OOD coverage deficit measurable at Kandy (no local hourly record). "
            "Same epistemic status as the B2 wind prior and the eps-floor."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")

    print(f"unwidened coverage      {cov1:.3f}  (nominal {NOMINAL})")
    print(f"k (direct search)       {k_search:.3f}")
    print(f"k (split-conformal)     {k_conformal:.3f}")
    print(f"k (Gaussian, NOT used)  {k_gauss:.3f}")
    print(f"-> shipped k = {k}  giving coverage {coverage(k):.3f} on n={len(d)} days")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
