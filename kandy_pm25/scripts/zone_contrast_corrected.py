"""zone_contrast_corrected.py — Test B re-run on the corrected (anomaly) estimator
(2026-08-07).

WHY A RE-RUN AND NOT A NEW TEST
-------------------------------
Test B was pre-registered in `docs/prereg_spatial_resolution_2026-08-06.md` and passed all
three gates (B1 cross-city slope, B2 sign agreement, B3 recovery at station-null cities).
But it was computed on HOUR-MATCHED station means, and F.32-F.34 subsequently established
that those are contaminated: matching hours hands every station the temporal weighting of
its own observations, so a model with strong temporal skill and no spatial skill still
scores. The zone contrasts inherited that.

**The gates are NOT changed.** B1, B2 and B3 keep their pre-registered thresholds and the
same zone definition (terciles of the traffic emission surface, a model input using no
concentration data). Only the contaminated input is replaced by the validated one: per-hour
network-mean-removed anomalies, which cannot carry temporal skill into a spatial number.
Substituting a corrected computation into a fixed gate is a repair, not a re-specification;
re-tuning the gates after seeing the first result would have been the latter.

WHAT CHANGES MECHANICALLY
-------------------------
Zone contrast becomes a difference of ANOMALIES rather than of levels, so it is centred
near zero by construction and its absolute magnitude is not comparable with the earlier
run. B1 (slope of observed on modelled contrast) and B2 (sign agreement) are scale-free and
transfer unchanged. B3's "recovers a station-null city" is re-expressed against the CURRENT
significance list from F.34, not the superseded one.

PRIOR, STATED BEFORE RUNNING
----------------------------
The earlier Test B passed 3/3 on contaminated input. Since roughly half the paired signal
turned out to be temporal leakage at several cities, I expect the corrected slope to be
LOWER and sign agreement to drop from 9/9. I expect B1 to survive and B2 to be marginal.

Run:  .venv/Scripts/python.exe scripts/zone_contrast_corrected.py
Out:  results/figures/multicity/zone_contrast_corrected.{csv,json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf                       # noqa: E402

OUT = REPO / "results" / "figures" / "multicity"
CITIES = ["xichang", "chiangmai", "bazhou", "chandigarh", "kathmandu",
          "baoji", "taian", "yichang", "medellin", "bogota"]
MIN_ST, MIN_NET, NBOOT, SEED = 4, 3, 4000, 20260807
# cities NOT significant under the corrected estimator (F.34) -- B3 is scored on these
NULL_CITIES = {"Yichang", "Bazhong", "Chiang"}


def anomaly_means(city: str):
    xf._setup(city)
    st, anc = xf._stations_split()
    vault = [s for s in st.index if int(s) not in anc]
    P, O = [], []
    for y in xf.xp.YEARS:
        try:
            P.append(xf._pred_at_stations(y)); O.append(xf._obs(y))
        except Exception:
            continue
    P = pd.concat(P).dropna(subset=["pred"]); O = pd.concat(O)
    P = P[P.station_id.isin(vault)]; O = O[O.station_id.isin(vault)]
    J = P.merge(O[["loct", "station_id", "pm25"]], on=["loct", "station_id"], how="inner")
    J = J.assign(n_t=J.groupby("loct").pm25.transform("size"))
    J = J[J.n_t >= MIN_NET]
    if J.empty:
        return None, None, None
    J = J.assign(a_obs=J.pm25 - J.groupby("loct").pm25.transform("mean"),
                 a_mod=J.pred - J.groupby("loct").pred.transform("mean"))
    ao = J.groupby("station_id").a_obs.mean()
    am = J.groupby("station_id").a_mod.mean()
    c = ao.index.intersection(am.index)
    return (am[c], ao[c], st) if len(c) >= MIN_ST else (None, None, None)


def terciles(city: str, st, ids):
    """Zones from the traffic emission surface — a model input (pre-registered)."""
    from scipy.interpolate import RegularGridInterpolator
    t = np.load(REPO / "data" / "processed" / "decomp" / f"S_traffic_{city}.npz")
    S, la, lo = t["S_traffic"], t["lats"], t["lons"]
    f = RegularGridInterpolator(
        (np.linspace(la[0], la[-1], S.shape[0]), np.linspace(lo[0], lo[-1], S.shape[1])),
        S, bounds_error=False, fill_value=np.nan)
    sub = st.loc[[i for i in ids if i in st.index]]
    s = pd.Series(f(np.column_stack([sub.lat.to_numpy(), sub.lon.to_numpy()])),
                  index=sub.index).dropna()
    if len(s) < 3 or s.nunique() < 3:
        return None
    q = s.rank(pct=True)
    return pd.Series(np.where(q <= 1 / 3, "Z1", np.where(q >= 2 / 3, "Z3", "Z2")),
                     index=s.index)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # resumable: --cities picks a subset, results are merged with any earlier partial run.
    # Kathmandu alone can exhaust memory when other heavy jobs are resident, and losing
    # nine cities of compute to that is avoidable.
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", default=None)
    args, _ = ap.parse_known_args()
    todo = args.cities.split(",") if args.cities else CITIES
    part = OUT / "zone_contrast_corrected.csv"
    prev = pd.read_csv(part) if part.exists() else pd.DataFrame()
    print("=== Test B RE-RUN on the corrected (anomaly) estimator ===")
    print("    gates unchanged from docs/prereg_spatial_resolution_2026-08-06.md")
    print("    prior: slope LOWER, sign agreement below 9/9; B1 survives, B2 marginal\n")
    rows = []
    print("  city            obs Delta   mod Delta   agree   nZ1  nZ3")
    for city in todo:
        try:
            am, ao, st = anomaly_means(city)
        except Exception as e:                                      # noqa: BLE001
            print(f"  {city:<15} SKIP ({type(e).__name__}: {e})"); continue
        name = xf.CFG["name"].split(" (")[0].strip()
        if am is None:
            print(f"  {name:<15} not estimable"); continue
        z = terciles(city, st, list(am.index))
        if z is None or z.nunique() < 3:
            print(f"  {name:<15} zones not estimable"); continue
        do = float(ao.reindex(z.index)[z == "Z3"].mean() - ao.reindex(z.index)[z == "Z1"].mean())
        dm = float(am.reindex(z.index)[z == "Z3"].mean() - am.reindex(z.index)[z == "Z1"].mean())
        agree = bool(np.sign(do) == np.sign(dm))
        rows.append(dict(city=name, d_obs=do, d_mod=dm, agree=agree,
                         n_z1=int((z == "Z1").sum()), n_z3=int((z == "Z3").sum())))
        print(f"  {name:<15}{do:>+10.2f}{dm:>+12.2f}   {'AGREE' if agree else ' no  '}"
              f"{(z == 'Z1').sum():>6}{(z == 'Z3').sum():>5}")

    R = pd.concat([prev, pd.DataFrame(rows)], ignore_index=True) if len(prev) else pd.DataFrame(rows)
    R = R.drop_duplicates("city", keep="last")
    R.to_csv(part, index=False)
    if len(R) < 5:
        print(f"  partial: {len(R)} cities so far -- rerun with the remainder to gate")
        return
    dm, do = R.d_mod.to_numpy(float), R.d_obs.to_numpy(float)

    rng = np.random.default_rng(SEED)
    slope = float(np.polyfit(dm, do, 1)[0]) if len(dm) >= 4 else np.nan
    bs = []
    for _ in range(NBOOT):
        k = rng.integers(0, len(dm), len(dm))
        if len(np.unique(k)) < 3:
            continue
        try:
            bs.append(float(np.polyfit(dm[k], do[k], 1)[0]))
        except Exception:                                            # noqa: BLE001
            continue
    lo_, hi_ = (np.percentile(bs, [5, 95]) if bs else (np.nan, np.nan))
    b1 = bool(np.isfinite(lo_) and lo_ > 0)
    nsign = int(R.agree.sum())
    b2 = nsign >= 7
    rec = [r.city for r in R.itertuples()
           if r.city.split()[0] in NULL_CITIES and r.agree and abs(r.d_obs) > 0.5]
    b3 = len(rec) >= 2

    print("\n" + "=" * 62 + "\n  PRE-REGISTERED GATES (unchanged)\n" + "=" * 62)
    print(f"  B1  slope > 0, 90% CI excludes 0 : {slope:+.3f} [{lo_:+.3f}, {hi_:+.3f}]"
          f"   -> {'PASS' if b1 else 'FAIL'}")
    print(f"  B2  sign agreement >= 7 of 9     : {nsign} of {len(R)}"
          f"   -> {'PASS' if b2 else 'FAIL'}")
    print(f"  B3  recovers >=2 non-significant : {rec}   -> {'PASS' if b3 else 'FAIL'}")

    npass = sum([b1, b2, b3])
    verdict = (
        ("Zone contrast SURVIVES the estimator correction. The coarser claim is validated "
         "on a statistic that cannot launder temporal skill, and it recovers structure at "
         "cities where the station-level rank is not significant — which is the specific "
         "reason to report zones alongside stations."
         if npass == 3 else
         "Zone contrast PARTIALLY survives; report only the gates that passed and do not "
         "present it as a validated replacement for the station rank."
         if npass == 2 else
         "Zone contrast does NOT survive the correction. The earlier 3/3 pass was carried "
         "by temporal leakage in the paired means, and no zone-level claim may be made."))
    print(f"\n  VERDICT ({npass}/3): {verdict}")
    (OUT / "zone_contrast_corrected.json").write_text(json.dumps({
        "gates": {"B1": b1, "B2": b2, "B3": b3}, "n_pass": npass,
        "slope": None if not np.isfinite(slope) else round(slope, 4),
        "slope_ci90": [None if not np.isfinite(lo_) else round(float(lo_), 4),
                       None if not np.isfinite(hi_) else round(float(hi_), 4)],
        "sign_agreement": f"{nsign}/{len(R)}", "b3_recovered": rec,
        "per_city": {r.city: {"d_obs": round(r.d_obs, 3), "d_mod": round(r.d_mod, 3),
                              "agree": bool(r.agree)} for r in R.itertuples()},
        "note": ("Contrasts are differences of per-hour network-mean-removed ANOMALIES, so "
                 "they are centred near zero and their magnitudes are not comparable with "
                 "the superseded paired-mean run. B1 and B2 are scale-free."),
        "prior": "expected lower slope and sign agreement below 9/9",
        "verdict": verdict}, indent=1, default=float), encoding="utf-8")
    print("\nwrote zone_contrast_corrected.{csv,json}")


if __name__ == "__main__":
    main()
