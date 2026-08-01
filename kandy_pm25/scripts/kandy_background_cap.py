"""kandy_background_cap.py — enforce the disclosed local-share floor on B(t)
(2026-07-27, after a user report that emission structure disappears from April).

THE DEFECT
----------
B(t) is built at DAILY resolution (a rural satellite floor shaped by the seasonal
cycle and air-mass origin) while T(t) is hourly with a large diurnal swing. Nothing
in the chain couples them, so on hours when T dips — midday convective mixing, and
the whole low season when the basin level falls to ~10 ug/m3 — the daily background
can exceed the hourly total.

Measured over the shipped payload (2019-2026, all 8 years):

    B > T in 28.5% of ALL hours
    by month: ~2-13% Jan-Mar, then 27-48% in April and high through November
    displayed local share (T-B)/T goes NEGATIVE in Sep/Oct/Nov of most years
    35.1% of hours sit below the f-posterior's own lower bound of 0.10

A background larger than the total is not a small numerical artefact: it is an
incoherent partition. Under the increment split those hours render spatially
UNIFORM by construction, so the map loses its local structure and the
background-vs-local panel reports zero or negative local emission — which is what
a viewer sees, seasonally, from April onward.

This is the documented hourly-T x daily-B seam. The architectural fix is
Consolidation v3 (an hourly semi-mechanistic background), which is deliberately
parked post-preprint. This script is the bounded interim fix.

THE FIX — a MASS-CONSERVING cap
-------------------------------
    B'(t) = min( s_m * B(t), (1 - F_MIN) * T(t) ),   F_MIN = 0.10

with one scale factor s_m per calendar month, solved by bisection so that

    mean_m( B' ) == mean_m( B )      exactly, every month

F_MIN is NOT a new free parameter: 0.10 is the lower edge of the project's own
published SBI posterior for the local fraction, f = 0.181 [0.10, 0.27] (Track I).
The model's partition should never place the local share below the band it
publishes.

The mass conservation matters more than it first appears. A PLAIN cap (no
rescaling) was tried first and rejected on measurement: it removed 12% of the
annual background (2019: 14.16 -> 12.45), which would have raised the implied
annual local fraction from the disclosed ~0.24 to ~0.32 — outside our own SBI band
and inconsistent with the f prior the preprint discloses. Fixing an hourly
incoherence must not silently rewrite the annual partition. Conserving the MONTHLY
mean also preserves the seasonal partition the extension tier inherits (gotcha #61).

Physically the operation is a redistribution: hours whose daily-resolution
background cannot fit under the hourly total give their excess to the hours in the
same month that have room for it.

WHY IT IS SAFE
--------------
The field is T-LOCKED: under the increment split the basin mean equals T(t) at
every hour whatever B is, so every published T-locked quantity — the annual means,
the seasonal cycle, the level anchor — is EXACTLY unchanged. With monthly mass
conservation the background series keeps its mean at monthly resolution too, so the
f-partition and the seasonal B/T profile are preserved. What moves is the spatial
amplitude on the affected hours (and therefore population-weighted exposure,
slightly) and the per-hour background/local split. Both are measured by the caller.

The uncapped series is preserved as `B_uncapped` in every parquet, so the change is
auditable and reversible.

Run:  .venv/Scripts/python.exe scripts/kandy_background_cap.py [--apply] [--city kandy]
      (default is a DRY RUN that only reports)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

F_MIN = 0.10          # lower edge of the SBI posterior f = 0.181 [0.10, 0.27]

STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
EXT_YEARS = (2024, 2025, 2026)


def _capped_mass_conserving(raw, cap, month):
    """min(s*raw, cap) with one s per month, chosen so each month's mean is kept.

    mean(min(s*raw, cap)) rises monotonically with s and saturates at mean(cap), so
    a bisection is exact and cheap. If a month has no headroom at all
    (mean(cap) < target) the month is left with the plain cap and reported by the
    caller — silently rescaling past the ceiling would reintroduce B > T.
    """
    out = raw.copy()
    for mm in np.unique(month):
        i = month == mm
        target = raw[i].mean()
        if cap[i].mean() <= target:                 # no headroom: plain cap
            out[i] = np.minimum(raw[i], cap[i])
            continue
        lo, hi = 1.0, 2.0
        while np.minimum(hi * raw[i], cap[i]).mean() < target and hi < 1e6:
            hi *= 2.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if np.minimum(mid * raw[i], cap[i]).mean() < target:
                lo = mid
            else:
                hi = mid
        out[i] = np.minimum(0.5 * (lo + hi) * raw[i], cap[i])
    return out


def paths(city: str, year: int):
    if city != "kandy":
        raise SystemExit("only kandy is wired here; port deliberately, with its own gate")
    s = "_drv" if year in EXT_YEARS else ""
    return (STG / "T_anchor" / f"T_kandy_hourly_{year}{s}.parquet",
            DEC / f"B_background_hourly_{year}_v2{s}.parquet")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="kandy")
    ap.add_argument("--apply", action="store_true", help="write the capped parquets")
    ap.add_argument("--years", type=int, nargs="*",
                    default=list(range(2019, 2027)))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(f"local-share floor F_MIN = {F_MIN}  (SBI posterior lower edge)")
    print(f"mode: {'APPLY' if a.apply else 'DRY RUN'}\n")
    rows = []
    for y in a.years:
        tf, bf = paths(a.city, y)
        if not (tf.exists() and bf.exists()):
            continue
        T = pd.read_parquet(tf)
        B = pd.read_parquet(bf)
        T["h"] = pd.to_datetime(T.datetime_utc, utc=True)
        B["h"] = pd.to_datetime(B.datetime_utc, utc=True)
        m = B.merge(T[["h", "T_q50"]], on="h", how="left")
        if m.T_q50.isna().any():
            raise SystemExit(f"{y}: {m.T_q50.isna().sum()} hours have B but no T")

        raw = (m["B_uncapped"] if "B_uncapped" in m.columns else m["B"]).to_numpy(float)
        cap = ((1.0 - F_MIN) * m.T_q50.clip(lower=0)).to_numpy(float)
        month = m.h.dt.month.to_numpy()
        new = _capped_mass_conserving(raw, cap, month)
        bound = new < raw - 1e-9
        incoh = raw > m.T_q50.to_numpy(float)

        Tv = m.T_q50.to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            sh_before = np.where(Tv > 0, (Tv - raw) / Tv, np.nan)
            sh_after = np.where(Tv > 0, (Tv - new) / Tv, np.nan)
        # monthly mass conservation check (the whole point of the rescale)
        mo = pd.DataFrame({"m": m.h.dt.month, "a": raw, "b": new}).groupby("m").mean()
        drift = float(np.abs(mo.a - mo.b).max())
        rows.append({"year": y, "n": len(m),
                     "B>T before %": 100 * incoh.mean(),
                     "B>T after %": 100 * float((new > Tv).mean()),
                     "adjusted %": 100 * bound.mean(),
                     "B mean before": float(raw.mean()),
                     "B mean after": float(new.mean()),
                     "max monthly drift": drift,
                     "share<0.10 before %": 100 * float(np.nanmean(sh_before < F_MIN)),
                     "share<0.10 after %": 100 * float(np.nanmean(sh_after < F_MIN))})

        if a.apply:
            out = pd.DataFrame({
                "datetime_utc": m.datetime_utc.to_numpy(),
                "B": new,
                # intervals keep their multiplicative relationship to the shipped B
                "B_lo": new * (m.B_lo.to_numpy(float) / raw.to_numpy(float)),
                "B_hi": new * (m.B_hi.to_numpy(float) / raw.to_numpy(float)),
                "B_uncapped": raw.to_numpy(float)})
            out.to_parquet(bf, index=False)

    r = pd.DataFrame(rows)
    print(r.round(2).to_string(index=False))
    print(f"\ntotal hours adjusted: {r['adjusted %'].mul(r.n).sum() / r.n.sum():.1f}% "
          f"of {int(r.n.sum()):,}   |   worst monthly mean drift "
          f"{r['max monthly drift'].max():.2e} ug/m3")
    if a.apply:
        print("\nWROTE capped B parquets (B_uncapped preserved).")
        print("NOW REBUILD, in order — a partial rebuild desyncs the exporter (gotcha #65):")
        print("  build_additive_field_v2.py  ->  build_additive_field_v3.py --city kandy")
        print("  ->  webapp_export.py --city kandy   (QA gate must PASS)")
        print("  ->  exposure_weighting.py + health_burden.py")
    else:
        print("\ndry run — nothing written. Re-run with --apply.")


if __name__ == "__main__":
    main()
