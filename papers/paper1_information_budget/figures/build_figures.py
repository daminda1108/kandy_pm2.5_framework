"""build_figures.py -- Paper 1 figures, every number read from the scored result files (FIGURE_PLAN.md).

Usage: python papers/paper1_information_budget/figures/build_figures.py [--figs 3,4]
Out:   papers/paper1_information_budget/figures/fig{N}_*.{pdf,png}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                                           # noqa: E402
from matplotlib.lines import Line2D                                       # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
LV2 = ROOT / "kandy_pm25" / "data" / "processed" / "modular" / "ladder_v2"
WIDTH = 6.5                                    # in; full text width, prints at 100 % in a 6.5 in column

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 9,
    "axes.labelsize": 9, "axes.titlesize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 400, "savefig.bbox": "tight", "pdf.fonttype": 42,
})

# Okabe-Ito (colour-blind safe)
C_CONF, C_PROS, C_DISC = "#000000", "#0072B2", "#999999"
VAR_COL = ["#000000", "#E69F00", "#56B4E9", "#009E73", "#CC79A7", "#D55E00"]

ENDPOINTS = [  # key, label, unit
    ("first2_rmse", "H1  first two stations", "% RMSE"),
    ("s36_rmse", "H2  stations 3–6", "% RMSE"),
    ("bg_rmse", "H3  background", "% RMSE"),
    ("bgm2_rmse", "H4  background − first two", "points"),
    ("bgm2_exceed", "H5  same, exceedance days", "points"),
]


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"{name}.{ext}")
    plt.close(fig)
    print("wrote", HERE / f"{name}.png")


# ── Fig. 3 ─────────────────────────────────────────────────────────────────────────────────────
def fig3() -> None:
    conf = load(LV2 / "confirm_REGISTERED_summary.json")
    disc = load(LV2 / "maiac_s21_b5_crossfit_c18_grid_dv2_summary.json")
    series = [("confirmation, reconstruction", conf["reconstruction"], C_CONF, "o", True),
              ("confirmation, prospective", conf["prospective"], C_PROS, "o", False),
              ("discovery (exploratory)", disc["reconstruction"], C_DISC, "D", True)]
    fig, ax = plt.subplots(figsize=(WIDTH, 3.3))
    n = len(ENDPOINTS)
    for i, (key, label, _) in enumerate(ENDPOINTS):
        y = n - 1 - i
        if key == "s36_rmse":                                   # registered equivalence bound
            ax.add_patch(plt.Rectangle((-1, y - 0.38), 2, 0.76, color="#DDDDDD", zorder=0, lw=0))
        for j, (_, src, col, mk, filled) in enumerate(series):
            e = src.get(f"pooled.{key}")
            if not e:
                continue
            yy = y + (0.22 - 0.22 * j)
            lo, hi = e["cluster"]
            ax.plot([lo, hi], [yy, yy], color=col, lw=1.2, zorder=2)
            ax.plot(e["median"], yy, marker=mk, ms=5, color=col, zorder=3,
                    mfc=col if filled else "white", mew=1.1)
            if j == 0:
                ax.text(hi + 1.2, yy, f"{e['median']:+.1f}  (n = {e['n']})", va="center", fontsize=7.5)
    ax.axvline(0, color="#555555", lw=0.8, zorder=1)
    ax.set_yticks(range(n))
    ax.set_yticklabels([lab for _, lab, _ in ENDPOINTS][::-1])
    ax.set_xlabel("gain: % reduction in daily RMSE (H1–H3); difference in points of gain (H4, H5)")
    ax.set_xlim(-25, 85)
    ax.set_ylim(-0.6, n - 0.4)
    handles = [Line2D([], [], color=c, marker=m, mfc=c if f else "white", lw=1.2, ms=5, label=l)
               for l, _, c, m, f in series]
    handles.append(plt.Rectangle((0, 0), 1, 1, color="#DDDDDD", label="H2 registered bound [−1, +1]"))
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False)
    save(fig, "fig3_confirmation")


SHORT = {"first2_rmse": "H1\nfirst two", "s36_rmse": "H2\nstations 3–6", "bg_rmse": "H3\nbackground",
         "bgm2_rmse": "H4\nbackground −\nfirst two", "bgm2_exceed": "H5\nsame,\nexceedances"}


# ── Fig. 4 ─────────────────────────────────────────────────────────────────────────────────────
def fig4() -> None:
    conf = load(LV2 / "confirm_REGISTERED_summary.json")["reconstruction"]
    rich = load(LV2 / "rich_REGISTERED_summary.json")
    lrn = load(LV2 / "learners_REGISTERED_summary.json")
    full = load(LV2 / "fullnet_full_summary.json")["reconstruction"]
    variants = [
        ("confirmed baseline", lambda k: conf.get(f"pooled.{k}")),
        ("+ CAMS, NO$_2$, fires, rain, terrain", lambda k: rich.get(f"reconstruction.confirmation.{k}_r")),
        ("TabPFN", lambda k: lrn.get(f"L1.reconstruction.confirmation.{k}")),
        ("recurrent network (14 d)", lambda k: lrn.get(f"L2.reconstruction.confirmation.{k}")),
        ("boosting + ventilation", lambda k: lrn.get(f"L3.reconstruction.confirmation.{k}")),
        ("full station networks", lambda k: full.get(f"pooled.{k}")),
    ]
    fig, axes = plt.subplots(1, len(ENDPOINTS), figsize=(WIDTH, 2.7), sharey=True)
    nv = len(variants)
    for a, (key, label, unit) in zip(axes, ENDPOINTS):
        base = variants[0][1](key)
        a.axvline(base["median"], color="#BBBBBB", lw=0.8, ls="--", zorder=0)
        a.axvline(0, color="#555555", lw=0.8, zorder=1)
        if key == "s36_rmse":
            a.axvspan(-1, 1, color="#EEEEEE", zorder=0, lw=0)
        for i, (vname, get) in enumerate(variants):
            e = get(key)
            if not e:
                continue
            y = nv - 1 - i
            lo, hi = e["cluster"]
            a.plot([lo, hi], [y, y], color=VAR_COL[i], lw=1.2)
            a.plot(e["median"], y, "o", ms=4.2, color=VAR_COL[i])
        a.set_title(SHORT[key], fontsize=8)
        a.set_xlabel(unit, fontsize=8)
        a.tick_params(axis="x", labelsize=7)
    axes[0].set_yticks(range(nv))
    axes[0].set_yticklabels([v for v, _ in variants][::-1])
    axes[0].set_ylim(-0.6, nv - 0.4)
    fig.subplots_adjust(wspace=0.22)
    save(fig, "fig4_robustness")


SC = ROOT / "kandy_pm25" / "data" / "processed" / "modular"
FRAMES = [("registered (one year per site)", SC / "spatial_curve", "-"),
          ("full station records", SC / "spatial_curve_full", "--")]
EST = [("E1", "free built-up raster", "#999999"), ("E2", "land-use regression", "#E69F00"),
       ("E3", "kriging", "#0072B2"), ("E5", "regression kriging", "#009E73"),
       ("E10", "convolutional neural process", "#CC79A7")]
TROP = ("tropical", "deep_tropical")


# ── Fig. 7 ─────────────────────────────────────────────────────────────────────────────────────
def fig7() -> None:
    import pandas as pd
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDTH, 2.9), gridspec_kw={"width_ratios": [1.55, 1]})
    ks = None
    for fname, d, ls in FRAMES:
        P = pd.read_csv(d / "analysis" / "curve_q1_pooled.csv")
        ks = sorted(P.k.unique())
        pos = {k: i for i, k in enumerate(ks)}
        for est, lab, col in EST:
            q = P[P.est == est].sort_values("k")
            if q.empty:
                continue
            a.plot([pos[k] for k in q.k], q["median"], ls=ls, color=col, lw=1.4, marker="o", ms=2.8)
    # city counts per k, read from the data
    cnt = {fn: pd.read_csv(d / "analysis" / "curve_q1_pooled.csv").query("est == 'E1'").set_index("k").cities
           for fn, d, _ in FRAMES}
    a.set_xticks(range(len(ks)))
    a.set_xticklabels([f"{k}\n{int(cnt[FRAMES[0][0]].get(k, 0))}/{int(cnt[FRAMES[1][0]].get(k, 0))}"
                       for k in ks], fontsize=7)
    a.set_xlabel("fitting stations k\n(cities: registered / full records)", fontsize=8)
    a.set_ylabel("median within-city rank correlation")
    a.set_title("(a) pooled curves", fontsize=9, loc="left")
    h = [Line2D([], [], color=c, lw=1.4, label=l) for _, l, c in EST]
    h += [Line2D([], [], color="k", ls=ls, lw=1.2, label=f) for f, _, ls in FRAMES]
    a.legend(handles=h, fontsize=6.8, frameon=False, loc="upper left", ncol=1)
    # (b) crossover per city
    cats = ["3", "5", "8", "12", "18", "25", "35", "never"]
    width = 0.38
    for j, (fname, d, ls) in enumerate(FRAMES):
        X = pd.read_csv(d / "analysis" / "crossover_city.csv").rename(columns={"Unnamed: 0": "cluster"})
        C = pd.read_csv(d / "frame_cities.csv")
        X = X[X.cluster.isin(C[C.primary.astype(bool)].cluster)]
        first = X[["E3", "E5"]].min(axis=1)
        vals = ["never" if pd.isna(v) else str(int(v)) for v in first]
        counts = [vals.count(c) for c in cats]
        xs = [i + (j - 0.5) * width for i in range(len(cats))]
        b.bar(xs, counts, width=width, color="#0072B2" if j == 0 else "white", edgecolor="#0072B2",
              hatch=None if j == 0 else "////", lw=0.8, label=f"{fname} ({len(vals)} cities)")
    b.set_xticks(range(len(cats)))
    b.set_xticklabels(cats, fontsize=7)
    b.set_xlabel("first k at which kriging or regression\nkriging beats the raster", fontsize=8)
    b.set_ylabel("cities")
    b.set_title("(b) crossover, per city", fontsize=9, loc="left")
    b.set_ylim(0, b.get_ylim()[1] * 1.45)
    b.legend(fontsize=6.8, frameon=False, loc="upper center")
    fig.tight_layout()
    save(fig, "fig7_spatial_curve")


# ── Fig. 8 ─────────────────────────────────────────────────────────────────────────────────────
def fig8() -> None:
    import pandas as pd
    d = SC / "spatial_curve_full"
    C = pd.read_csv(d / "frame_cities.csv")
    ck = pd.read_csv(d / "analysis" / "curve_q1_city.csv")
    f3 = load(d / "F3_tropical_arm.json")["registered"]
    temp = C[C.primary.astype(bool) & ~C.band.isin(TROP)].cluster
    env = ck[(ck.est == "E3") & ck.cluster.isin(temp)].groupby("k").rho.agg(["min", "max", "median"])
    ks = list(env.index)
    pos = {k: i for i, k in enumerate(ks)}
    fig, ax = plt.subplots(figsize=(WIDTH * 0.72, 3.0))
    ax.fill_between(range(len(ks)), env["min"], env["max"], color="#DDDDDD", lw=0,
                    label=f"envelope, {len(temp)} non-tropical cities")
    ax.plot(range(len(ks)), env["median"], color="#888888", lw=1, ls=":", label="their median")
    arm = C[C.band_arm.astype(bool)]
    cols = ["#D55E00", "#0072B2", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#882255", "#000000"]
    for col, r in zip(cols, arm.itertuples()):
        g = ck[(ck.cluster == r.cluster) & (ck.est == "E3")].sort_values("k")
        g = g[g.k.isin(pos)]
        if g.empty:
            continue
        lab = f"{r.country}, {r.sites} sites" + (" (deep tropical)" if r.band == "deep_tropical" else "")
        ax.plot([pos[k] for k in g.k], g.rho, color=col, lw=1.3, marker="o", ms=3, label=lab)
    ax.axhline(0, color="#555555", lw=0.6)
    ax.set_xticks(range(len(ks)))
    ax.set_xticklabels([str(k) for k in ks], fontsize=7)
    ax.set_xlabel("fitting stations k")
    ax.set_ylabel("kriging (E3): within-city rank correlation")
    ax.text(0.99, 0.02, f"detection limit {f3['detection_limit']:.2f} ({f3['arm_countries']} countries)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7)
    ax.legend(fontsize=6.5, frameon=False, loc="center left", bbox_to_anchor=(1.0, 0.5))
    save(fig, "fig8_tropical_arm")


# ── Fig. 6 ─────────────────────────────────────────────────────────────────────────────────────
def fig6() -> None:
    import pandas as pd
    V = SC / "verify_2026-09-25"
    key = "deep_tropical.bg_minus_first2"
    prod = load(V / "honesty_maiac.json")["prod"][key]
    S = pd.read_csv(V / "honesty_seeds_maiac.csv").sort_values(f"{key}.median").reset_index(drop=True)
    v2 = load(LV2 / "maiac_s21_b5_crossfit_c18_grid_dv2_summary.json")["reconstruction"]["deep_tropical.bgm2_rmse"]
    rows = [("one split, one seed\n(as first reported)", prod["median"], prod["lo"], prod["hi"], "#D55E00", "s")]
    for i, r in S.iterrows():
        rows.append((None, r[f"{key}.median"], r[f"{key}.lo"], r[f"{key}.hi"], None, "o"))
    rows.append(("averaged over 21 splits\nand 5 seeds (ladder v2)", v2["median"], *v2["cluster"], "#000000", "D"))
    n = len(rows)
    fig, ax = plt.subplots(figsize=(WIDTH * 0.8, 3.6))
    excl = 0
    for i, (lab, m, lo, hi, col, mk) in enumerate(rows):
        y = n - 1 - i + (0.6 if i == 0 else (-0.6 if i == n - 1 else 0))
        if col is None:
            ex = lo > 0 or hi < 0
            excl += ex
            col = "#0072B2" if ex else "#AAAAAA"
        ax.plot([lo, hi], [y, y], color=col, lw=1.3 if mk != "o" else 0.9)
        ax.plot(m, y, marker=mk, ms=5 if mk != "o" else 3.5, color=col)
    ax.axvline(0, color="#555555", lw=0.8)
    ax.set_yticks([n - 1 + 0.6, (n - 1) / 2, -0.6])
    ax.set_yticklabels([rows[0][0], f"20 other splits\n({excl} of 20 exclude 0, blue)", rows[-1][0]], fontsize=8)
    ax.set_xlabel("deep tropics: background − first two stations (points of RMSE gain)\n"
                  "negative = local stations ahead")
    save(fig, "fig6_one_split")


# ── Fig. 5 ─────────────────────────────────────────────────────────────────────────────────────
BAND_COL = {"temperate": "#0072B2", "subtropical": "#009E73", "tropical": "#E69F00", "deep_tropical": "#D55E00"}


def fig5() -> None:
    import numpy as np
    import pandas as pd
    conf = pd.read_csv(LV2 / "confirm_REGISTERED_percity_reconstruction.csv", index_col=0)
    disc = pd.read_csv(LV2 / "maiac_s21_b5_crossfit_c18_grid_dv2_percity_reconstruction.csv", index_col=0)
    cs = load(LV2 / "confirm_REGISTERED_summary.json")["reconstruction"]
    ds = load(LV2 / "maiac_s21_b5_crossfit_c18_grid_dv2_summary.json")["reconstruction"]
    rng = np.random.default_rng(1)
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.8), sharey=True)
    for a, key, title in ((axes[0], "bgm2_rmse", "(a) ordinary days (RMSE loss)"),
                          (axes[1], "bgm2_exceed", "(b) guideline exceedances")):
        groups = [("confirmation\n(all bands)", conf, cs[f"pooled.{key}"], 1.0),
                  ("discovery, deep\ntropics (exploratory)", disc[disc.band == "deep_tropical"],
                   ds[f"deep_tropical.{key}"], 0.0)]
        for name, D, summ, y in groups:
            v = D[[key, "band"]].dropna()
            jit = rng.uniform(-0.18, 0.18, len(v))
            a.scatter(v[key], y + jit, s=9, c=[BAND_COL.get(b, "#777777") for b in v.band], alpha=0.75,
                      lw=0, zorder=2)
            lo, hi = summ["cluster"]
            a.plot([lo, hi], [y - 0.32, y - 0.32], color="k", lw=1.6, zorder=3)
            a.plot(summ["median"], y - 0.32, "D", color="k", ms=4.5, zorder=4)
            a.text(hi, y - 0.32, f"  {summ['median']:+.1f}  (n = {summ['n']})".replace("-", "−"), va="center",
                   fontsize=7)
        a.axvline(0, color="#555555", lw=0.8)
        a.set_title(title, fontsize=9, loc="left")
        a.set_xlabel("background − first two (points)\n← local stations ahead · background ahead →", fontsize=8)
    axes[0].set_yticks([1.0, 0.0])
    axes[0].set_yticklabels([g[0] for g in groups][::1] if False else ["confirmation\n(all bands)",
                                                                      "discovery, deep\ntropics (exploratory)"])
    axes[0].set_ylim(-0.6, 1.4)
    h = [Line2D([], [], marker="o", ls="", color=c, ms=4, label=b.replace("_", " ")) for b, c in BAND_COL.items()]
    h.append(Line2D([], [], marker="D", color="k", ms=4, lw=1.6, label="median, cluster 95 %"))
    fig.legend(handles=h, loc="lower center", ncol=5, frameon=False, fontsize=7, bbox_to_anchor=(0.55, -0.2))
    fig.subplots_adjust(wspace=0.08)
    save(fig, "fig5_city_by_city")


# ── Fig. 9 ─────────────────────────────────────────────────────────────────────────────────────
def fig9() -> None:
    M = SC / "verify_2026-09-25" / "mde_recompute.json"
    mde = load(M)
    emb = load(SC / "embedding_spatial_test.json")["tests"]
    tour = load(SC / "spatial_tournament.json")["families"]
    sit = load(SC / "siting_experiment.json")["paired_vs_convenience"]["clhs"]
    t = mde["tests"]
    c2 = mde["C2_phase2_bootstrap"]
    rows = [("learned pattern (2jyfg)", c2["median"], c2["lo"], c2["hi"], t["2jyfg_phase2_learned_minus_baseline"]["mde"], True),
            ("EO embeddings alone, E1 (6udm3)", emb["E1"]["median"], emb["E1"]["lo"], emb["E1"]["hi"],
             t["6udm3_E1_emb_minus_bench"]["mde"], True),
            ("embeddings + 60 predictors, E2 (6udm3)", emb["E2"]["median"], emb["E2"]["lo"], emb["E2"]["hi"],
             t["6udm3_E2_combined_minus_existing"]["mde"], True)]
    fam = [("gp_covariates", "Gaussian process"), ("lur_stepwise", "stepwise land-use regression"),
           ("ridge", "ridge regression"), ("mixed_effects", "mixed model"), ("elasticnet", "elastic net"),
           ("random_forest", "random forest"), ("gradient_boost", "gradient boosting")]
    for k, lab in fam:
        f = tour[k]
        rows.append((lab, f["paired"], f["lo"], f["hi"], t[f"F105_{k}_minus_benchmark"]["mde"], False))
    rows.append(("siting by design vs convenience", sit["median"], sit["lo"], sit["hi"], None, False))
    n = len(rows)
    fig, ax = plt.subplots(figsize=(WIDTH * 0.85, 3.6))
    for i, (lab, m, lo, hi, d, reg) in enumerate(rows):
        y = n - 1 - i
        col = "#000000" if reg else "#666666"
        ax.plot([lo, hi], [y, y], color=col, lw=1.3)
        ax.plot(m, y, "o", color=col, ms=4.5, mfc=col if reg else "white")
        if d is not None:
            ax.plot([d, d], [y - 0.3, y + 0.3], color="#D55E00", lw=1.6)
    ax.axvline(0, color="#555555", lw=0.8)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=8)
    for tl, r in zip(ax.get_yticklabels(), rows[::-1]):
        tl.set_fontweight("bold" if r[5] else "normal")
    ax.set_xlabel("paired advantage over the built-up benchmark (within-city rank correlation)")
    h = [Line2D([], [], color="k", marker="o", lw=1.3, label="registered test"),
         Line2D([], [], color="#666666", marker="o", mfc="white", lw=1.3, label="exploratory"),
         Line2D([], [], color="#D55E00", lw=1.6, label="smallest effect the test could detect (δ)")]
    ax.legend(handles=h, fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.16), ncol=3)
    save(fig, "fig9_spatial_nulls")


# ── Fig. 2 ─────────────────────────────────────────────────────────────────────────────────────
def fig2() -> None:
    import sys
    import cartopy
    import cartopy.crs as ccrs
    import cartopy.io.shapereader as shpreader
    import pandas as pd
    sys.path.insert(0, str(ROOT / "kandy_pm25"))
    from src.modular.city_meta import city_meta
    disc_ids = pd.read_csv(LV2 / "maiac_s21_b5_crossfit_c18_grid_dv2_percity_reconstruction.csv", index_col=0).index
    D = city_meta([str(c) for c in disc_ids])
    P = pd.read_csv(SC / "confirmation" / "confirmation_panel.csv")
    scored = set(pd.read_csv(LV2 / "confirm_REGISTERED_percity_reconstruction.csv", index_col=0).index)
    P["scored"] = P.cid.isin(scored)
    P["ref"] = (P.n_ref / P.n) >= 0.5
    land = Path(cartopy.config["data_dir"]) / "shapefiles" / "natural_earth" / "physical" / "ne_110m_land.shp"
    if not land.exists():
        raise FileNotFoundError(land)
    fig = plt.figure(figsize=(WIDTH, 3.5))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
    ax.set_extent([-180, 180, -50, 72], crs=ccrs.PlateCarree())
    ax.add_geometries(shpreader.Reader(str(land)).geometries(), ccrs.PlateCarree(), facecolor="#EEEEEE",
                      edgecolor="#BBBBBB", lw=0.3)
    for lat in (-23.5, 23.5, -15, 15):
        ax.plot([-180, 180], [lat, lat], transform=ccrs.PlateCarree(), color="#999999", lw=0.4,
                ls="--" if abs(lat) == 23.5 else ":")
    tr = ccrs.PlateCarree()
    for b, col in BAND_COL.items():
        d = D[D.band == b]
        ax.scatter(d.lon, d.lat, s=22, marker="^", facecolor=[col if f >= 0.5 else "white" for f in d.frac_reference],
                   edgecolor=col, lw=0.9, transform=tr, zorder=3)
        c = P[(P.band == b) & P.scored]
        ax.scatter(c.lon, c.lat, s=18, marker="o", facecolor=[col if r else "white" for r in c.ref],
                   edgecolor=col, lw=0.9, transform=tr, zorder=3)
    x = P[~P.scored]
    ax.scatter(x.lon, x.lat, s=26, marker="x", color="#555555", lw=0.9, transform=tr, zorder=4)
    h = [Line2D([], [], marker="^", ls="", mfc="#666666", mec="#666666", ms=5,
                label=f"discovery, {len(D)} cities scored"),
         Line2D([], [], marker="o", ls="", mfc="#666666", mec="#666666", ms=5,
                label=f"confirmation, {int(P.scored.sum())} of {len(P)} scored"),
         Line2D([], [], marker="x", ls="", color="#555555", ms=5, label="confirmation, excluded by rule"),
         Line2D([], [], marker="o", ls="", mfc="white", mec="#666666", ms=5, label="open: mainly low-cost sensors")]
    h += [Line2D([], [], marker="s", ls="", color=c, ms=5,
                 label=f"{b.replace('_', ' ')} ({int((D.band == b).sum())} + {int(((P.band == b) & P.scored).sum())})")
          for b, c in BAND_COL.items()]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=4, fontsize=6.8, frameon=False)
    save(fig, "fig2_panels")


# ── Fig. 1 ─────────────────────────────────────────────────────────────────────────────────────
def fig1() -> None:
    import pandas as pd
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    n_disc = len(pd.read_csv(LV2 / "maiac_s21_b5_crossfit_c18_grid_dv2_percity_reconstruction.csv", index_col=0))
    P = pd.read_csv(SC / "confirmation" / "confirmation_panel.csv")
    n_conf = len(pd.read_csv(LV2 / "confirm_REGISTERED_percity_reconstruction.csv", index_col=0))
    fig, ax = plt.subplots(figsize=(WIDTH, 3.7))
    ax.set_xlim(-1, 101); ax.set_ylim(0, 55); ax.axis("off")

    def box(x, y, w, h, text, fc, ec="#333333", fs=7.5, bold_first=True):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=0.8))
        lines = text.split("\n")
        ax.text(x + w / 2, y + h / 2, "\n".join(lines), ha="center", va="center", fontsize=fs, linespacing=1.25,
                fontweight="normal")

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9, lw=0.9, color="#333333"))

    # (a) the ladder
    ax.text(0, 53.5, "(a) the declared ladder, for one city and one random split of its stations", fontsize=8.5)
    rungs = [("Bud0  no local sensors", "weather, static geography,\nsatellite aerosol;\nboosted trees, city left out", "#F2F2F2"),
             ("Bud1  + first two stations", "Bud0 recalibrated\nto two local stations", "#DCEAF6"),
             ("Bud2  + stations 3–6", "recalibrated to\nsix local stations", "#C3DBEF"),
             ("Bud3  + background", "daily 10th percentile of\nthe remaining stations", "#A7C9E6")]
    w, gap, y0 = 21.5, 4.2, 33
    for i, (t, sub, fc) in enumerate(rungs):
        x = 1 + i * (w + gap)
        box(x, y0, w, 15, t + "\n\n" + sub, fc, fs=6.9)
        if i:
            arrow(x - gap + 0.4, y0 + 7.5, x - 0.4, y0 + 7.5)
    box(1, 23.5, 97.5, 5.5, "held-out stations, never used by any rung, score every rung: gain = % reduction in daily RMSE,\n"
        "averaged over 21 station splits × 5 learner seeds, then a two-level cluster bootstrap over cities", "#FFF4E0",
        fs=6.9)
    for i in range(4):
        arrow(1 + i * (w + gap) + w / 2, y0 - 0.6, 1 + i * (w + gap) + w / 2, 29.6)

    # (b) the design
    ax.text(0, 18.5, "(b) the study design", fontsize=8.5)
    steps = [(f"discovery\n{n_disc} cities scored\n(develop, check)", "#F2F2F2"),
             ("estimator frozen\nby hash; endpoints\nregistered (OSF)", "#E8E8E8"),
             (f"confirmation, once\n{n_conf} of {len(P)} fresh cities\n(OSF ueyfr)", "#D9EAD3"),
             ("robustness, once each:\nbaseline, learner,\nstation cap\n(b379r, jea58, mhgna)", "#D9EAD3")]
    w2, gap2, y1 = 21.5, 4.2, 1.5
    for i, (t, fc) in enumerate(steps):
        x = 1 + i * (w2 + gap2)
        box(x, y1, w2, 14, t, fc, fs=6.9)
        if i:
            arrow(x - gap2 + 0.4, y1 + 7, x - 0.4, y1 + 7)
    save(fig, "fig1_design")


# ── Fig. 3b (review F.124): like for like ─────────────────────────────────────────────────────────
def fig3b() -> None:
    S = load(LV2 / "review_registered_loco_summary.json")
    reg = S["reconstruction.union.registered_samecities"]
    sym = S["reconstruction.union.symmetric"]
    pro = S["prospective.union.symmetric"]
    rows = [  # label, (block, key), colour, marker, filled
        ("first two, recalibration only (registered H1)", reg["first2_rmse"], "#999999", "s", True),
        ("background, read on the day (registered H3)", reg["bg_rmse"], "#999999", "D", True),
        ("first two, read on the day", sym["gL2s_rmse"], "#000000", "o", True),
        ("background as registered, read on the day", sym["gBGall_rmse"], "#0072B2", "o", True),
        ("background from two outer stations", sym["gBG2_rmse"], "#E69F00", "o", True),
        ("mean of two outer stations", sym["gM2_rmse"], "#009E73", "o", True),
    ]
    diffs = [("background − first two, both on the day", sym["BGallmL2s_rmse"], pro["BGallmL2s_rmse"]),
             ("background (two stations) − first two", sym["BG2mL2s_rmse"], pro["BG2mL2s_rmse"]),
             ("mean of two outer − first two", sym["M2mL2s_rmse"], pro["M2mL2s_rmse"]),
             ("background − first two, exceedance loss", sym["BGallmL2s_exceed"], pro["BGallmL2s_exceed"])]
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDTH, 3.0), gridspec_kw={"width_ratios": [1.25, 1]})
    n = len(rows)
    for i, (lab, e, col, mk, f) in enumerate(rows):
        y = n - 1 - i
        a.plot(e["cluster"], [y, y], color=col, lw=1.2)
        a.plot(e["median"], y, marker=mk, color=col, ms=5, mfc=col if f else "white")
        a.text(e["cluster"][1] + 1.5, y, f"{e['median']:+.1f}", va="center", fontsize=7.5)
    a.axhline(n - 2.5, color="#BBBBBB", lw=0.6, ls="--")
    a.set_yticks(range(n)); a.set_yticklabels([r[0] for r in rows][::-1], fontsize=7.5)
    a.set_xlim(0, 85); a.set_xlabel("% reduction in daily RMSE over the free estimate")
    a.set_title(f"(a) gains, {sym['gL2s_rmse']['n']} cities (grey: registered construction)", fontsize=8, loc="left")
    m = len(diffs)
    for i, (lab, e, p) in enumerate(diffs):
        y = m - 1 - i
        b.plot(e["cluster"], [y + 0.12] * 2, color="#000000", lw=1.2)
        b.plot(e["median"], y + 0.12, "o", color="#000000", ms=4.5)
        b.plot(p["cluster"], [y - 0.12] * 2, color="#0072B2", lw=1.2)
        b.plot(p["median"], y - 0.12, "o", color="#0072B2", ms=4.5, mfc="white")
    b.axvline(0, color="#555555", lw=0.8)
    b.axvspan(-1, 1, color="#EEEEEE", zorder=0)
    b.set_yticks(range(m)); b.set_yticklabels([d[0] for d in diffs][::-1], fontsize=7.5)
    b.set_xlabel("paired difference, points of gain")
    b.set_title("(b) same-day arms, paired", fontsize=9, loc="left")
    b.legend(handles=[Line2D([], [], color="#000000", marker="o", lw=1.2, label="reconstruction"),
                      Line2D([], [], color="#0072B2", marker="o", mfc="white", lw=1.2, label="prospective")],
             fontsize=7, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.07), ncol=2)
    fig.tight_layout()
    save(fig, "fig3b_like_for_like")


# ── Fig. 7b (review F.124): how much of the spatial curve is noise ───────────────────────────────
def fig7b() -> None:
    import numpy as np
    import pandas as pd
    d = SC / "spatial_curve_full"
    R = pd.read_csv(d / "analysis" / "reanalysis_city.csv")
    R = R[(R.k == 3) & R.primary].sort_values("d")
    sb = load(d / "analysis" / "satellite_benchmark.json")
    rn = load(d / "analysis" / "reanalysis.json")
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDTH, 3.2), gridspec_kw={"width_ratios": [1.3, 1]})
    se = np.sqrt(R["var"].to_numpy())
    for i, (dz, s, band) in enumerate(zip(R.d, se, R.band)):
        col = "#D55E00" if band in TROP else "#000000"
        a.plot([dz - 1.96 * s, dz + 1.96 * s], [i, i], color=col, lw=0.9)
        a.plot(dz, i, "o", color=col, ms=3)
    a.axvline(0, color="#555555", lw=0.8)
    a.set_yticks([]); a.set_xlabel("kriging − built-up raster at 3 stations (Fisher z)")
    h = rn["S3_heterogeneity_by_k"]["3"]
    a.set_title(f"(a) cities, k = 3: heterogeneity p = {h['p_Q']:.2f}; "
                f"{rn['S4_holm_crossover']['crossing']}/{rn['S4_holm_crossover']['cities']} cross (Holm)",
                fontsize=8, loc="left")
    a.legend(handles=[Line2D([], [], color="#000000", marker="o", label="non-tropical"),
                      Line2D([], [], color="#D55E00", marker="o", label="tropical")], fontsize=7,
             frameon=False, loc="lower right")
    items = [("GHAP satellite surface", sb["GHAP"]), ("built-up raster (E1)", sb["E1"]),
             ("GHAP − raster", sb["GHAP_minus_E1"]), ("kriging k=3 − GHAP", sb["E3k3_minus_GHAP"]),
             ("kriging k=5 − GHAP", sb["E3k5_minus_GHAP"]), ("kriging k=8 − GHAP", sb["E3k8_minus_GHAP"])]
    for i, (lab, e) in enumerate(items):
        y = len(items) - 1 - i
        b.plot([e["lo"], e["hi"]], [y, y], color="#0072B2", lw=1.2)
        b.plot(e["median"], y, "o", color="#0072B2", ms=4.5)
    b.axvline(0, color="#555555", lw=0.8)
    b.set_yticks(range(len(items))); b.set_yticklabels([x[0] for x in items][::-1], fontsize=7.5)
    b.set_xlabel("rank correlation / paired difference")
    b.set_title(f"(b) free surfaces, {sb['cities']} cities", fontsize=9, loc="left")
    fig.tight_layout()
    save(fig, "fig7b_spatial_noise")


FIGS = {"1": fig1, "2": fig2, "3": fig3, "3b": fig3b, "4": fig4, "5": fig5, "6": fig6, "7": fig7,
        "7b": fig7b, "8": fig8, "9": fig9}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--figs", default=",".join(FIGS))
    for f in ap.parse_args().figs.split(","):
        FIGS[f.strip()]()
