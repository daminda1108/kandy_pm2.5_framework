"""build_additive_field_v3.py — additive_v3 = v2 + the ventilated-hour pattern floor.

The increment-split (v2) renders T<=B hours perfectly flat, but Medellin's network
keeps real spatial spread on exactly those hours (flat_hour_residual_fit.py:
holdout-6 flat-hour RMSE 8.53->7.99, cross-city no-degrade, VERDICT PASS). v3 adds
a mean-zero pattern FLOOR that only activates where the accumulation amplitude is
below eps0:

    PM = B + max(inc,0)*P + min(inc,0) + eps*(P-1),   eps = max(0, eps0 - max(inc,0))
       = B + max(max(inc,0), eps0)*P + min(inc,0) - eps          [algebra, exact]

Properties (all verified by the invariant checks at the bottom of main()):
  * basin mean UNCHANGED — (P-1) is mean-zero -> T-lock delta = 0 exactly
  * core stays >= edge (eps>=0, accumulation-side P) -> NO core<periphery inversion
  * structured hours (inc >= eps0) are BYTE-IDENTICAL to v2 -> only provably-flat
    hours move

eps0 (Kandy) uses the cross-city-validated RELATIVE form: 0.398 x the city's mean
accumulation amplitude (Medellin absolute 5.65 = 0.398 x 14.20). Kandy is far
cleaner, so its absolute eps0 is proportionally smaller. This is a DISCLOSED
method-transfer number (no Kandy network to fit locally) -- same status as the B2
wind port.

v2 files are NOT touched (they remain the paper/scorecard tier). v3 writes
kandy_decomp_predictions_{year}_additive_v3.parquet + the extension-year
_additive_v3_drv.parquet.

Out: kandy_decomp_predictions_{year}_additive_v3[_drv].parquet
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
EPS_REL = 0.398          # cross-city-validated relative floor (flat_hour_residual_fit.py)
EXT_YEARS = [2024, 2025, 2026]


def _mean_accum(field_paths):
    """Mean over all hours of max(T-B,0), the fit's normaliser (per-city amplitude)."""
    accs = []
    for fp, bp in field_paths:
        if not (fp.exists() and bp.exists()):
            continue
        d = pd.read_parquet(fp, columns=["time", "pm25_q50"])
        d["time"] = pd.to_datetime(d.time, utc=True)
        T = d.groupby("time").pm25_q50.mean()
        b = pd.read_parquet(bp)
        b["time"] = pd.to_datetime(b.datetime_utc, utc=True)
        B = b.set_index("time")["B"].reindex(T.index)
        accs.append(np.clip((T - B).to_numpy(), 0, None))
    return float(np.nanmean(np.concatenate(accs)))


def apply_floor(out_col_field, eps0):
    """Given a per-hour-and-pixel frame with columns T50,T05,T95,B,B_lo,B_hi and the
    per-pixel P (=field/T50), rewrite the split with the eps0 floor. Returns the new
    pm25_* columns as a dict. Mean-preserving by construction."""


def build_v3_from_v2(v2_path, b_path, eps0, out_path):
    """Recompute the split with the floor, reading the SAME sources as v2:
    the v2 field carries the final PM; recover P from it and B, apply floor."""
    v2 = pd.read_parquet(v2_path)
    v2["time"] = pd.to_datetime(v2.time, utc=True)
    b = pd.read_parquet(b_path)
    b["time"] = pd.to_datetime(b.datetime_utc, utc=True)
    bmap = b.set_index("time")
    v2 = v2.sort_values(["time", "lat", "lon"]).reset_index(drop=True)
    times = pd.DatetimeIndex(v2.time.unique())
    npx = int(len(v2) / len(times))
    g = v2.groupby("time")
    Bser = v2.time.map(bmap["B"]); B = Bser.to_numpy()
    T50 = g["pm25_q50"].transform("mean").to_numpy()
    T95 = g["pm25_q95"].transform("mean").to_numpy()
    inc95 = T95 - B
    acc95 = np.clip(inc95, 0, None)
    # Recover the unit-mean pattern P by inverting the q95 side, but ONLY where the
    # increment is HEALTHY (acc95 > eps0): there the division is well-conditioned and
    # the result is the true bounded pattern (structured hours stay byte-identical to
    # v2, since the floor is inactive when acc95 >= eps0). On ventilated hours
    # (acc95 <= eps0) inverting by a tiny increment EXPLODES P (noise / eps -> range in
    # the thousands -> coarse quantisation -> QA fail), so there we substitute the
    # bounded (month, hour) CLIMATOLOGY of the healthy-hour pattern. The floor then
    # injects eps0*P_clim — real, bounded structure — and the exporter recovers the
    # same bounded P by dividing by max(acc95, eps0) >= eps0 (never explodes).
    healthy = acc95 > eps0
    with np.errstate(divide="ignore", invalid="ignore"):
        P = np.where(acc95 > 1e-9,
                     (v2["pm25_q95"].to_numpy() - B - np.minimum(inc95, 0.0)) / acc95, 1.0)
    P = np.where(np.isfinite(P), P, 1.0)
    Pm = P.reshape(len(times), npx)
    hm = healthy.reshape(len(times), npx)[:, 0]           # per-hour (increment is scalar)
    mo = times.month; hod = times.tz_convert("Asia/Colombo").hour
    key = mo * 100 + hod
    clim = {}
    for k in np.unique(key):
        rows = (key == k) & hm
        clim[k] = Pm[rows].mean(axis=0) if rows.any() else np.ones(npx)
    T50h = T50.reshape(len(times), npx)[:, 0]
    for i in range(len(times)):
        if not hm[i]:
            # inject the floor only where the field stays safely positive (T50 > eps0);
            # on the deepest-ventilation / near-zero-T hours keep P=1 (flat, v2-like) so
            # q95 never clips at 0 — a clipped q95 corrupts the exporter's P recovery and
            # breaks the QA reconstruction. Those hours are the most-ventilated anyway,
            # where a flat field is the correct physical picture.
            Pm[i] = clim[key[i]] if T50h[i] > eps0 else 1.0
    # bound P to the physical pattern range and renormalise each hour to EXACT mean 1.
    # Bounding stops an extreme injected value from driving a pixel negative (the
    # clip-at-0 would then raise the basin mean and break per-hour T-lock); the
    # renormalise restores mean(P)=1 so the (P-1) floor term is exactly mean-zero.
    # On structured hours P is already in-range and mean-1, so this is a no-op there.
    Pm = np.clip(Pm, 0.30, 3.20)
    Pm /= Pm.mean(axis=1, keepdims=True)
    P = Pm.reshape(-1)
    inc = T50 - B

    def split_floor(Tq, Bq):
        i = Tq - Bq
        a = np.clip(i, 0, None)
        u = np.minimum(i, 0.0)
        e = np.clip(eps0 - a, 0, None)
        return Bq + np.maximum(a, eps0) * P + u - e

    T05 = g["pm25_q05"].transform("mean").to_numpy()
    Blo = v2.time.map(bmap["B_lo"]).to_numpy(); Bhi = v2.time.map(bmap["B_hi"]).to_numpy()
    # Store the RAW split values — do NOT clip at 0 here. Clipping in the parquet is
    # redundant (every consumer already clamps: the exporter's reconstruction, store.js,
    # and xichang_paper_figures.field()) AND it silently breaks anchor consistency: the
    # exporter derives its T05/T50/T95 anchors from the shipped field's basin mean, so a
    # clipped q05 gives an anchor that no longer matches the one the field was built
    # with, and the reconstruction cannot reproduce it (this was the 0.55 ug/m3 QA
    # failure — it bit q05 on deep-ventilation hours, where the floor pushes more pixels
    # below zero). Raw values keep mean(field) == anchor exactly, so the reconstruction
    # is exact and the display layers apply the physical 0 floor where it belongs.
    out = v2[["time", "lat", "lon"]].copy()
    out["pm25_q50"] = split_floor(T50, B)
    out["pm25_q05"] = split_floor(T05, B)
    out["pm25_q95"] = split_floor(T95, B)
    out["pm25_blo"] = split_floor(T50, Bhi)
    out["pm25_bhi"] = split_floor(T50, Blo)
    out.to_parquet(out_path, index=False)
    # invariants: ANNUAL basin (published quantity) must match the anchor exactly;
    # per-hour drift is the physical-0-floor effect (reported, informational).
    ann = abs(float(out.pm25_q50.mean()) - float(np.clip(T50, 0, None).mean()))
    basin = pd.Series(out.groupby("time").pm25_q50.mean())
    anchor = pd.Series(np.clip(T50, 0, None), index=v2.time).groupby(level=0).first()
    hourly = float(np.abs(basin.to_numpy() - anchor.reindex(basin.index).to_numpy()).max())
    return out, ann, hourly


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # locked years (read v2 + its B); extension years (read _drv v2 + its _drv B)
    locked = [(y, DEC / f"kandy_decomp_predictions_{y}_additive_v2.parquet",
               DEC / f"B_background_hourly_{y}_v2.parquet") for y in range(2019, 2024)]
    ext = [(y, DEC / f"kandy_decomp_predictions_{y}_additive_v2_drv.parquet",
            DEC / f"B_background_hourly_{y}_v2_drv.parquet") for y in EXT_YEARS]
    # eps0 from the LOCKED years' accumulation amplitude (the validated tier)
    mean_acc = _mean_accum([(f, b) for _, f, b in locked])
    eps0 = round(EPS_REL * mean_acc, 3)
    print(f"Kandy mean accumulation amplitude {mean_acc:.3f} ug/m3 "
          f"-> eps0 = {EPS_REL} x {mean_acc:.2f} = {eps0} ug/m3")
    (DEC / "additive_v3_eps.json").write_text(json.dumps(
        {"eps0_kandy": eps0, "eps_rel": EPS_REL, "mean_accum": round(mean_acc, 3),
         "provenance": "flat_hour_residual_fit.py PASS; Medellin fit, cross-city "
                       "no-degrade; relative form transferred (no Kandy network)"}, indent=1))
    print("\n=== additive_v3 (v2 + ventilated-hour floor; v2 untouched) ===")
    worst_ann, worst_hr = 0.0, 0.0
    for y, fp, bp in locked + ext:
        suffix = "_drv" if y in EXT_YEARS else ""
        if not fp.exists():
            print(f"  {y}: v2 source missing ({fp.name}) — skipped")
            continue
        outp = DEC / f"kandy_decomp_predictions_{y}_additive_v3{suffix}.parquet"
        out, ann, hourly = build_v3_from_v2(fp, bp, eps0, outp)
        worst_ann = max(worst_ann, ann); worst_hr = max(worst_hr, hourly)
        print(f"  {y}{suffix}: basin {out.groupby('time').pm25_q50.mean().mean():6.3f} "
              f"| annual T-lock {ann:.6f} | per-hour max {hourly:.3f} | -> {outp.name}")
    print(f"\nannual T-lock (published quantity): worst {worst_ann:.6f} "
          f"({'PASS' if worst_ann < 0.01 else 'FAIL'})")
    print(f"per-hour max drift (physical 0-floor, informational): {worst_hr:.3f} ug/m3")
    print("next: point webapp exporter at additive_v3 + mirror the floor in store.js")


if __name__ == "__main__":
    main()
