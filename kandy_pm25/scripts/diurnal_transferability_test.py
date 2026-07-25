"""diurnal_transferability_test.py — is the diurnal SHAPE transferable between cities
at all? The cheap pre-test that decides whether a 199-city hourly met pull is worth it.

Why. Option A (fixed sensor-free box model) reached LOCO diurnal r = 0.412 median;
Option B (learned, but only 5 training cities per fold) did WORSE at 0.299 — data
starvation. Both fall short of the shipped 2-sensor 0.708. The open question is whether
a properly powered panel model (199 cities, needing a NEW hourly ERA5 pull) would close
the gap, or whether the diurnal cycle is irreducibly city-specific.

This test answers the necessary condition WITHOUT the pull, using the hourly CNEMC panel
station data already on disk (199 cities x monthly parquets):

  1. How similar are cities' observed diurnal shapes to each other? (pairwise r)
  2. How much of one city's shape does the PANEL MEAN shape explain? That is the
     ceiling for any model that has no local information -- a model can never beat
     "predict the average city" unless meteorology carries city-specific timing.
  3. Is that ceiling above the 2-sensor 0.708 the product already achieves?

Logic: if the panel-mean shape already explains a held-out city's diurnal cycle well,
a panel model has a real target and the hourly pull is justified. If cities' shapes are
mutually uncorrelated, no met data can transfer them and the pull is pointless.

Out: results/figures/multicity/diurnal_transferability.{csv,txt}
"""
from __future__ import annotations
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PANEL = REPO / "data" / "processed" / "cnemc_panel" / "cities"
OUT = REPO / "results" / "figures" / "multicity"
MIN_HOURS = 6000               # need a stable diurnal climatology
MAX_CITIES = 199


def city_diurnal(cdir: Path):
    """Unit-mean observed diurnal climatology (local time) for one panel city."""
    fs = sorted(glob.glob(str(cdir / "*.parquet")))
    if not fs:
        return None
    keep = []
    for f in fs:
        try:
            d = pd.read_parquet(f)
        except Exception:
            continue
        tc = next((c for c in d.columns if c.lower() in
                   ("datetime", "time", "datetime_utc", "date")), None)
        pc = next((c for c in d.columns if "pm25" in c.lower()), None)
        if tc is None or pc is None:
            continue
        keep.append(d[[tc, pc]].rename(columns={tc: "t", pc: "pm"}))
    if not keep:
        return None
    d = pd.concat(keep, ignore_index=True)
    d["t"] = pd.to_datetime(d.t, errors="coerce")
    d = d.dropna(subset=["t", "pm"])
    d = d[(d.pm > 0) & (d.pm < 1000)]
    if len(d) < MIN_HOURS:
        return None
    # CNEMC timestamps are Beijing time (UTC+8) -> already local for these cities
    d["h"] = d.t.dt.hour
    d["day"] = d.t.dt.floor("D")
    # unit-mean-per-day, then average over days: isolates SHAPE from level exactly as
    # the product would use it (daily level is Track T-a's job)
    dm = d.groupby("day").pm.transform("mean")
    d = d[dm > 0]
    d["s"] = d.pm / dm[dm > 0]
    clim = d.groupby("h").s.mean()
    if len(clim) < 24 or not np.isfinite(clim).all():
        return None
    return (clim / clim.mean()).reindex(range(24))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dirs = sorted([p for p in PANEL.iterdir() if p.is_dir()])[:MAX_CITIES]
    shapes = {}
    for i, cd in enumerate(dirs):
        s = city_diurnal(cd)
        if s is not None:
            shapes[cd.name] = s
        if (i + 1) % 50 == 0:
            print(f"  scanned {i+1}/{len(dirs)} panel cities, {len(shapes)} usable")
    print(f"usable panel cities with a stable diurnal climatology: {len(shapes)}")
    if len(shapes) < 20:
        print("too few for a transferability estimate"); return

    M = pd.DataFrame(shapes)                     # 24 x n_cities
    # 1. pairwise similarity between cities' shapes
    C = M.corr()
    iu = np.triu_indices_from(C.values, k=1)
    pair = C.values[iu]
    # 2. leave-one-city-out: how well does the PANEL MEAN shape explain a held-out city?
    loco = {}
    for c in M.columns:
        mean_other = M.drop(columns=[c]).mean(axis=1)
        loco[c] = float(np.corrcoef(M[c], mean_other)[0, 1])
    lo = pd.Series(loco)
    # amplitude spread: do cities even share a swing magnitude?
    amp = M.max() - M.min()

    t = pd.DataFrame({"city": M.columns, "r_vs_panel_mean": lo.values.round(3),
                      "amplitude": amp.values.round(3)}).sort_values(
                          "r_vs_panel_mean", ascending=False)
    t.to_csv(OUT / "diurnal_transferability.csv", index=False)

    L = ["DIURNAL TRANSFERABILITY — the necessary condition for a panel-learned cycle",
         "=" * 80,
         f"panel cities with a stable diurnal climatology: {len(shapes)}",
         "shape = observed hourly / that day's mean, averaged over days (unit mean)", "",
         "1. pairwise similarity BETWEEN cities' diurnal shapes",
         f"     median r = {np.median(pair):+.3f}   IQR [{np.percentile(pair,25):+.3f},"
         f" {np.percentile(pair,75):+.3f}]   frac r>0.8 = {(pair>0.8).mean():.2f}",
         "",
         "2. leave-one-city-out: PANEL MEAN shape vs the held-out city's shape",
         "   (this is the CEILING for any model with no local information)",
         f"     median r = {lo.median():+.3f}   10th pct = {lo.quantile(0.1):+.3f}"
         f"   frac r>=0.80 = {(lo>=0.80).mean():.2f}   frac r>=0.60 = {(lo>=0.60).mean():.2f}",
         "",
         "3. amplitude (max-min of the unit-mean shape)",
         f"     median {amp.median():.3f}   IQR [{amp.quantile(.25):.3f}, {amp.quantile(.75):.3f}]",
         ""]
    ceiling = lo.median()
    L += [f"REFERENCE: shipped 2-sensor diurnal r median = 0.708;",
          f"           Option A fixed box model = 0.412;  Option B learned (5 cities) = 0.299",
          ""]
    if ceiling >= 0.80:
        v = ("TRANSFERABLE — cities share a common diurnal shape, and simply predicting the\n"
             "         panel-mean shape already beats both sensorless attempts AND the\n"
             "         2-sensor product. A panel model has a real target: the 199-city hourly\n"
             "         ERA5 pull is JUSTIFIED, and a large part of the win may need no met at\n"
             "         all (a climatological shape conditioned on city descriptors).")
    elif ceiling >= 0.60:
        v = ("PARTLY TRANSFERABLE — a common shape explains much but not all. A panel model\n"
             "         could plausibly reach the 2-sensor level; the pull is a reasonable bet.")
    else:
        v = ("NOT TRANSFERABLE — cities' diurnal shapes are mutually too dissimilar, so no\n"
             "         amount of met data can transfer them. The 199-city hourly pull would NOT\n"
             "         fix the sensorless diurnal. Keep the disclosed 2-sensor product.")
    L += [f"VERDICT: {v}"]
    txt = "\n".join(L)
    (OUT / "diurnal_transferability.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)


if __name__ == "__main__":
    main()
