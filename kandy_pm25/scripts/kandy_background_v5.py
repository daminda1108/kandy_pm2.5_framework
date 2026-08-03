"""kandy_background_v5.py — background as the persistent lower envelope of the total
(2026-08-03). ADOPTED.

WHY THIS FORM
-------------
The project's stated framework is Lenschow (2001): the urban background is the part of
the total that is present regardless of local activity — operationally, the persistent
LOWER ENVELOPE of the concentration record, not a fraction chosen in advance.

v2 did not do that. It set an annual level from a prior (`FRAC_LOCAL_YEAR`, 0.20-0.28)
and shaped it independently of T. The consequence is arithmetic, not stylistic: a
background that is flat within a day cannot exceed that day's minimum total, and the
shipped split violates that floor in **9 of 12 months** (April-December), annually
0.244 against a floor of 0.410, with the implied local share going NEGATIVE in
September (F.17). Under the increment split every such hour renders spatially uniform,
which is the "no emission structure since April" the user reported.

Four attempts to repair it by reparameterisation failed (F.13, F.15, F.17): with an
independently-levelled background you can have coherence OR f ~ 0.25, never both.
Estimating the envelope directly dissolves the conflict, because coherence stops being
a constraint to satisfy and becomes a property of the construction.

    B(t) = L(month) . G(day) . D(hour)

    L(month)  QLOW quantile of the hourly total within that month — the envelope
    G(day)    GEOS-CF daily prior, mean-1 within month. Kept because it is the only
              term with external support: r = +0.37 against the NBRO island network,
              where a background rebuilt from local meteorology scored -0.07 (F.15).
    D(hour)   (H_ref/BLH)^ALPHA, mean-1 within month — the dilution response whose
              absence produced B > T at midday. NOT normalised within each day: a
              daily-neutral factor cannot lower the midday background, which is the
              whole point (the mistake F.17 records).

    Each month is then rescaled so mean(B) over the month equals L(month) exactly.

WHAT MOVES, AND WHAT CANNOT
---------------------------
CANNOT: the field is T-LOCKED. The basin mean equals T(t) at every hour whatever B is,
so annual means, the seasonal cycle, the level anchor, exposure and burden are
arithmetically unchanged. Verified, not assumed.

MOVES: the background series; the displayed background/local split; the spatial
amplitude on hours that were previously rendered flat; and the local fraction f, which
becomes an OUTPUT (~0.4 rather than the 0.24 prior). That is a change to a published
claim and is reported, not hidden -- see the checklist this script prints.

Run:  .venv/Scripts/python.exe scripts/kandy_background_v5.py [--apply]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kandy_background_v4 import (DEC, EXT, LOCKED, H_REF, daily_class,  # noqa: E402
                                 geos_daily, geos_doy_climatology, load_year)

OUT = DEC / "kandy_background_v5.json"
ALPHA = 0.35              # dilution exponent (swept below; reported, not tuned to a gate)
COHERENCE_MAX_PCT = 3.0   # ~1.8% is irreducible: T itself dips below the measured floor


def build(d: pd.DataFrame, g: pd.Series, qlow: float, alpha: float) -> np.ndarray:
    x = d.copy()
    x["mo"] = x.h.dt.month
    gg = pd.Series(np.asarray(x.date.map(g), float))
    gg = gg.fillna(gg.mean() if gg.notna().any() else 1.0).to_numpy()
    D = (H_REF / x.blh.to_numpy(float)) ** alpha
    T = x.T_q50.to_numpy(float)
    B = np.zeros(len(x))
    for m in range(1, 13):
        i = (x.mo == m).to_numpy()
        if not i.any():
            continue
        lvl = float(np.nanquantile(np.clip(T[i], 0, None), qlow))   # the envelope
        gm = gg[i] / (np.nanmean(gg[i]) or 1.0)
        dm = D[i] / (np.nanmean(D[i]) or 1.0)
        b = lvl * gm * dm
        b *= lvl / (b.mean() or 1.0)          # month mean == the envelope exactly
        B[i] = b
    return np.clip(B, 0.05, None)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== B(t) v5: background as the persistent lower envelope (Lenschow) ===")

    ref = load_year(2022)
    blh_ref = ref.assign(mo=ref.h.dt.month, hh=ref.h.dt.hour).groupby(
        ["mo", "hh"]).blh.mean().to_dict()
    data, geos = {}, {}
    for y in LOCKED + EXT:
        try:
            data[y] = load_year(y, blh_ref)
            geos[y] = geos_daily(y)
        except FileNotFoundError:
            continue
    clim = geos_doy_climatology(sorted(data))
    for y, d in data.items():
        if len(geos[y]) <= 100 and len(clim):
            doy = pd.to_datetime(pd.Series(sorted(d.date.unique()))).dt.dayofyear
            geos[y] = pd.Series(clim.reindex(doy).to_numpy(),
                                index=pd.Index(sorted(d.date.unique()), name="date"))
    print(f"  years: {sorted(data)}")

    def evaluate(qlow, alpha):
        Bs, Ts, mos = [], [], []
        for y, d in data.items():
            Bs.append(build(d, geos[y], qlow, alpha))
            Ts.append(d.T_q50.to_numpy(float)); mos.append(d.h.dt.month.to_numpy())
        B, T, mo = map(np.concatenate, (Bs, Ts, mos))
        return B, T, mo

    print("\n  sweep: envelope quantile x dilution exponent")
    print("    qlow  alpha   B>T %    f annual   JJA/DJF")
    rows = []
    for qlow in (0.05, 0.10, 0.15, 0.20, 0.25):
        for alpha in (0.0, 0.35, 0.7):
            B, T, mo = evaluate(qlow, alpha)
            g = pd.DataFrame({"B": B, "mo": mo}).groupby("mo").B.mean()
            rows.append({"qlow": qlow, "alpha": alpha,
                         "bt_pct": round(100 * float((B > T).mean()), 2),
                         "f": round(float(1 - B.mean() / T.mean()), 3),
                         "w2": round(float(g.loc[[6, 7, 8]].mean() / g.loc[[12, 1, 2]].mean()), 3)})
            print(f"    {qlow:.2f}  {alpha:.2f}  {rows[-1]['bt_pct']:6.2f}    "
                  f"{rows[-1]['f']:.3f}     {rows[-1]['w2']:.3f}")

    sweep = pd.DataFrame(rows)
    ok = sweep[sweep.bt_pct <= COHERENCE_MAX_PCT].sort_values("f")
    if ok.empty:
        raise SystemExit("no (qlow, alpha) reaches coherence")
    # the LARGEST background that stays coherent = the smallest f: a background should be
    # as large as the data permits, not as small as the solver can make it
    pick = ok.iloc[0]
    qlow, alpha = float(pick.qlow), float(pick.alpha)
    B, T, mo = evaluate(qlow, alpha)
    print(f"\n  adopted: qlow={qlow:.2f} alpha={alpha:.2f} -> "
          f"B>T {pick.bt_pct:.2f}%, f={pick.f:.3f}, JJA/DJF={pick.w2:.3f}")

    g = pd.DataFrame({"B": B, "T": T, "mo": mo}).groupby("mo").mean()
    fmo = (1 - g.B / g["T"])
    print("\n  monthly f (OUTPUT):", " ".join(f"{m}:{v:.2f}" for m, v in fmo.round(2).items()))
    print("  monthly B/T      :", " ".join(f"{m}:{v:.2f}" for m, v in (g.B / g["T"]).round(2).items()))

    per_year = {}
    for y, d in data.items():
        Bv = build(d, geos[y], qlow, alpha)
        per_year[y] = (d, Bv)
    res = {"form": "B = L(month quantile of T) * G(day) * D(hour)",
           "qlow": qlow, "alpha": alpha,
           "f_annual_pooled": round(float(1 - B.mean() / T.mean()), 3),
           "f_by_year": {str(y): round(float(1 - b.mean() / d.T_q50.mean()), 3)
                         for y, (d, b) in per_year.items()},
           "f_monthly": {int(k): round(float(v), 3) for k, v in fmo.items()},
           "coherence_pct": round(100 * float((B > T).mean()), 2),
           "w2_jja_djf": round(float(pick.w2), 3),
           "sweep": rows,
           "supersedes": "FRAC_LOCAL_YEAR prior (0.20-0.28); f is now an output",
           "claims_to_update": [
               "preprint: the ~25% local / ~75% regional split becomes ~%d%% / ~%d%%"
               % (round(100 * float(1 - B.mean() / T.mean())),
                  round(100 * B.mean() / T.mean())),
               "preprint S1 sensitivity: the f sweep range must cover the new value",
               "preprint W2: the JJA/DJF background ratio is revised (was 0.53 observed)",
               "model reference IV.3.3 + ledger F.3: f is an OUTPUT, not a prior",
               "T-locked quantities (annual means, exposure, burden) are UNCHANGED"]}
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\n  f by year: {res['f_by_year']}")
    print(f"\nwrote {OUT.name}")
    print("\n  CLAIMS THAT MUST BE UPDATED IF THIS SHIPS:")
    for c in res["claims_to_update"]:
        print(f"    - {c}")

    if not a.apply:
        print("\ndry run — no parquets written.")
        return
    for y, (d, Bv) in per_year.items():
        s = "_drv" if y in EXT else ""
        pd.DataFrame({"datetime_utc": d.datetime_utc.to_numpy(), "B": Bv,
                      "B_lo": 0.70 * Bv, "B_hi": 1.25 * Bv}
                     ).to_parquet(DEC / f"B_background_hourly_{y}_v2{s}.parquet", index=False)
    print("\nwrote B_background_hourly_*_v2*.parquet (v5 content, v2 filename so the")
    print("existing chain consumes it). REBUILD IN FULL — partial rebuilds desync (gotcha #65):")
    print("  build_additive_field_v2.py -> build_additive_field_v3.py --city kandy")
    print("  -> webapp_export.py --city kandy (QA gate) -> exposure_weighting + health_burden")


if __name__ == "__main__":
    main()
