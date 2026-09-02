"""C-H1..C-H4 -- does composition agree with what the decomposition calls its two terms?

Registered at https://osf.io/kx23c/ (2026-09-01) BEFORE this ran.

THE CLAIM UNDER TEST. The production model is PM = B + local increment, with B asserted to be
the regional/transboundary background. That is the load-bearing physical claim of the whole
formulation and every support it has is statistical. Composition can test it, because secondary
species (sulphate, nitrate, SOA) form over hours to days and mark an AGED, TRANSPORTED air mass,
while black and primary organic carbon mark LOCAL, FRESH combustion.

WHY NOT THE OBVIOUS TEST. Correlating B(t) against the secondary fraction is INADMISSIBLE:
build_additive_field_v2.py builds B via geoscf_daily_shape, so B's seasonal shape and the
speciation come from the same model, and the correlation would measure GEOS-CF's internal
consistency. The admissible classifier is back-trajectory SECTOR, derived from trajectory
geometry rather than from GEOS-CF chemistry.

⚠ Independence is partial: GEOS-CF's chemistry runs on its own meteorology, which is related to
the trajectories. What is not shared is the CHEMICAL prediction -- that continental Indian air
should be secondary-rich is an atmospheric-chemistry claim, not a meteorological one.

Usage:  .venv/Scripts/python.exe scripts/chemistry_origin_test.py
Out:    data/processed/modular/chemistry_origin_test.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "data" / "processed" / "modular" / "chemistry_origin_test.csv"

CONTINENTAL = ["Penin_India", "IGP_E_India"]
MARINE = ["BoB_marine", "SW_marine"]
RNG = np.random.default_rng(20260901)


def boot_median(x, n=2000):
    if len(x) < 3:
        return np.nan, np.nan
    b = [np.median(RNG.choice(x, len(x), replace=True)) for _ in range(n)]
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main() -> None:
    sp = pd.read_csv(DEC / "kandy_geoscf_speciation_daily.csv", parse_dates=["date"])
    sp["sec"] = sp.sulphate + sp.nitrate + sp.secondary_organic
    sp["pri"] = sp.black_carbon + sp.organic_carbon
    sp["sec_frac"] = sp.sec / (sp.sec + sp.pri)
    sp["oc_bc"] = sp.organic_carbon / sp.black_carbon.replace(0, np.nan)

    tr = pd.read_parquet(DEC / "w2" / "d1_trajectories_850.parquet")
    tr["date"] = pd.to_datetime(tr.date)
    # Daily class = dominant sector. The archive is 6-hourly and the sector changes within the
    # day on ~25% of days (F.44), so `unanimous` marks the days where all arrivals agree and is
    # carried as a sensitivity rather than as the headline.
    g = tr.groupby("date").sector
    daily = pd.DataFrame({"sector": g.agg(lambda s: s.mode().iloc[0]),
                          "unanimous": g.nunique().eq(1)}).reset_index()

    d = sp.merge(daily, on="date", how="inner")
    print(f"speciation {len(sp)} days | trajectories {daily.date.nunique()} days "
          f"| overlap {len(d)} days\n")

    rows = []
    print("=== secondary fraction by air-mass origin ===")
    print(f"  {'sector':<14}{'n':>6}{'median':>9}{'95% CI':>20}{'OC/BC':>8}")
    print("  " + "-" * 57)
    order = d.groupby("sector").sec_frac.median().sort_values()
    for sec in order.index:
        g_ = d[d.sector == sec]
        lo, hi = boot_median(g_.sec_frac.dropna().values)
        print(f"  {sec:<14}{len(g_):>6}{g_.sec_frac.median():>9.3f}"
              f"   [{lo:.3f}, {hi:.3f}]{g_.oc_bc.median():>8.1f}")
        rows.append(dict(kind="sector", label=sec, n=len(g_),
                         sec_frac=round(float(g_.sec_frac.median()), 4),
                         lo95=round(lo, 4), hi95=round(hi, 4),
                         oc_bc=round(float(g_.oc_bc.median()), 2)))

    cont = d[d.sector.isin(CONTINENTAL)].sec_frac.dropna()
    mar = d[d.sector.isin(MARINE)].sec_frac.dropna()
    loc = d[d.sector == "local_recirc"].sec_frac.dropna()

    print(f"\n  continental (n={len(cont)}) median {cont.median():.3f}")
    print(f"  marine      (n={len(mar)}) median {mar.median():.3f}")
    u, p = mannwhitneyu(cont, mar, alternative="two-sided")
    print(f"  Mann-Whitney two-sided p = {p:.3g}")

    # ── registered predictions ────────────────────────────────────────────────────────────
    ch1 = cont.median() > mar.median()
    ch2 = bool(order.index[0] == "local_recirc")
    d["month"] = d.date.dt.month
    def gap(mask):
        c = d[mask & d.sector.isin(CONTINENTAL)].sec_frac.median()
        m = d[mask & d.sector.isin(MARINE)].sec_frac.median()
        return c - m
    g_djfmam = gap(d.month.isin([12, 1, 2, 3, 4, 5]))
    g_jja = gap(d.month.isin([6, 7, 8]))
    ch3 = bool(np.nan_to_num(g_djfmam, nan=-9) > np.nan_to_num(g_jja, nan=9))
    monthly_ocbc = d.groupby("month").oc_bc.median()
    ch4 = bool((monthly_ocbc > 5).all())

    print("\n=== REGISTERED PREDICTIONS (osf.io/kx23c) ===")
    print(f"  C-H1  {'HELD    ' if ch1 else 'REFUTED '}  continental sec_frac "
          f"({cont.median():.3f}) > marine ({mar.median():.3f}), p={p:.3g}")
    print(f"  C-H2  {'HELD    ' if ch2 else 'REFUTED '}  local_recirc is the minimum sector "
          f"(it is '{order.index[0]}'; local_recirc = {loc.median():.3f}, n={len(loc)})")
    print(f"  C-H3  {'HELD    ' if ch3 else 'REFUTED '}  continental-marine gap larger in "
          f"DJF-MAM ({g_djfmam:+.3f}) than JJA ({g_jja:+.3f})")
    print(f"  C-H4  {'HELD    ' if ch4 else 'REFUTED '}  OC/BC > 5 in every month "
          f"(min monthly median {monthly_ocbc.min():.1f})")
    for k, ok in [("C-H1", ch1), ("C-H2", ch2), ("C-H3", ch3), ("C-H4", ch4)]:
        rows.append(dict(kind="prediction", label=k, n=len(d), sec_frac=int(ok)))

    # ── sensitivity: unanimous-sector days only ───────────────────────────────────────────
    un = d[d.unanimous]
    cu = un[un.sector.isin(CONTINENTAL)].sec_frac.dropna()
    mu = un[un.sector.isin(MARINE)].sec_frac.dropna()
    print(f"\n=== sensitivity: days where all 4 arrivals agree (n={len(un)}) ===")
    if len(cu) >= 3 and len(mu) >= 3:
        _, pu = mannwhitneyu(cu, mu, alternative="two-sided")
        print(f"  continental {cu.median():.3f} (n={len(cu)})  vs  marine {mu.median():.3f} "
              f"(n={len(mu)})   p={pu:.3g}   direction {'holds' if cu.median()>mu.median() else 'FLIPS'}")
        rows.append(dict(kind="sensitivity", label="unanimous_days", n=len(un),
                         sec_frac=round(float(cu.median() - mu.median()), 4)))
    else:
        print(f"  too few continental unanimous days (n={len(cu)}) to test")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print("\n[!] GEOS-CF is a model. This corroborates or contradicts the decomposition; it")
    print("    cannot validate it. And it tests the TEMPORAL origin claim, not the spatial one.")


if __name__ == "__main__":
    main()
