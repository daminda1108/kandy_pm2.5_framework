"""PHASE 2, L3 — does the gauge hold in floating point?

Registered prediction L3 at https://osf.io/2jyfg/:

    |mean_cells(P) - 1| < 1e-9 at every hour.

WHY THIS IS A SEPARATE SCRIPT. The primary metric of Phase 2 is a per-city Spearman rank
correlation, and softmax is monotone within a city, so the metric is INVARIANT to the gauge.
Claiming the gauge through the scoring would be claiming credit for something the scoring
cannot see. What the gauge actually buys is that the learned pattern is usable as a FIELD: the
spatial mean returns the temporal anchor exactly, so a badly learned pattern misplaces material
and can never corrupt the basin mean. That is a property of the construction and it is checked
here, directly, on the construction.

The check is deliberately adversarial. A softmax over cells is exactly unit-mean in real
arithmetic; the question is whether it survives float64 at realistic grid sizes and with
realistic logit ranges, including the degenerate cases a learner can actually produce -- a
saturated pattern where one cell takes almost all the weight, and a dead pattern where the
logits are constant.

Usage: .venv/Scripts/python.exe scripts/phase2_gauge_check.py
Out:   data/processed/paper_figures/phase2_gauge.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from figdata import emit  # noqa: E402

TOL = 1e-9


def pattern(logits: np.ndarray) -> np.ndarray:
    """P = N * softmax(logits) over cells. Max-subtraction is required, not cosmetic:
    without it a logit range a learner can reach overflows exp() and returns NaN."""
    z = logits - logits.max()
    e = np.exp(z)
    return e.size * e / e.sum()


def field(B, inc, P, eps=0.0):
    """The shipped decomposition. Its spatial mean must return B + inc for any P."""
    return B + np.maximum(inc, 0.0) * P + min(inc, 0.0) + eps * (P - 1.0)


def main() -> int:
    rng = np.random.default_rng(0)
    print("PHASE 2 L3 -- gauge check  (registered at osf.io/2jyfg)\n")

    cases = {
        "typical 16x16": rng.normal(0, 1, (16, 16)),
        "typical 64x64": rng.normal(0, 1, (64, 64)),
        "large 256x256": rng.normal(0, 1, (256, 256)),
        "wide logits (sd 12)": rng.normal(0, 12, (64, 64)),
        "saturated (one cell +40)": np.r_[40.0, np.zeros(64 * 64 - 1)].reshape(64, 64),
        "dead (all equal)": np.zeros((64, 64)),
        "extreme (sd 200)": rng.normal(0, 200, (64, 64)),
    }

    worst_p, worst_f, rows = 0.0, 0.0, []
    print(f"  {'case':<26}{'|mean(P)-1|':>14}{'max P':>10}{'|field gauge|':>15}")
    for name, lg in cases.items():
        P = pattern(lg)
        dp = abs(float(P.mean()) - 1.0)
        # and the property that actually matters: the field's spatial mean returns the anchor
        B, inc = 12.0, 9.0
        F = field(B, inc, P, eps=3.69)
        df = abs(float(F.mean()) - (B + inc))
        worst_p, worst_f = max(worst_p, dp), max(worst_f, df)
        rows.append((name, dp, float(P.max()), df))
        print(f"  {name:<26}{dp:>14.2e}{P.max():>10.1f}{df:>15.2e}")

    # a ventilated hour: inc < 0, where the increment split applies and P must not structure it
    P = pattern(rng.normal(0, 1, (64, 64)))
    Fv = field(12.0, -4.0, P, eps=0.0)
    dv = abs(float(Fv.mean()) - (12.0 - 4.0))
    print(f"\n  ventilated hour (inc < 0)      {dv:.2e}   "
          f"spread {Fv.max() - Fv.min():.2e}  (must be flat)")

    held = worst_p < TOL and worst_f < TOL and dv < TOL
    print(f"\n=== REGISTERED PREDICTION L3 ===")
    print(f"  L3  {'HELD    ' if held else 'REFUTED '}  worst |mean(P)-1| = {worst_p:.2e}, "
          f"worst field drift = {max(worst_f, dv):.2e}, tolerance {TOL:.0e}")
    if held:
        print("\n  The gauge is exact by construction and survives every degenerate case a\n"
              "  learner can produce, including a saturated pattern and an overflow-range\n"
              "  logit field. A learned pattern can misplace material; it cannot create it.")

    emit("phase2_gauge",
         worst_pattern_drift=float(worst_p),
         worst_field_drift=float(max(worst_f, dv)),
         ventilated_spread=float(Fv.max() - Fv.min()),
         tolerance=TOL, cases=len(cases), l3_held=bool(held))
    return 0 if held else 1


if __name__ == "__main__":
    sys.exit(main())
