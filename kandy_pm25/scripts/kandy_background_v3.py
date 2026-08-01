"""kandy_background_v3.py — Consolidation v3: an HOURLY semi-mechanistic background
(2026-08-01).

WHY THE DAILY BACKGROUND HAD TO GO
----------------------------------
B(t) v2 is built at DAILY resolution: an origin-conditioned regional level modulated
by a daily chemistry shape. T(t) is hourly with a large diurnal swing. Nothing couples
them, so B exceeds T whenever T dips — B > T in **28.5%** of all shipped hours, rising
to 27-48% from April, with monthly-mean B/T reaching **1.11 in September** (F.13). Under
the increment split those hours render spatially uniform, which is the reported "no
emission structure since April". Three independent lines say the wet-season background
is simply too high:

  1. internal coherence   B > T 28.5% of hours, monthly B/T -> 1.14              (F.13)
  2. W2 (D2)              model JJA background 8.50 vs observed ~7.4
  3. NBRO island network  B = 1.51x the LCS-corrected regional floor, n=44 days  (F.14)

THE MISSING PHYSICS
-------------------
The diagnosis is not that the background's ANNUAL level is wrong — F.14 corroborates it
(B sits at 1.12x the network P25, where a rural floor belongs). It is that B carries **no
dilution response**. Surface concentration of an advected layer scales roughly inversely
with mixing depth; T has that response and B does not, so at midday T falls and B does
not follow. Adding the term is both the physical fix and the coherence fix.

    B(t) = L_class(t) . D(t) . W(t),   normalised so each class keeps its mean level

    D(t) = (H_ref / H(t))^alpha        dilution by boundary-layer depth
    W(t) = exp(-kappa . R(t))          wet removal, R = rain decayed with memory TAU

alpha = 0 recovers v2 exactly (no dilution response). alpha = 1 is a perfectly mixed
layer. The regional background is a deep advected layer, not confined to the boundary
layer, so the physical expectation is 0 < alpha < 1.

FIRST FORMULATION — BUILT AND REFUTED BY ITS OWN GATES (2026-08-01)
------------------------------------------------------------------
The first version rebuilt B from scratch as L_class . D . W, fitting alpha/kappa/tau to
the NBRO floor. It failed, and the failure is the useful part:

  * alpha saturated at the grid edge (0.80) — the classic sign of a term being asked to
    do work it cannot do (cf. the SharedTerrainAnsatz diagnostic, all 6 params bound-hit)
  * coherence barely moved: B > T 28.5% -> 21.8%, still a FAIL
  * W2 JJA/DJF 0.427 vs observed 0.53 — a FAIL
  * **correlation against the NBRO floor fell to r = -0.07**, against **+0.37 for the
    v2 daily background** it replaced

The last point is the finding. **The regional background's day-to-day variation is set by
what is ADVECTED IN — chemistry and transport, which the GEOS-CF daily shape captures —
not by local dilution and washout.** That is what a background should do: it is
determined upwind. Rebuilding it from local meteorology throws away real information.
It also shows the seam is not mainly a diurnal-SHAPE problem but a low-season LEVEL one.

SECOND FORMULATION — the one implemented below
----------------------------------------------
Keep everything that has external support, add only the physics that is missing:

    B_v3(t) = B_v2(t) . D(t) / mean_day(D)        D(t) = (H_ref / H(t))^alpha

D is normalised WITHIN EACH DAY, so every daily mean of B is preserved EXACTLY. Three
consequences, all by construction rather than by fitting:
  * the daily series is untouched -> the r = +0.37 external agreement is preserved
  * f is untouched -> the disclosed partition does not move
  * the W2 JJA/DJF ratio is untouched -> the transboundary result cannot be bought
Only the DIURNAL distribution of the background changes: it falls when the mixing depth
grows, which is exactly when T falls, and rises at night. That is the missing response.

alpha is then set as the SMALLEST exponent that makes the partition coherent — the
minimal physical intervention, reported as a curve rather than a single fitted value.

RESULT: ALSO REFUTED. NO alpha achieves coherence (2026-08-01)
--------------------------------------------------------------
    alpha   0.0    0.2    0.4    0.6    0.8    1.0
    B > T  28.6%  28.1%  27.8%  28.0%  28.5%  29.1%
    swing   3.65   9.27  14.73  19.70  24.18  28.19  ug/m3

Coherence is FLAT in alpha and slightly WORSE at the top end, even with a background
diurnal swing of 28 ug/m3 — physically absurd and still no gain. The reason is that B
and T already share their diurnal driver: giving the background its own BLH response
moves it up at night and down at midday, which is exactly what T does, so B/T barely
changes; and at large alpha the background's night peak overshoots T, creating NEW
incoherent hours at night to replace the ones fixed at midday.

**The seam is a LEVEL problem, not a phase problem.** Three formulations have now been
built and rejected on measurement rather than on argument:

  1. mass-conserving seasonal re-level   fixes coherence, costs dry-season structure (F.13)
  2. background rebuilt from local physics   external r -0.07 vs +0.37; coherence + W2 FAIL
  3. diurnal dilution added to v2 (here)     coherence unchanged at every alpha

The only lever left is the low-season LEVEL of B, and lowering it necessarily raises f
above its disclosed band. That is not a modelling choice that can be made from the
model's own internals — and the one external measurement we have (F.14) covers only the
WET season, so it cannot say whether the compensating rise in the DRY-season background
is right or wrong. The NBRO log accumulates DJF coverage from December; that is the
measurement which decides it.

GATE (never fitted to): hourly coherence B <= (1-F_MIN).T; the W2 JJA/DJF background
ratio against the observed 0.53; and T-lock exactness after the field rebuild.

REPORT, do not impose: the resulting local fraction f. In v2, f is an INPUT prior
(FRAC_LOCAL_YEAR, 0.20-0.28) that the claim audit called the weakest number in the
chain. Here the background level is set by physics plus an external measurement, and f
comes out the other end. If it moves outside the disclosed band, that is a finding to
publish, not an error to suppress.

Run:  .venv/Scripts/python.exe scripts/kandy_background_v3.py [--fit] [--apply]
Out:  data/processed/decomp/kandy_background_v3.json  (params + gates + diagnostics)
      B_background_hourly_{year}_v3.parquet           (only with --apply)
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

STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
DRV = REPO / "data" / "external" / "kandy" / "extended_gee" / "drive"
IMERG = REPO / "data" / "external" / "tier_c" / "gpm_imerg"
TRAJ = DEC / "w2" / "d1_trajectories_850.parquet"
NBRO_JSON = DEC / "kandy_background_nbro_check.json"
OUT = DEC / "kandy_background_v3.json"

LOCKED = list(range(2019, 2024))
EXT = [2024, 2025, 2026]
MARINE_SECTORS = {"SW_marine"}
B_MARINE = 6.5            # marine-sector floor, unchanged from v2
H_REF = 500.0             # reference mixing depth (m) for the dilution term
F_MIN = 0.10              # coherence gate: local share must not fall below the SBI floor
W2_OBS = 0.53             # observed JJA/DJF background ratio (W2 D2)
W2_TOL = 0.06
LCS_SLOPE = 1.35          # low-cost-sensor over-read assumed for the NBRO network


# ── inputs ───────────────────────────────────────────────────────────────────
def daily_class() -> pd.DataFrame:
    t = pd.read_parquet(TRAJ)
    t["date"] = pd.to_datetime(t["date"])
    dom = t.groupby("date").sector.agg(lambda s: s.mode().iloc[0]).rename("sector").reset_index()
    dom["month"] = dom.date.dt.month
    dom["marine"] = dom.apply(
        lambda r: (r.sector in MARINE_SECTORS)
        or (r.sector == "BoB_marine" and r.month in (6, 7, 8, 9)), axis=1)
    return dom[["date", "marine"]]


def _blh_climatology(idx: pd.DatetimeIndex, ref: pd.DataFrame) -> np.ndarray:
    c = ref.groupby([ref.h.dt.month, ref.h.dt.hour]).blh.mean()
    key = list(zip(idx.month, idx.hour))
    return np.array([c.get(k, ref.blh.mean()) for k in key], float)


def load_met(year: int, ref: pd.DataFrame | None = None) -> pd.DataFrame:
    """Hourly area-mean BLH + rain on the T-anchor clock, for locked and extension years."""
    ig = STG / f"inference_grid_{year}_s12451.parquet"
    if ig.exists():
        m = pd.read_parquet(ig, columns=["datetime_utc", "blh_m", "tp", "wind_speed_10m"])
        m["h"] = pd.to_datetime(m.datetime_utc, utc=True)
        g = m.groupby("h").agg(blh=("blh_m", "mean"), tp=("tp", "mean"),
                               wspd=("wind_speed_10m", "mean")).reset_index()
    else:
        e = pd.read_csv(DRV / f"kandy_era5land_{year}.csv")
        e["h"] = pd.to_datetime(e.datetime).dt.tz_localize("UTC")
        e["wspd"] = np.hypot(e.u_component_of_wind_10m, e.v_component_of_wind_10m)
        gf = DRV / f"kandy_geoscf_{year}.csv"
        g = pd.DataFrame({"h": e.h, "tp": 0.0, "wspd": e.wspd})
        blh = pd.Series(np.nan, index=e.index)
        if gf.exists():
            gg = pd.read_csv(gf)
            if len(gg) > 100:
                gg["h"] = pd.to_datetime(gg.datetime).dt.tz_localize("UTC")
                blh = e[["h"]].merge(gg[["h", "ZPBL"]], on="h", how="left").ZPBL
        g["blh"] = blh.to_numpy()
        if g.blh.isna().mean() > 0.5 and ref is not None:
            g["blh"] = _blh_climatology(pd.DatetimeIndex(g.h), ref)
    # IMERG rain (the shipped source; ERA5-Land tp is rejected — gotcha #63)
    ip = IMERG / f"gpm_imerg_{year}.csv"
    if ip.exists():
        r = pd.read_csv(ip)
        tcol = [c for c in r.columns if "time" in c.lower() or "date" in c.lower()][0]
        pcol = [c for c in r.columns if "precip" in c.lower()][0]
        r["h"] = pd.to_datetime(r[tcol], utc=True, errors="coerce").dt.floor("h")
        rr = r.groupby("h")[pcol].mean().rename("rain").reset_index()
        g = g.merge(rr, on="h", how="left")
    if "rain" not in g.columns:
        g["rain"] = np.nan
    g["rain"] = g.rain.fillna(0.0).clip(lower=0)
    g["blh"] = g.blh.clip(lower=50.0)
    return g


def load_T(year: int) -> pd.DataFrame:
    s = "_drv" if year in EXT else ""
    t = pd.read_parquet(STG / "T_anchor" / f"T_kandy_hourly_{year}{s}.parquet")
    t["h"] = pd.to_datetime(t.datetime_utc, utc=True)
    return t[["h", "datetime_utc", "T_q50"]]


# ── the background ───────────────────────────────────────────────────────────
def rain_memory(rain: np.ndarray, tau_h: float) -> np.ndarray:
    """Exponentially decayed recent rain: wet removal persists past the shower."""
    lam = np.exp(-1.0 / max(tau_h, 1e-6))
    out = np.zeros_like(rain, dtype=float)
    acc = 0.0
    for i, r in enumerate(rain):
        acc = acc * lam + float(r)
        out[i] = acc
    return out


def build_B_v3(Bv2: np.ndarray, blh: np.ndarray, day: np.ndarray,
               alpha: float) -> np.ndarray:
    """B_v2 modulated by a within-day dilution response. Daily means preserved exactly.

    D = (H_ref/BLH)^alpha, renormalised to mean 1 within each calendar day, so the
    background acquires a diurnal cycle without any daily/seasonal/annual quantity
    moving. alpha = 0 returns B_v2 unchanged.
    """
    D = (H_REF / np.clip(blh, 50.0, None)) ** alpha
    out = np.empty_like(D)
    df = pd.DataFrame({"d": day, "D": D})
    m = df.groupby("d").D.transform("mean").to_numpy()
    out = Bv2 * D / np.where(m > 0, m, 1.0)
    return np.clip(out, 0.05, None)


def build_B(T: pd.DataFrame, met: pd.DataFrame, cls: pd.DataFrame,
            alpha: float, kappa: float, tau: float,
            level_marine: float, level_cont: float) -> np.ndarray:
    d = T.merge(met, on="h", how="left")
    d["date"] = d.h.dt.tz_convert("UTC").dt.floor("D").dt.tz_localize(None)
    d = d.merge(cls, on="date", how="left")
    d["marine"] = d.marine.fillna(False)
    d["blh"] = d.blh.interpolate(limit_direction="both").fillna(H_REF)
    d["rain"] = d.rain.fillna(0.0)

    D = (H_REF / d.blh.to_numpy(float)) ** alpha
    W = np.exp(-kappa * rain_memory(d.rain.to_numpy(float), tau))
    shape = D * W
    lvl = np.where(d.marine.to_numpy(bool), level_marine, level_cont)
    B = lvl * shape
    # normalise the shape to mean 1 WITHIN each class, so the class levels keep their
    # meaning and the dilution/washout terms only redistribute in time
    for flag, want in ((True, level_marine), (False, level_cont)):
        i = d.marine.to_numpy(bool) == flag
        if i.sum() and B[i].mean() > 0:
            B[i] *= want / B[i].mean()
    return np.clip(B, 0.05, None)


# ── external target ──────────────────────────────────────────────────────────
def nbro_daily_target() -> pd.DataFrame:
    """LCS-corrected regional floor from the NBRO network (see F.14)."""
    csv = DEC / "kandy_background_nbro_check.csv"
    if not csv.exists():
        raise SystemExit("run scripts/kandy_background_nbro_check.py first")
    d = pd.read_csv(csv, parse_dates=["date"])
    # the check writes tz-aware dates; strip tz so both sides of the join are naive
    d["date"] = pd.to_datetime(d.date, utc=True).dt.tz_localize(None)
    d["target"] = d.p25 / LCS_SLOPE
    return d[["date", "target"]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== Consolidation v3: hourly semi-mechanistic background ===")

    cls = daily_class()
    years = LOCKED + EXT
    ref_met = load_met(2022)
    ref_met["h"] = pd.to_datetime(ref_met.h, utc=True)
    data = {}
    for y in years:
        try:
            T = load_T(y)
        except FileNotFoundError:
            continue
        met = load_met(y, ref=ref_met)
        data[y] = (T, met)
    print(f"  loaded {len(data)} years: {sorted(data)}")

    tgt = nbro_daily_target()
    print(f"  external target: {len(tgt)} NBRO days, mean {tgt.target.mean():.2f} ug/m3 "
          f"(P25 / {LCS_SLOPE})")

    # v2 annual background levels — the starting point for the class levels, so the
    # ANNUAL level (which F.14 corroborates) is preserved while the SHAPE is rebuilt.
    v2_level = {}
    for y in data:
        s = "_drv" if y in EXT else ""
        p = DEC / f"B_background_hourly_{y}_v2{s}.parquet"
        v2_level[y] = float(pd.read_parquet(p).B.mean()) if p.exists() else np.nan

    # ── load v2 background + sweep alpha ─────────────────────────────────────
    tgtj = tgt.copy()
    rows = []
    per_year = {}
    for y, (T, met) in data.items():
        s = "_drv" if y in EXT else ""
        bp = DEC / f"B_background_hourly_{y}_v2{s}.parquet"
        if not bp.exists():
            continue
        b2 = pd.read_parquet(bp)
        b2["h"] = pd.to_datetime(b2.datetime_utc, utc=True)
        d = T.merge(b2[["h", "B"]], on="h", how="inner").merge(met[["h", "blh"]],
                                                              on="h", how="left")
        d["blh"] = d.blh.interpolate(limit_direction="both").fillna(H_REF)
        d["day"] = d.h.dt.floor("D").values.astype("datetime64[D]").astype(int)
        per_year[y] = d

    print("\n  alpha sweep (daily means preserved exactly at every alpha)")
    print("    alpha   B>T %   share<f_min %   diurnal B swing   r vs NBRO floor")
    for alpha in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        bt, sh, swing, dailies = [], [], [], []
        for y, d in per_year.items():
            Bv = build_B_v3(d.B.to_numpy(float), d.blh.to_numpy(float),
                            d.day.to_numpy(), alpha)
            Tv = d.T_q50.to_numpy(float)
            bt.append((Bv > Tv).astype(float))
            with np.errstate(invalid="ignore", divide="ignore"):
                sh.append(np.where(Tv > 0, (Tv - Bv) / Tv, np.nan))
            hh = d.h.dt.hour.to_numpy()
            prof = pd.Series(Bv).groupby(hh).mean()
            swing.append(float(prof.max() - prof.min()))
            dd = pd.DataFrame({"date": d.h.dt.floor("D").dt.tz_localize(None),
                               "B": Bv}).groupby("date", as_index=False).B.mean()
            dailies.append(dd)
        allbt = float(np.concatenate(bt).mean()) * 100
        allsh = float(np.nanmean(np.concatenate(sh) < F_MIN)) * 100
        dd = pd.concat(dailies).groupby("date", as_index=False).B.mean()
        mm = dd.merge(tgtj, on="date", how="inner")
        r = float(np.corrcoef(mm.B, mm.target)[0, 1]) if len(mm) > 3 else float("nan")
        rows.append({"alpha": alpha, "B_gt_T_pct": round(allbt, 2),
                     "share_lt_fmin_pct": round(allsh, 2),
                     "diurnal_swing": round(float(np.mean(swing)), 3),
                     "r_vs_nbro": round(r, 3)})
        print(f"    {alpha:4.1f}   {allbt:6.2f}   {allsh:9.2f}       {np.mean(swing):8.2f}"
              f"          {r:+.3f}")

    sweep = pd.DataFrame(rows)
    ok = sweep[sweep.B_gt_T_pct < 1.0]
    if ok.empty:
        print("\n  NO alpha achieves coherence: the low-season LEVEL, not the diurnal")
        print("  shape, is the binding problem. Consolidation v3 in this form cannot fix it.")
        chosen = None
    else:
        chosen = float(ok.alpha.min())
        print(f"\n  smallest alpha achieving coherence: {chosen:.2f}")

    res = {"form": "B_v3 = B_v2 * (H_ref/BLH)^alpha, renormalised within each day",
           "H_ref": H_REF, "sweep": rows, "chosen_alpha": chosen,
           "invariants": ["daily mean of B preserved exactly at every alpha",
                          "=> f, the W2 JJA/DJF ratio and every seasonal quantity are "
                          "unchanged by construction"],
           "first_formulation_refuted": {
               "form": "L_class * D * W rebuilt from scratch",
               "alpha": 0.80, "note": "bound-saturated",
               "B_gt_T_pct": 21.82, "w2_ratio": 0.427,
               "r_vs_nbro": -0.071,
               "verdict": "rejected: worse external agreement than the v2 daily series "
                          "(+0.37), coherence and W2 both FAIL"}}

    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT.name}")

    if not a.apply:
        print("dry run — no parquets written. Re-run with --apply once the gates pass.")
        return
    if not (gates["PASS_coherence"] and gates["PASS_w2"]):
        raise SystemExit("REFUSING to write: a gate failed.")
    for y, (T, met) in data.items():
        Bv = build_B(T, met, cls, best["alpha"], best["kappa"], best["tau"],
                     B_MARINE, v2_level[y])
        s = "_drv" if y in EXT else ""
        pd.DataFrame({"datetime_utc": T.datetime_utc.to_numpy(), "B": Bv,
                      "B_lo": 0.70 * Bv, "B_hi": 1.25 * Bv}
                     ).to_parquet(DEC / f"B_background_hourly_{y}_v3{s}.parquet", index=False)
    print("wrote B_background_hourly_*_v3*.parquet")


if __name__ == "__main__":
    main()
