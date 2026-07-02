"""city_validation_scorecard.py — the consolidation deliverable: a single multi-city
held-out-network validation scorecard for the production v2 model applied across
monitored analogue cities (Xichang, Chiang Mai, Bazhou, Chandigarh, …).

Reuses the validated F10 logic (xichang_paper_figures._pred_at_stations / _obs /
_stations_split). For each city: seasonal r, diurnal r, level error %, spatial ρ vs
the HELD-OUT network. Output: a colour-coded scorecard table + a spatial-vs-temporal
summary panel → results/figures/multicity/validation_scorecard.png.

Run:  python scripts/city_validation_scorecard.py --cities xichang,chiangmai,bazhou,chandigarh
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
from src.stage1_satml.decomp import pubfig            # noqa: F401 (style)
import xichang_paper_figures as xf

OUT = REPO / "results" / "figures" / "multicity"
OUT.mkdir(parents=True, exist_ok=True)


def metrics(city):
    from scipy.stats import pearsonr, spearmanr
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
    pm = P.assign(m=P.loct.dt.month).groupby("m").pred.mean()
    om = O.assign(m=O.loct.dt.month).groupby("m").pm25.mean()
    r_se = pearsonr(pm.reindex(om.index).dropna().values,
                    om.loc[pm.reindex(om.index).dropna().index].values)[0]
    ph = P.assign(h=P.loct.dt.hour).groupby("h").pred.mean()
    oh = O.assign(h=O.loct.dt.hour).groupby("h").pm25.mean()
    r_di = pearsonr(ph.reindex(oh.index).values, oh.values)[0]
    ps = P.groupby("station_id").pred.mean(); os_ = O.groupby("station_id").pm25.mean()
    common = ps.index.intersection(os_.index)
    rho = spearmanr(ps[common], os_[common])[0] if len(common) >= 4 else np.nan
    obs_lvl = float(O.pm25.mean()); mod_lvl = float(P.pred.mean())
    return dict(city=xf.CFG["name"], regime=xf.CFG["regime"], n=len(vault),
                seasonal=r_se, diurnal=r_di, level=100 * (mod_lvl - obs_lvl) / obs_lvl,
                spatial=rho, obs=obs_lvl)


def build(cities, reuse=False):
    if reuse and (OUT / "validation_scorecard.csv").exists():
        df = pd.read_csv(OUT / "validation_scorecard.csv")
        print(f"  [reuse] {len(df)} cities from validation_scorecard.csv")
    else:
        rows = []
        for c in cities:
            try:
                m = metrics(c); rows.append(m)
                print(f"  {m['city']:16s} n={m['n']:2d}  seas {m['seasonal']:.2f}  diur {m['diurnal']:.2f}  "
                      f"level {m['level']:+.0f}%  spatial {m['spatial']:.2f}")
            except Exception as e:
                print(f"  {c}: FAIL {e}")
        df = pd.DataFrame(rows)
        df.to_csv(OUT / "validation_scorecard.csv", index=False)

    # ── scorecard table figure ──────────────────────────────────────────────
    fig = plt.figure(figsize=(9.5, 0.62 * len(df) + 2.3))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.4, 1.0], wspace=0.18)
    axt = fig.add_subplot(gs[0, 0]); axt.axis("off")
    cols = [("seasonal", "seasonal r", "≥0.80", "up"), ("diurnal", "diurnal r", "≥0.70", "up"),
            ("level", "level err", "|≤15|%", "lvl"), ("spatial", "spatial ρ", "≥0.40", "up")]
    xc = [0.0, 0.30, 0.45, 0.60, 0.75]
    ytop, dy = 0.86, 0.80 / max(len(df), 1)
    axt.text(xc[0], 0.97, "city / regime", fontweight="bold", fontsize=9, transform=axt.transAxes)
    for x, (_, lab, thr, _) in zip(xc[1:], cols):
        axt.text(x + 0.04, 0.97, f"{lab}\n{thr}", fontweight="bold", fontsize=8, va="top", ha="center", transform=axt.transAxes)
    for i, r in df.iterrows():
        y = ytop - (i + 0.5) * dy
        axt.text(xc[0], y, f"$\\bf{{{r.city}}}$\n{r.regime[:42]}", fontsize=7.4, va="center", transform=axt.transAxes)
        for x, (k, _, _, kind) in zip(xc[1:], cols):
            v = r[k]
            if kind == "up":
                thr = 0.80 if k == "seasonal" else (0.70 if k == "diurnal" else 0.40)
                ok = v >= thr; txt = f"{v:.2f}"
            else:
                ok = abs(v) <= 15; txt = f"{v:+.0f}%"
            col = "#2e8b57" if ok else ("#d9a441" if (kind == "lvl" and abs(v) <= 30) or
                                        (kind == "up" and v >= (0.20 if k == "spatial" else thr - 0.1)) else "#c0392b")
            axt.add_patch(plt.Rectangle((x - 0.02, y - dy * 0.42), 0.13, dy * 0.8, transform=axt.transAxes,
                          facecolor=col, alpha=0.18, edgecolor="none"))
            axt.text(x + 0.04, y, txt, fontsize=8.4, fontweight="bold", color=col, ha="center", va="center", transform=axt.transAxes)
    axt.set_title("Validation against held-out monitoring networks across analogue cities",
                  fontsize=10, pad=10, loc="left")

    # ── temporal-vs-spatial summary ─────────────────────────────────────────
    axs = fig.add_subplot(gs[0, 1])
    t_mean = df[["seasonal", "diurnal"]].mean(axis=1)
    axs.scatter(t_mean, df.spatial, s=90, c="#B35806", edgecolor="k", zorder=4)
    for _, r in df.iterrows():
        axs.annotate(r.city.split(" (")[0], (np.mean([r.seasonal, r.diurnal]), r.spatial),
                     (4, 2), textcoords="offset points", fontsize=6.8)
    axs.axhline(0.40, ls="--", color="grey", lw=0.8); axs.axvline(0.80, ls="--", color="grey", lw=0.8)
    axs.set_xlabel("temporal skill (mean seasonal+diurnal r)"); axs.set_ylabel("spatial rank ρ")
    axs.axhline(0.0, ls=":", color="0.7", lw=0.7)
    sp = df.spatial.dropna()
    axs.set_xlim(min(0.5, float(t_mean.min()) - 0.05), 1.03)
    axs.set_ylim(min(-0.15, float(sp.min()) - 0.05), max(0.75, float(sp.max()) + 0.08))
    axs.set_title("temporal vs fine-spatial skill", fontsize=8.6); axs.grid(alpha=0.25)
    fig.savefig(OUT / "validation_scorecard.png", dpi=350, bbox_inches="tight")
    plt.close(fig)
    print(f"\nwrote {OUT/'validation_scorecard.png'} + .csv  (N={len(df)} cities)")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", default="xichang,chiangmai,bazhou")
    ap.add_argument("--reuse", action="store_true", help="replot from saved CSV (skip recompute)")
    a = ap.parse_args()
    build([c.strip() for c in a.cities.split(",")], reuse=a.reuse)


if __name__ == "__main__":
    main()
