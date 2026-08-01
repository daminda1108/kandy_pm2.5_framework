"""kandy_background_relevel.py — fix the low-season background over-estimate that
destroys the local increment from April onward (2026-07-27).

THE DEFECT (measured over all 66,193 shipped hours, 2019-2026)
--------------------------------------------------------------
B(t) is a DAILY-resolution background; T(t) is hourly. Nothing couples them, and in
the low season the background estimate is simply too large:

    monthly B/T (locked years):  Jan-Mar 0.53-0.63 | Apr 0.89 | May 0.97
                                 Jun-Aug 0.78-0.83 | Sep 1.11 | Oct 1.01 | Nov 0.96

    B > T in 28.5% of ALL hours (2-13% Jan-Mar, 27-48% from April)
    35.1% of hours below the SBI posterior's own lower bound f >= 0.10
    displayed local share goes NEGATIVE in Sep/Oct/Nov of most years

In May, September, October and November the MONTHLY MEAN background exceeds 90% of
the monthly mean total, so the incoherence is not merely an hourly sampling artefact.
Under the increment split every such hour renders spatially UNIFORM by construction:
the map loses its local structure and the background-vs-local panel reports zero or
negative local emission. That is the reported "since April" symptom, and it is
present in every year of the record, not only 2026.

Corroboration that the wet-season background specifically runs high: W2 (D2) puts the
observed JJA level near the pristine marine floor at ~7.4 ug/m3, while the model's JJA
background alone is 8.50.

THE FIX — seasonal re-level, ANNUAL MASS PRESERVED
--------------------------------------------------
Two stages, both mass-conserving so no published aggregate moves:

  1. MONTHLY: reduce any month whose B/T exceeds CAP_BT to exactly CAP_BT * T_m, and
     redistribute the removed mass across the months that have room, in proportion to
     their headroom, never pushing any month over the cap. The YEAR's mean background
     is preserved exactly, so the disclosed local fraction f is untouched.
  2. HOURLY: within each month, cap at (1 - F_MIN) * T(t) and rescale to hold the
     month's mean. After stage 1 every month sits at or below CAP_BT < 1 - F_MIN, so
     the headroom needed for this to be exact always exists.

Neither stage touches T, and the field is T-LOCKED (the increment split preserves
basin mean = T whatever B is), so annual means, the seasonal cycle of the total and
the level anchor are EXACTLY unchanged. What changes: the seasonal profile of the
background, the per-hour background/local split, and the spatial amplitude on the
affected hours (hence population-weighted exposure, slightly).

WHAT THIS SCRIPT DOES NOT DECIDE
--------------------------------
Redistributing wet-season background into the dry months alters the JJA/DJF background
ratio, which W2 reports against an observed 0.53. The script MEASURES that ratio before
and after and refuses to write if it moves away from the observation by more than
W2_TOL — the fix must not buy local structure at the cost of the transboundary result.

CHOOSING CAP_BT — measured, not picked
--------------------------------------
Annual mass conservation forces a trade: background removed from the low season has
to be given back somewhere, and wherever it goes it shrinks that month's local
increment. Swept over the whole record:

    CAP_BT   dry-season local share    low-season local share    W2 ratio drift
    0.85     0.322 -> 0.290  (-10%)    -0.079 -> +0.150          +0.057
    0.89     0.322 -> 0.319  ( -1%)    -0.079 -> +0.112          +0.026

0.89 takes almost all of the benefit for almost none of the collateral damage: the
dry season, which currently renders well, is left essentially untouched, while the
low season moves from a NEGATIVE (incoherent) local share to a coherent ~11%.

Residual: about 0.13% of hours still show B > T after the fix. Those are the ~90
deep-night hours per year where the raw T anchor itself dips slightly below zero
(a known locked-model artefact); the ceiling is a fraction of T and cannot lift a
negative total. They are already clamped at render.

Run:  .venv/Scripts/python.exe scripts/kandy_background_relevel.py [--apply]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

CAP_BT = 0.89         # monthly ceiling on B/T (swept; see the note below)
F_MIN = 0.10          # hourly floor on the local share (SBI posterior lower edge)
W2_OBS = 0.53         # observed JJA/DJF ratio (W2 D2, FECT by air-mass origin)
W2_TOL = 0.03         # refuse to write if the fix moves the ratio further than this

STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
EXT_YEARS = (2024, 2025, 2026)


def paths(year: int):
    s = "_drv" if year in EXT_YEARS else ""
    return (STG / "T_anchor" / f"T_kandy_hourly_{year}{s}.parquet",
            DEC / f"B_background_hourly_{year}_v2{s}.parquet")


def _monthly_relevel(B, T, month):
    """Stage 1: monthly B/T <= CAP_BT, year mean of B preserved exactly.

    The redistribution is MULTIPLICATIVE — one common factor s >= 1 applied to every
    month, each then clipped at its own ceiling:

        B*_m = min(s * B_m, CAP_BT * T_m),   s solved so that sum(B*_m n_m) is unchanged

    A first attempt distributed the removed mass in proportion to each month's
    HEADROOM instead. That is wrong in a way the gate caught: the months with the
    most headroom are Jan-Mar, so the wet-season excess piled into DJF and drove the
    W2 JJA/DJF background ratio from 0.544 to 0.447, away from the observed 0.53.
    The multiplicative form leaves the ratio between any two UNCAPPED months exactly
    unchanged, and only Apr/May/Sep/Oct/Nov are capped — none of which is in JJA or
    DJF — so the transboundary seasonal result survives.
    """
    out = B.copy()
    mo = np.unique(month)
    n = np.array([(month == m).sum() for m in mo], float)
    Bm = np.array([B[month == m].mean() for m in mo])
    Tm = np.array([T[month == m].mean() for m in mo])
    ceil = CAP_BT * Tm
    target = float((Bm * n).sum())
    if (Bm <= ceil + 1e-12).all():
        return out, {int(m): 1.0 for m in mo}
    if float((ceil * n).sum()) < target:
        raise SystemExit("even at the ceiling the year cannot hold its own background; "
                         "the annual partition is incoherent — that needs Consolidation "
                         "v3, not a re-level")
    lo, hi = 1.0, 2.0
    tot = lambda s: float((np.minimum(s * Bm, ceil) * n).sum())
    while tot(hi) < target and hi < 1e6:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if tot(mid) < target:
            lo = mid
        else:
            hi = mid
    s = 0.5 * (lo + hi)
    newBm = np.minimum(s * Bm, ceil)
    scale = {}
    for j, m in enumerate(mo):
        f = newBm[j] / Bm[j] if Bm[j] > 0 else 1.0
        out[month == m] = B[month == m] * f
        scale[int(m)] = float(f)
    return out, scale


def _hourly_cap(B, T, month):
    """Stage 2: hourly B <= (1-F_MIN)*T, each month's mean preserved by bisection."""
    out = B.copy()
    cap = (1.0 - F_MIN) * np.clip(T, 0, None)
    for m in np.unique(month):
        i = month == m
        target = B[i].mean()
        if cap[i].mean() <= target:                  # no headroom (should not happen)
            out[i] = np.minimum(B[i], cap[i])
            continue
        lo, hi = 1.0, 2.0
        while np.minimum(hi * B[i], cap[i]).mean() < target and hi < 1e6:
            hi *= 2.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if np.minimum(mid * B[i], cap[i]).mean() < target:
                lo = mid
            else:
                hi = mid
        out[i] = np.minimum(0.5 * (lo + hi) * B[i], cap[i])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--years", type=int, nargs="*", default=list(range(2019, 2027)))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"CAP_BT={CAP_BT}  F_MIN={F_MIN}  mode={'APPLY' if a.apply else 'DRY RUN'}\n")

    rows, frames = [], {}
    for y in a.years:
        tf, bf = paths(y)
        if not (tf.exists() and bf.exists()):
            continue
        T = pd.read_parquet(tf); B = pd.read_parquet(bf)
        T["h"] = pd.to_datetime(T.datetime_utc, utc=True)
        B["h"] = pd.to_datetime(B.datetime_utc, utc=True)
        m = B.merge(T[["h", "T_q50"]], on="h", how="left")
        if m.T_q50.isna().any():
            raise SystemExit(f"{y}: {int(m.T_q50.isna().sum())} hours have B but no T")
        raw = (m["B_uncapped"] if "B_uncapped" in m.columns else m["B"]).to_numpy(float)
        Tv = m.T_q50.to_numpy(float)
        month = m.h.dt.month.to_numpy()

        b1, scale = _monthly_relevel(raw, Tv, month)
        b2 = _hourly_cap(b1, Tv, month)
        frames[y] = (m, raw, b2, Tv, month)

        with np.errstate(divide="ignore", invalid="ignore"):
            sh0 = np.where(Tv > 0, (Tv - raw) / Tv, np.nan)
            sh1 = np.where(Tv > 0, (Tv - b2) / Tv, np.nan)
        rows.append({"year": y, "n": len(m),
                     "B ann before": raw.mean(), "B ann after": b2.mean(),
                     "B>T before %": 100 * (raw > Tv).mean(),
                     "B>T after %": 100 * (b2 > Tv).mean(),
                     "share<0.10 before %": 100 * float(np.nanmean(sh0 < F_MIN)),
                     "share<0.10 after %": 100 * float(np.nanmean(sh1 < F_MIN)),
                     "median share before": float(np.nanmedian(sh0)),
                     "median share after": float(np.nanmedian(sh1))})

    r = pd.DataFrame(rows)
    print(r.round(3).to_string(index=False))
    print(f"\nannual background drift: worst {np.abs(r['B ann after'] - r['B ann before']).max():.2e} ug/m3"
          "  (0 => the disclosed f partition is untouched)")

    # ── W2 gate: the JJA/DJF background ratio must not move away from the observation
    allm = pd.concat([pd.DataFrame({"mo": mo, "b0": b0, "b1": b1_})
                      for (_, b0, b1_, _, mo) in frames.values()], ignore_index=True)
    g = allm.groupby("mo").mean()
    jja, djf = [6, 7, 8], [12, 1, 2]
    before = g.loc[jja, "b0"].mean() / g.loc[djf, "b0"].mean()
    after = g.loc[jja, "b1"].mean() / g.loc[djf, "b1"].mean()
    print(f"\nW2 JJA/DJF background ratio: before {before:.3f} -> after {after:.3f} "
          f"(observed {W2_OBS})")
    ok = abs(after - W2_OBS) <= abs(before - W2_OBS) + W2_TOL
    print(f"W2 gate: {'PASS' if ok else 'FAIL'} (tolerance {W2_TOL})")

    print("\nmonthly B/T before -> after (locked years pooled)")
    gt = pd.concat([pd.DataFrame({"mo": mo, "b0": b0, "b1": b1_, "t": tv})
                    for (_, b0, b1_, tv, mo) in frames.values()], ignore_index=True
                   ).groupby("mo").mean()
    print(pd.DataFrame({"B/T before": gt.b0 / gt.t,
                        "B/T after": gt.b1 / gt.t}).round(3).to_string())

    if not ok:
        raise SystemExit("\nREFUSING to write: the re-level moves the W2 transboundary "
                         "ratio away from the observation. Local structure must not be "
                         "bought with the transboundary result.")
    if not a.apply:
        print("\ndry run — nothing written. Re-run with --apply.")
        return
    for y, (m, raw, b2, Tv, month) in frames.items():
        _, bf = paths(y)
        ratio = np.where(raw > 0, b2 / raw, 1.0)
        pd.DataFrame({"datetime_utc": m.datetime_utc.to_numpy(), "B": b2,
                      "B_lo": m.B_lo.to_numpy(float) * ratio,
                      "B_hi": m.B_hi.to_numpy(float) * ratio,
                      "B_uncapped": raw}).to_parquet(bf, index=False)
    print("\nWROTE re-levelled B parquets (B_uncapped preserved).")
    print("REBUILD IN FULL — a partial rebuild desyncs the exporter (gotcha #65):")
    print("  build_additive_field_v2.py -> build_additive_field_v3.py --city kandy")
    print("  -> webapp_export.py --city kandy  (QA gate)  -> exposure + health")


if __name__ == "__main__":
    main()
