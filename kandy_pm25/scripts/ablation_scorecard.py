"""ablation_scorecard.py — Phase 3 of the evidence-hardening plan.

Quantify what each model component contributes, scored against a HELD-OUT ground network
(Kathmandu, 39 vaulted stations). Reads the ablation fields produced by
`xichang_prod.py --city <c> --stage field` with ABLATE={no_terrain,no_emission,no_pattern}
(additive headline) and ABLATE={no_winds,no_timing} (4factor scenario), plus the two full
fields (additive_v2 headline, 4factor multiplicative scenario).

Honest framing built into the design: the scored HEADLINE (additive_v2) uses P_local=S_emit·M,
so terrain/emission/pattern ablations move the SPATIAL rank while the temporal (seasonal/
diurnal) scores — driven by the T(t) anchor — stay put. That is the thesis, made measurable:
temporal skill is anchor-driven and robust; the spatial rank is the small structured residual
the physics supplies. Winds/timing modulate the 4factor transport scenario, not the headline.

Out: data/processed/decomp/ablation_scorecard_{city}.csv
     results/figures/paper_figures_v2/S2_ablation.png
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf
from scipy.stats import pearsonr, spearmanr
from scipy.interpolate import RegularGridInterpolator

OUTF = REPO / "results" / "figures" / "paper_figures_v2"
OUTF.mkdir(parents=True, exist_ok=True)

# label → filename stem (relative to decomp_{city}/)
VARIANTS = [
    ("full (headline)",     "additive_v2"),
    ("− terrain confinement", "additive_v2_abl_no_terrain"),
    ("− emission surface",   "additive_v2_abl_no_emission"),
    ("− all spatial (P=1)",  "additive_v2_abl_no_pattern"),
    ("multiplicative 4factor", "4factor"),
    ("4factor − winds",      "4factor_abl_no_winds"),
    ("4factor − timing",     "4factor_abl_no_timing"),
]


def _pred_for(stem, year):
    p = xf.DEC / f"{xf.CITY}_decomp_predictions_{year}_{stem}.parquet"
    if not p.exists():
        return None
    d = pd.read_parquet(p, columns=["time", "lat", "lon", "pm25_q50"])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert(xf.TZ)
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    st, _ = xf._stations_split()
    out = []
    for (t, loct), g in d.groupby(["time", "loct"]):
        Z = g.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
        f = RegularGridInterpolator((lats, lons), Z, bounds_error=False, fill_value=np.nan)
        v = f(np.column_stack([st.lat.to_numpy(), st.lon.to_numpy()]))
        out.append(pd.DataFrame({"loct": loct, "station_id": st.index, "pred": v}))
    return pd.concat(out, ignore_index=True).dropna(subset=["pred"])


def score(stem):
    st, anc = xf._stations_split()
    vault = [s for s in st.index if int(s) not in anc]
    P, O = [], []
    for y in xf.xp.YEARS:
        p = _pred_for(stem, y)
        if p is None:
            return None
        P.append(p); O.append(xf._obs(y))
    P = pd.concat(P); O = pd.concat(O)
    P = P[P.station_id.isin(vault)]; O = O[O.station_id.isin(vault)]
    pm = P.assign(m=P.loct.dt.month).groupby("m").pred.mean()
    om = O.assign(m=O.loct.dt.month).groupby("m").pm25.mean()
    idx = pm.reindex(om.index).dropna().index
    r_se = pearsonr(pm.loc[idx].values, om.loc[idx].values)[0]
    ph = P.assign(h=P.loct.dt.hour).groupby("h").pred.mean()
    oh = O.assign(h=O.loct.dt.hour).groupby("h").pm25.mean()
    r_di = pearsonr(ph.reindex(oh.index).values, oh.values)[0]
    ps = P.groupby("station_id").pred.mean(); os_ = O.groupby("station_id").pm25.mean()
    common = ps.index.intersection(os_.index)
    rho = spearmanr(ps[common], os_[common])[0] if len(common) >= 4 else np.nan
    lvl = 100 * (P.pred.mean() - O.pm25.mean()) / O.pm25.mean()
    return dict(seasonal=r_se, diurnal=r_di, spatial=rho, level=lvl)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--city", default="kathmandu")
    a = ap.parse_args()
    xf._setup(a.city)
    rows = []
    for lab, stem in VARIANTS:
        m = score(stem)
        if m is None:
            print(f"  {lab:26s} (field missing — skipped)"); continue
        m2 = dict(variant=lab, **{k: round(v, 3) for k, v in m.items()})
        rows.append(m2)
        print(f"  {lab:26s} seas {m['seasonal']:.2f}  diur {m['diurnal']:.2f}  "
              f"spatial {m['spatial']:.2f}  level {m['level']:+.0f}%")
    df = pd.DataFrame(rows)
    df.to_csv(xf.DEC / f"ablation_scorecard_{a.city}.csv", index=False)

    # figure: grouped bars, seasonal/diurnal/spatial per variant
    fig, ax = plt.subplots(figsize=(9.6, 3.4), constrained_layout=True)
    x = np.arange(len(df)); w = 0.26
    ax.bar(x - w, df.seasonal, w, label="seasonal r", color="#4C72B0")
    ax.bar(x, df.diurnal, w, label="diurnal r", color="#55A868")
    ax.bar(x + w, df.spatial, w, label="spatial ρ", color="#C44E52")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(x); ax.set_xticklabels(df.variant, rotation=30, ha="right", fontsize=7.4)
    ax.set_ylabel("skill"); ax.set_ylim(-0.1, 1.05)
    ax.set_title(f"Component ablation vs the {a.city.title()} held-out network (39 stations): temporal "
                 "skill is anchor-driven and robust; spatial rank is what the physics adds", fontsize=8.8)
    ax.legend(fontsize=7.5, ncol=3, loc="center", bbox_to_anchor=(0.5, 0.66),
              framealpha=0.95); ax.grid(alpha=0.25, axis="y")
    fig.savefig(OUTF / "S2_ablation.png", dpi=350, bbox_inches="tight"); plt.close(fig)
    print(f"\nwrote {xf.DEC/f'ablation_scorecard_{a.city}.csv'}\nwrote {OUTF/'S2_ablation.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
