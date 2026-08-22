"""colombo_zeroshot_test.py -- the pre-registered Colombo zero-shot out-of-regime test.

Pre-registration: docs/prereg_colombo_zeroshot_2026-08-22.md
OSF registration:  https://osf.io/nxqgb/   (registered 2026-08-22T17:29:53Z, before this file existed)

Runs EXACTLY the registered design. No re-specification after seeing a result (prereg section 6).

    C-G1  daily RMSE within the tropical p10-p90 band [13.43, 45.54]
    C-G2  monthly-mean seasonal r >= 0.60
    C-G3  absolute level bias <= 40%
    C-G4  daily R2 > 0 against a day-of-year climatology baseline   <- the decisive gate

The technical pre-check (prereg section 7) runs FIRST: if Colombo's driver distributions fall
outside the panel's per-feature ranges the test is declared INCONCLUSIVE ON TECHNICAL GROUNDS
and stops. It is not re-run with a modified feature set.

Usage:  python scripts/colombo_zeroshot_test.py
Out:    data/processed/modular/colombo_zeroshot.csv
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from modular_validation_all import FEATS, build_frame  # noqa: E402

OUT = REPO / "data" / "processed" / "modular" / "colombo_zeroshot.csv"

# thresholds fixed in the pre-registration, NOT after seeing anything
G1_LO, G1_HI = 13.43, 45.54
G2_MIN, G3_MAX = 0.60, 40.0
SEEDS = (0, 1, 2)


def colombo_drivers() -> pd.DataFrame:
    """Hourly ERA5 -> daily mean, in the panel's units and conventions."""
    fr = []
    for f in sorted(glob.glob(str(REPO / "data/raw/era5_colombo/colombo_era5_*.csv"))):
        fr.append(pd.read_csv(f))
    d = pd.concat(fr, ignore_index=True)
    d["date"] = pd.to_datetime(d.datetime, errors="coerce").dt.tz_localize(None).dt.normalize()
    agg = {c: "mean" for c in
           ["temperature_2m", "u_component_of_wind_10m", "v_component_of_wind_10m",
            "boundary_layer_height"] if c in d.columns}
    g = d.groupby("date").agg(agg).reset_index()
    # wind formed from the DAILY-MEAN components, matching drivers_cnemc/drivers_openaq
    g["wind"] = np.hypot(g.u_component_of_wind_10m, g.v_component_of_wind_10m)
    return g


def colombo_obs() -> pd.DataFrame:
    d = pd.read_parquet(REPO / "data/processed/stage1_v2/dataset_v2_colombo_daily.parquet",
                        columns=["date", "pm25_observed"])
    d["date"] = pd.to_datetime(d.date).dt.tz_localize(None).dt.normalize()
    return d.dropna().groupby("date", as_index=False).pm25_observed.mean()


def main() -> None:
    print("=== Colombo zero-shot test -- pre-registered at https://osf.io/nxqgb/ ===\n")

    print("[1] building the 47-city panel pool ...")
    sample = pd.read_csv(REPO / "data/processed/modular/validation_sample.csv")
    manifest = pd.read_csv(REPO / "data/processed/modular/openaq_manifest.csv")
    _, pool = build_frame(sample, manifest)
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    feats = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=feats + ["pm25_city"])
    print(f"    pool: {len(pool)} city-days, {pool.city.nunique()} cities, feats={feats}")
    assert not pool.city.astype(str).str.contains("colombo", case=False).any(), \
        "Colombo leaked into the training panel"

    print("\n[2] building Colombo drivers and observations ...")
    cd = colombo_drivers()
    co = colombo_obs()
    d = cd.merge(co, on="date", how="inner")
    dy = d.date.dt.dayofyear
    d["doy_sin"] = np.sin(2 * np.pi * dy / 365.25)
    d["doy_cos"] = np.cos(2 * np.pi * dy / 365.25)
    d = d.dropna(subset=feats + ["pm25_observed"])
    print(f"    Colombo: {len(d)} matched days, {d.date.min().date()} to {d.date.max().date()}")

    # ---- prereg section 7: the technical pre-check, BEFORE any scoring ----
    print("\n[3] TECHNICAL PRE-CHECK (prereg section 7): driver distributions vs panel ranges")
    bad = []
    for f in feats:
        plo, phi = pool[f].quantile(0.001), pool[f].quantile(0.999)
        cm, cs = d[f].mean(), d[f].std()
        inside = plo <= cm <= phi
        print(f"    {f:<28} panel[{plo:10.3f},{phi:10.3f}]  colombo mean {cm:10.3f} sd {cs:8.3f}  "
              f"{'ok' if inside else 'OUT OF RANGE'}")
        if not inside:
            bad.append(f)
    if bad:
        print(f"\n    INCONCLUSIVE ON TECHNICAL GROUNDS -- {bad} outside the panel range.")
        print("    Per the pre-registration this is NOT a failure and the test is not re-run.")
        return
    print("    all features inside the panel range -- proceeding to score")

    print("\n[4] training Bud0 leave-one-city-out (Colombo held out entirely) ...")
    preds = []
    for s in SEEDS:
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, random_state=s)
        m.fit(pool[feats], pool.pm25_city)
        preds.append(m.predict(d[feats]))
    P = np.vstack(preds)
    yhat = np.median(P, axis=0)
    y = d.pm25_observed.to_numpy()

    # ---- gates ----
    rmse = float(np.sqrt(np.mean((yhat - y) ** 2)))
    bias = float((yhat.mean() - y.mean()) / y.mean() * 100)
    mm = pd.DataFrame({"m": d.date.dt.month, "o": y, "p": yhat}).groupby("m").mean()
    seas_r = float(np.corrcoef(mm.o, mm.p)[0, 1])
    clim = pd.Series(y).groupby(d.date.dt.dayofyear.values).transform("mean").to_numpy()
    ss_res = float(((y - yhat) ** 2).sum()); ss_clim = float(((y - clim) ** 2).sum())
    r2_vs_clim = 1 - ss_res / ss_clim
    r2_plain = 1 - ss_res / float(((y - y.mean()) ** 2).sum())

    g1 = G1_LO <= rmse <= G1_HI
    g2 = seas_r >= G2_MIN
    g3 = abs(bias) <= G3_MAX
    g4 = r2_vs_clim > 0

    print(f"\n=== RESULTS (n={len(d)} days, seed spread {P.std(axis=0).mean():.3f}) ===")
    print(f"  observed mean {y.mean():.2f}   modelled mean {yhat.mean():.2f}")
    print(f"  C-G1  daily RMSE        {rmse:8.2f}   band [{G1_LO}, {G1_HI}]      {'PASS' if g1 else 'FAIL'}")
    print(f"  C-G2  seasonal r        {seas_r:8.3f}   >= {G2_MIN}                 {'PASS' if g2 else 'FAIL'}")
    print(f"  C-G3  level bias        {bias:+8.1f}%  |bias| <= {G3_MAX}%          {'PASS' if g3 else 'FAIL'}")
    print(f"  C-G4  R2 vs climatology {r2_vs_clim:8.3f}   > 0                     {'PASS' if g4 else 'FAIL'}")
    print(f"        (plain R2 vs mean: {r2_plain:.3f})")

    print("\n=== REGISTERED PRIORS vs OUTCOME ===")
    print(f"  prior: seasonal r >= 0.6           -> {seas_r:.3f}  {'held' if g2 else 'REFUTED'}")
    print(f"  prior: level 15-40% LOW            -> {bias:+.1f}%  "
          f"{'held' if -40 <= bias <= -15 else 'REFUTED'}")
    print(f"  prior: overall fail on level only  -> "
          f"{'held' if (g1 and g2 and g4 and not g3) else 'REFUTED'}")

    pd.DataFrame([dict(n_days=len(d), obs_mean=y.mean(), mod_mean=yhat.mean(), rmse=rmse,
                       seasonal_r=seas_r, level_bias_pct=bias, r2_vs_climatology=r2_vs_clim,
                       r2_plain=r2_plain, C_G1=g1, C_G2=g2, C_G3=g3, C_G4=g4)]).to_csv(OUT, index=False)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
