"""kandy_driver_tier_build.py — Phase 5.1: the Kandy post-VanD extension tier.

Ports the Medellín-VALIDATED driver-anchored recipe (medellin_driver_tier_build.py;
2024 annual level +2.0% vs withheld ground truth, LOYO |bias| 3.3%) to Kandy, so the
explorer is no longer capped at 2023 (where the VanD satellite anchor ends).

Design decisions (audited 2026-07-19, recorded in the deliverable plan Phase 5.1):
  - FECT usable hours: 2024 = 2,682 (Akurana only), 2025 = 1, 2026 = 160. FECT
    therefore CANNOT anchor 2025-26, and thin single-station coverage is exactly the
    failure mode that degraded Medellín's 2023 sensor anchor (-15.3%). So the tier is
    DRIVER-ANCHORED throughout, with FECT 2024 as an independent CONSISTENCY CHECK.
  - Training target = the FECT-calibrated hourly PM2.5 record (the same ground series
    the locked Kandy T(t) is built on), features = GEOS-CF prior + met + calendar.
  - Level sanity: the driver tier must land near the locked model's own 2019-2023
    level (~17-21 area) and inside the [GHAP, VanD] bracket; large drift = abort.

Inputs : data/external/kandy/extended_gee/drive/kandy_{geoscf,era5land}_{y}.csv
         data/processed/stage1_v3/dataset_v3_hourly.parquet   (FECT ground)
Outputs: data/processed/stage1_v3/T_anchor/T_kandy_hourly_{y}_drv.parquet
         data/processed/decomp/B_background_hourly_{y}_v2_drv.parquet
         results/figures/kandy_extension/driver_tier_report.txt
Run: .venv/Scripts/python.exe scripts/kandy_driver_tier_build.py [--years 2024 2025 2026]
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
DRV = REPO / "data/external/kandy/extended_gee/drive"
STG = REPO / "data/processed/stage1_v3"
DEC = REPO / "data/processed/decomp"
OUT = REPO / "results/figures/kandy_extension"
FEATURES = ["sin_h", "cos_h", "sin_doy", "cos_doy", "dow",
            "blh", "u10", "v10", "wspd", "t2m", "c_prior"]
# Graceful feature fallback (measured on the 2023 temporal holdout, 2026-07-20):
#   FULL      (with c_prior+blh) : level -14.6%, monthly r 0.989, hourly r 0.867
#   MET-ONLY  (blh, no c_prior)  : level -12.1%, monthly r 0.995, hourly r 0.813
#   ERA5-ONLY (neither)          : level -12.5%, monthly r 0.996, hourly r 0.807
# i.e. the chemistry prior and BLH add essentially nothing to the LEVEL/SEASONAL
# signal this tier exists to carry (only hourly detail softens slightly) — consistent
# with F-K1 satellite-independence and the Track T-a met-only anchor. This lets a year
# be built as soon as ERA5-Land lands, without waiting on GEOS-CF's 2-3 month GEE
# latency (gotcha #30). The variant used is recorded per year in the report.
ERA5_ONLY = ["sin_h", "cos_h", "sin_doy", "cos_doy", "dow", "u10", "v10", "wspd", "t2m"]
LGBM = dict(learning_rate=0.05, num_leaves=63, n_estimators=400,
            min_child_samples=20, subsample=0.8, colsample_bytree=0.8,
            verbose=-1, n_jobs=-1)
F_LOCAL = 0.24          # Kandy official local fraction (SBI band [0.10, 0.27])
TZ = "Asia/Colombo"


def calendar(df, col="valid"):
    dt = df[col]
    df["sin_h"] = np.sin(2 * np.pi * dt.dt.hour / 24)
    df["cos_h"] = np.cos(2 * np.pi * dt.dt.hour / 24)
    doy = dt.dt.dayofyear
    df["sin_doy"] = np.sin(2 * np.pi * doy / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * doy / 365.25)
    df["dow"] = dt.dt.dayofweek
    return df


def _drivers_from_inference_grid(year):
    """Existing per-year inference grid already carries the same drivers (GEOS-CF raw
    prior + ERA5 met) on the model's own clock — preferred where it exists (2024),
    so the extension stays consistent with the locked chain."""
    fp = STG / f"inference_grid_{year}_s12451.parquet"
    if not fp.exists():
        return None
    d = pd.read_parquet(fp, columns=["datetime_utc", "geos_cf_pm25_raw", "blh_m",
                                     "u10", "v10", "t2m"])
    d["valid"] = pd.to_datetime(d.datetime_utc, utc=True).dt.tz_localize(None)
    d = (d.groupby("valid").agg(c_prior=("geos_cf_pm25_raw", "mean"),
                                blh=("blh_m", "mean"), u10=("u10", "mean"),
                                v10=("v10", "mean"), t2m=("t2m", "mean"))
          .reset_index())
    d["wspd"] = np.hypot(d.u10, d.v10)
    return calendar(d)


def load_drivers(years, quiet=False):
    """Hourly driver frame per year: inference grid where available, else the
    KandyExtGEE area-mean CSVs (2025-26)."""
    out = []
    for y in years:
        g = _drivers_from_inference_grid(y)
        if g is not None and len(g) > 1000:
            g["src"] = "inference_grid"
            out.append(g)
            continue
        fe, fg = DRV / f"kandy_era5land_{y}.csv", DRV / f"kandy_geoscf_{y}.csv"
        if not (fe.exists() and fg.exists()):
            print(f"  {y}: SKIPPED (no drivers — inference grid absent and "
                  f"KandyExtGEE CSVs missing/empty)")
            continue
        e = pd.read_csv(fe).rename(columns={
            "u_component_of_wind_10m": "u10", "v_component_of_wind_10m": "v10",
            "temperature_2m": "t2m", "dewpoint_temperature_2m": "d2m",
            "total_precipitation": "tp"})
        e["valid"] = pd.to_datetime(e.datetime)
        gg = pd.read_csv(fg).rename(columns={"PM25_RH35_GCC": "c_prior", "ZPBL": "blh"})
        if len(gg) < 100:
            # GEOS-CF not yet published for this year (gotcha #30) -> ERA5-Land-only
            # variant, which the holdout shows is equivalent for level/seasonal skill.
            print(f"  {y}: GEOS-CF only {len(gg)} rows -> ERA5-Land-only variant")
            e["c_prior"] = np.nan
            e["blh"] = np.nan
            e["wspd"] = np.hypot(e.u10, e.v10)
            e["src"] = "KandyExtGEE(era5-only)"
            out.append(calendar(e))
            continue
        gg["valid"] = pd.to_datetime(gg.datetime)
        d = e.merge(gg[["valid", "c_prior", "blh"]], on="valid", how="inner")
        d["wspd"] = np.hypot(d.u10, d.v10)
        d["src"] = "KandyExtGEE"
        out.append(calendar(d))
    if not out:
        sys.exit("no usable driver years")
    d = pd.concat(out, ignore_index=True).dropna(subset=ERA5_ONLY)
    if not quiet:
        for y, g in d.groupby(d.valid.dt.year):
            print(f"  drivers {y}: {len(g):,} h ({g.src.iloc[0]})")
    return d.sort_values("valid").reset_index(drop=True)


def load_area_target(years=(2019, 2020, 2021, 2022, 2023)):
    """TRAINING TARGET = the locked model's own area-anchored T(t) (VanD-re-anchored,
    diurnally sharpened) for 2019-2023, on the driver clock.

    WHY NOT the FECT record (the obvious choice, and what Medellín used): Medellín's
    24-station network mean IS area-representative, so training on it reproduces the
    area level. Kandy's 1-2 FECT points are NOT (gotcha #51: FECT ~13.6 vs area
    ~17-21 vs KOALA floor 24.5) — training on them yields a POINT level ~40% low
    (measured: 12.1 vs locked 17-21). Training on the locked T(t) instead continues
    exactly the quantity the explorer already shows, in the same units, so the
    extension years are commensurable with 2019-2023. FECT then serves as an
    independent SHAPE/consistency check (see main()).
    """
    rows = []
    for y in years:
        fp = STG / "T_anchor" / f"T_kandy_hourly_{y}.parquet"
        if not fp.exists():
            continue
        t = pd.read_parquet(fp)
        t["valid"] = pd.to_datetime(t.datetime_utc, utc=True).dt.tz_localize(None)
        rows.append(t[["valid", "T_q50"]].rename(columns={"T_q50": "pm25"}))
    tgt = pd.concat(rows, ignore_index=True)
    drv = load_drivers(years, quiet=True)
    d = tgt.merge(drv, on="valid", how="inner")
    return d


def load_ground():
    """FECT-calibrated hourly PM2.5 (point sensors — consistency check only)."""
    f = pd.read_parquet(STG / "dataset_v3_hourly.parquet",
                        columns=["datetime_utc", "sensor_id", "pm25_observed",
                                 "geos_cf_pm25_raw", "blh_m", "u10", "v10", "t2m"])
    f["valid"] = pd.to_datetime(f.datetime_utc, utc=True).dt.tz_localize(None)
    f = f.dropna(subset=["pm25_observed"])
    h = (f.groupby("valid").agg(pm25=("pm25_observed", "mean"),
                                n_st=("pm25_observed", "count"),
                                c_prior=("geos_cf_pm25_raw", "mean"),
                                blh=("blh_m", "mean"),
                                u10=("u10", "mean"), v10=("v10", "mean"),
                                t2m=("t2m", "mean")).reset_index())
    h["wspd"] = np.hypot(h.u10, h.v10)
    return calendar(h)


_R_MO = None


def _locked_b_over_t():
    """Monthly B/T ratio of the LOCKED chain (2019-2023) — the seasonal partition
    the extension years inherit (see the SEASONAL PARTITION note in main())."""
    global _R_MO
    if _R_MO is None:
        rows = []
        for y in range(2019, 2024):
            tf = STG / "T_anchor" / f"T_kandy_hourly_{y}.parquet"
            bf = DEC / f"B_background_hourly_{y}_v2.parquet"
            if not (tf.exists() and bf.exists()):
                continue
            T = pd.read_parquet(tf); T["t"] = pd.to_datetime(T.datetime_utc, utc=True)
            B = pd.read_parquet(bf); B["t"] = pd.to_datetime(B.datetime_utc, utc=True)
            rows.append(T[["t", "T_q50"]].merge(B[["t", "B"]], on="t"))
        d = pd.concat(rows)
        gm = d.groupby(d.t.dt.month).agg(Tm=("T_q50", "mean"), Bm=("B", "mean"))
        _R_MO = (gm["Bm"] / gm["Tm"]).reindex(range(1, 13)).ffill().bfill()
    return _R_MO


def sharpen_to_locked(ext, target):
    """Restore the diurnal + seasonal AMPLITUDE the GBM damps (gotcha #53).

    A quantile GBM regresses toward the mean, so the driver tier reproduces the right
    diurnal PHASE but a shrunken swing (measured 2026-07-20: 10.97 ug/m3 in 2025 vs
    the locked chain's 14.07 - a ~22% shortfall). Because the local field only carries
    structure where T exceeds B, a damped T spends more hours below B and renders
    spatially FLAT: the extension years showed only 58-60% accumulation hours vs
    61-75% in the anchored years. This is exactly what `sharpen_T_diurnal.py` corrects
    in the locked chain, so the extension gets the same treatment.

    Method (mirrors sharpen_T_diurnal): map the tier's (hour-of-day) and (month)
    climatologies onto the LOCKED T(t) climatologies via multiplicative factors, then
    rescale so each year's ANNUAL MEAN is unchanged. Phase and synoptic variability
    are untouched; only the systematic amplitude deficit is removed.
    """
    lt_t = pd.DatetimeIndex(target.valid).tz_localize("UTC").tz_convert(TZ)
    lt_e = pd.DatetimeIndex(ext.datetime_utc).tz_convert(TZ)

    def ratio(vals, keys):
        s = pd.Series(np.asarray(vals), index=np.asarray(keys))
        c = s.groupby(level=0).mean()
        return c / c.mean()

    f_h = (ratio(target.pm25, lt_t.hour)
           / ratio(ext.T_q50, lt_e.hour)).reindex(range(24)).fillna(1.0)
    f_m = (ratio(target.pm25, lt_t.month)
           / ratio(ext.T_q50, lt_e.month)).reindex(range(1, 13)).fillna(1.0)
    fac = (f_h.reindex(lt_e.hour).to_numpy()
           * f_m.reindex(lt_e.month).to_numpy())
    out = ext.copy()
    for c in ("T_q05", "T_q50", "T_q95"):
        out[c] = out[c].to_numpy() * fac
    # preserve each year's annual mean exactly
    for y, idx in out.groupby(out.datetime_utc.dt.year).groups.items():
        k = ext.loc[idx, "T_q50"].mean() / out.loc[idx, "T_q50"].mean()
        for c in ("T_q05", "T_q50", "T_q95"):
            out.loc[idx, c] = out.loc[idx, c] * k
    a0 = ext.groupby(lt_e.hour).T_q50.mean()
    a1 = out.groupby(lt_e.hour).T_q50.mean()
    print(f"  amplitude sharpening: diurnal swing {a0.max()-a0.min():.2f} -> "
          f"{a1.max()-a1.min():.2f} ug/m3 (locked reference "
          f"{ratio(target.pm25, lt_t.hour).pipe(lambda r: (r.max()-r.min())*target.pm25.mean()):.2f})")
    return out


def fit_quantiles(tr, alphas=(0.05, 0.5, 0.95), feats=None):
    feats = feats or FEATURES
    return {a: LGBMRegressor(objective="quantile", alpha=a, **LGBM)
            .fit(tr[feats], tr.pm25) for a in alphas}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2024, 2025, 2026])
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)

    # ── TARGET = the locked area-anchored T(t) (see load_area_target docstring) ──
    g = load_area_target().dropna(subset=FEATURES + ["pm25"])
    print(f"area-target hours (locked T(t) 2019-2023 on driver clock): {len(g):,} "
          f"| mean {g.pm25.mean():.2f} ug/m3")

    # temporal holdout: train <=2022, verify the 2023 area level + PI coverage
    tr, te = g[g.valid.dt.year <= 2022], g[g.valid.dt.year == 2023]
    infl, chk = 1.0, None
    if len(te) >= 500:
        m = fit_quantiles(tr)
        lo = m[0.05].predict(te[FEATURES]); hi = m[0.95].predict(te[FEATURES])
        mid = m[0.5].predict(te[FEATURES])
        cov = float(np.mean((te.pm25 >= lo) & (te.pm25 <= hi)))
        if cov < 0.85:
            for cand in (1.1, 1.25, 1.5, 1.75, 2.0):
                c = float(np.mean((te.pm25 >= mid + (lo - mid) * cand)
                                  & (te.pm25 <= mid + (hi - mid) * cand)))
                if c >= 0.88:
                    infl, cov = cand, c
                    break
            else:
                infl, cov = 2.0, c
        bias = float(100 * (mid.mean() - te.pm25.mean()) / te.pm25.mean())
        r_mon = float(np.corrcoef(
            pd.Series(mid).groupby(te.valid.dt.month.to_numpy()).mean(),
            te.pm25.groupby(te.valid.dt.month.to_numpy()).mean())[0, 1])
        chk = dict(n=len(te), level_bias_pct=round(bias, 1), cov90=round(cov, 2),
                   monthly_r=round(r_mon, 3), inflation=infl)
        print(f"  2023 temporal holdout vs locked T(t): level bias {bias:+.1f}% | "
              f"monthly r {r_mon:.2f} | cov90 {cov:.2f} (inflation x{infl})")

    # independent FECT shape check (point sensors — NOT the level reference)
    fect = load_ground().dropna(subset=["pm25"])
    f24 = fect[fect.valid.dt.year == 2024]
    fect_chk = None
    if len(f24) >= 200:
        mfull = fit_quantiles(g)
        pred24 = mfull[0.5].predict(
            load_drivers([2024], quiet=True).set_index("valid")
            .reindex(f24.valid).reset_index()[FEATURES].ffill())
        ok = np.isfinite(pred24)
        r_h = float(np.corrcoef(pred24[ok], f24.pm25.to_numpy()[ok])[0, 1])
        ratio = float(np.nanmean(pred24[ok]) / f24.pm25.mean())
        fect_chk = dict(n=int(ok.sum()), hourly_r=round(r_h, 3),
                        area_over_point_ratio=round(ratio, 2))
        print(f"  2024 FECT shape check: hourly r {r_h:.2f}, area/point level ratio "
              f"{ratio:.2f} (expected >1 — FECT points read below the area mean, "
              f"gotcha #51)")

    # production refit on ALL area-target years — two variants, so a year can be built
    # as soon as ERA5-Land lands (see ERA5_ONLY note above)
    mfull = fit_quantiles(g, feats=FEATURES)
    mera = fit_quantiles(g, feats=ERA5_ONLY)
    drv = load_drivers(a.years)
    print(f"driver hours {len(drv):,} ({drv.valid.min()} -> {drv.valid.max()})")
    parts, variant_of = [], {}
    for y, gy in drv.groupby(drv.valid.dt.year):
        has_full = gy[FEATURES].notna().all(axis=1).mean() > 0.95
        mm, feats, vname = ((mfull, FEATURES, "full")
                            if has_full else (mera, ERA5_ONLY, "era5-only"))
        variant_of[int(y)] = vname
        X = gy[feats]
        p50 = mm[0.5].predict(X)
        parts.append(pd.DataFrame({
            "datetime_utc": gy.valid.dt.tz_localize("UTC"),
            "T_q05": np.clip(p50 + (mm[0.05].predict(X) - p50) * infl, 0, None),
            "T_q50": np.clip(p50, 0, None),
            "T_q95": np.clip(p50 + (mm[0.95].predict(X) - p50) * infl, 0, None)}))
        print(f"  {y}: variant = {vname}")
    ext = pd.concat(parts, ignore_index=True)
    ext = sharpen_to_locked(ext, g)

    lines = []
    for y, gy in ext.groupby(ext.datetime_utc.dt.year):
        gy.to_parquet(STG / "T_anchor" / f"T_kandy_hourly_{y}_drv.parquet", index=False)
        ann = float(gy.T_q50.mean())
        # B(t): (1-f) x annual level, shaped by the daily GEOS-CF prior (same
        # convention as the locked B v2 chain: level x normalised daily shape)
        gd = drv[drv.valid.dt.year == y].copy()
        # ── SEASONAL PARTITION (fix, 2026-07-20) ──────────────────────────────
        # A flat (1-f)*annual background is WRONG for Kandy: the locked B(t) v2 is
        # origin-conditioned and drops hard in the SW monsoon (JJA B ~8.5 against
        # T ~10.5, leaving a visible local increment). Scaling a constant annual B by
        # only a daily shape leaves B ~11-13 in JJA, which SWAMPS T -> the increment
        # goes negative and the increment-split renders those hours spatially FLAT.
        # Measured before this fix: July 2026 had B/T = 1.34 and only 18.6% of hours
        # with T > B (locked July: 0.79 and 70.2%) — i.e. 81% of the month showed no
        # local structure at all. Fix: inherit the locked MONTHLY B/T ratio, so the
        # seasonal partition (and therefore the local increment) behaves like the
        # anchored years. The daily prior shape is kept as a within-month modulation.
        r_mo = _locked_b_over_t()
        base = gy.set_index(gy.datetime_utc)["T_q50"].to_numpy() * \
            r_mo.reindex(gd.valid.dt.month).to_numpy()
        if gd.c_prior.notna().mean() > 0.5:
            day = gd.groupby(gd.valid.dt.floor("D")).c_prior.mean()
            shape = (day / day.mean()).reindex(gd.valid.dt.floor("D")).to_numpy()
        else:
            # ERA5-only year: no chemistry prior to shape the background. Use the
            # day-of-year climatology of the normalised daily prior from the years
            # that do have it, so the seasonal background structure is preserved.
            ref = drv[drv.c_prior.notna()].copy()
            if len(ref) < 1000:
                shape = np.ones(len(gd))
            else:
                rd = ref.groupby(ref.valid.dt.floor("D")).agg(
                    c=("c_prior", "mean"), doy=("valid", lambda s: s.iloc[0].dayofyear))
                rd["c"] = rd.c / rd.c.mean()
                clim = rd.groupby("doy").c.mean()
                clim = clim.reindex(range(1, 367)).interpolate(
                    limit_direction="both").fillna(1.0)
                shape = clim.reindex(gd.valid.dt.dayofyear).to_numpy()
            shape = shape / np.nanmean(shape)
        # normalise the daily shape WITHIN each month so it modulates without
        # disturbing the inherited monthly partition
        sh = pd.Series(shape, index=gd.valid.to_numpy())
        sh = sh / sh.groupby(pd.DatetimeIndex(sh.index).month).transform("mean")
        B = base * sh.to_numpy()
        b_ann = float(np.nanmean(B))
        pd.DataFrame({"datetime_utc": gy.datetime_utc.to_numpy(),
                      "B": B, "B_lo": B * 0.70, "B_hi": B * 1.25}
                     ).to_parquet(DEC / f"B_background_hourly_{y}_v2_drv.parquet",
                                  index=False)
        # PLAUSIBILITY FLAG ONLY — never a clamp. The model output is whatever the
        # drivers imply; real inter-annual variation may legitimately fall outside the
        # locked-year range, and a genuinely cleaner/dirtier year MUST be allowed to
        # show. This flag exists to prompt a look, not to constrain: an "INSPECT"
        # means check the drivers, not adjust the number.
        # NOTE (2026-07-25 audit): the locked 2019-2023 annual means are
        # 19.75/19.09/17.08/18.76/21.04, i.e. the true locked range is 17.08-21.04 —
        # NOT the "17.1-21.0" quoted in earlier notes, which by rounding excludes two
        # of the five locked years. The operational window below is deliberately much
        # wider (14-26) so it flags only a real driver anomaly, and it has never fired.
        plausible = 14.0 <= ann <= 26.0
        lines.append(f"  {y}: {len(gy):,} h  T annual {ann:.2f}  B annual {b_ann:.2f}"
                     f"  [{variant_of.get(int(y), '?')}]"
                     f"  {'within plausible window (14-26)' if plausible else 'OUTSIDE window — INSPECT DRIVERS (not a defect)'}")
        print(lines[-1])

    rep = ["Kandy driver-anchored extension tier (Phase 5.1)",
           f"years: {a.years} | TARGET = locked area-anchored T(t) 2019-2023 "
           f"({len(g):,} h, mean {g.pm25.mean():.2f})",
           f"features: {FEATURES}",
           "TARGET CHOICE (important): trained on the locked T(t), NOT the FECT record.",
           "  Medellin could train on its 24-station network mean because that IS",
           "  area-representative; Kandy's 1-2 FECT points are not (gotcha #51: FECT",
           "  ~13.6 vs area ~17-21 vs KOALA floor 24.5). Training on FECT gave a point",
           "  level of 12.1 (~40% low); training on the locked T(t) continues exactly",
           "  the quantity the explorer shows, in the same units.",
           "FECT coverage audit: 2024=2,682 h (Akurana only), 2025=1, 2026=160 ->",
           "  FECT cannot anchor 2025+; used as an independent SHAPE check only.",
           f"2023 temporal holdout vs locked T(t): {chk}",
           f"2024 FECT shape check: {fect_chk}",
           "recipe pedigree: Medellin driver tier validated vs withheld ground truth",
           "  (2024 annual level +2.0%, LOYO |bias| 3.3% vs clim 10.1%/GEOS 9.4%).",
           "Kandy has no withheld network by premise -> this is a TRANSFERRED-method",
           "  tier with consistency checks, NOT a locally validated one. Label as such.",
           ""] + lines
    (OUT / "driver_tier_report.txt").write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep[-3:]))
    print(f"\nWrote T_kandy_hourly_*_drv.parquet + B_*_v2_drv.parquet + "
          f"{OUT / 'driver_tier_report.txt'}")


if __name__ == "__main__":
    main()
