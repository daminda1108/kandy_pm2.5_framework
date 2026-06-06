"""
figure_additive_decomp.py — the additive Lenschow decomposition + the regional-vs-local
partition (2026-06-05). The headline contribution of the additive reframe:

    PM(x,y,t) = B(t) [uniform regional/transboundary background]
              + [T(t)-B(t)]*P_local(x,y,t) [local increment, spatially structured]

Panels:
  (a) uniform background B  — the transboundary/regional floor added to every pixel
  (b) local increment map   — (PM_add - B), the locally-emitted add-on in µg m⁻³
                              (where local traffic/terrain raise PM above background)
  (c) total additive headline (cividis, WHO scale)
  (d) regional-vs-local PARTITION — stacked bars per year (B background + I increment
      = basin mean); ~75% regional / ~25% local => only the local quarter is locally
      actionable. The single most important policy figure.

Out: results/figures/final_model_suite/figX8_additive_decomposition.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import zoom

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.figures_pub import _draw, _scale_bar, _north_arrow, LANDMARKS

DEC = REPO / "data" / "processed" / "decomp"
from src.stage1_satml.decomp.pubfig import PUB_OUT as OUT  # publication style + folder
OUT.mkdir(parents=True, exist_ok=True)
CMAP, VMN, VMX = "cividis", 12, 30
WHO_T = [15, 20, 25, 30]; WHO_L = ["15 IT-3", "20", "25 IT-2", "30"]
CEN = (7.2906, 80.6337)
YEARS = list(range(2019, 2024))


def _grid(df, col, lats, lons):
    return df.groupby(["lat", "lon"])[col].mean().unstack("lon").reindex(
        index=lats, columns=lons).values


def main(year=2023):
    add = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_additive.parquet",
                          columns=["time", "lat", "lon", "pm25_q50"])
    b = pd.read_parquet(DEC / f"B_background_hourly_{year}.parquet")
    b["time"] = pd.to_datetime(b["datetime_utc"])
    add["time"] = pd.to_datetime(add["time"])
    add["B"] = add["time"].map(b.set_index("time")["B"])
    add["incr"] = add["pm25_q50"] - add["B"]                 # local add-on, µg m⁻³
    lats = np.sort(add.lat.unique()); lons = np.sort(add.lon.unique())
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    Ztot = _grid(add, "pm25_q50", lats, lons)
    Zinc = _grid(add, "incr", lats, lons)
    Bann = float(add["B"].mean())

    # per-year partition (background + increment = basin)
    part = []
    for y in YEARS:
        a = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive.parquet",
                            columns=["pm25_q50"])
        bb = pd.read_parquet(DEC / f"B_background_hourly_{y}.parquet")["B"].mean()
        basin = float(a["pm25_q50"].mean())
        part.append(dict(year=y, B=float(bb), I=basin - float(bb), basin=basin,
                         local_pct=(basin - float(bb)) / basin * 100))
    pf = pd.DataFrame(part)
    pf.to_csv(DEC / "additive_partition.csv", index=False)

    fig = plt.figure(figsize=(18, 5.2), constrained_layout=True)
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.05])
    # (a) uniform background
    axa = fig.add_subplot(gs[0, 0])
    Bfield = np.full_like(Ztot, Bann)
    im = axa.imshow(Bfield, origin="lower", extent=ext, cmap=CMAP, vmin=VMN, vmax=VMX, aspect="auto")
    axa.set_title(f"(a) regional background $B$\n(uniform, {Bann:.1f} µg m⁻³ — transboundary)", fontsize=9)
    # (b) local increment
    axb = fig.add_subplot(gs[0, 1])
    imb = axb.imshow(zoom(Zinc, 8, order=3), origin="lower", extent=ext, cmap="YlOrRd",
                     aspect="auto", interpolation="bilinear", vmin=0, vmax=np.percentile(Zinc, 99))
    axb.set_title("(b) local increment $[T-B]\\,P_{local}$\n(locally-emitted add-on, µg m⁻³)", fontsize=9)
    fig.colorbar(imb, ax=axb, shrink=0.7, label="µg m⁻³")
    # (c) total
    axc = fig.add_subplot(gs[0, 2])
    imc = _draw(axc, Ztot, lats, lons, CMAP, vmin=VMN, vmax=VMX)
    axc.set_title(f"(c) total headline $\\widehat{{PM}}_{{2.5}}$\n(B + increment, {Ztot.mean():.1f} µg m⁻³)", fontsize=9)
    cb = fig.colorbar(imc, ax=axc, shrink=0.7, label="PM₂.₅ (µg m⁻³)", extend="both", ticks=WHO_T)
    cb.ax.set_yticklabels(WHO_L, fontsize=7)
    for a, im_ in [(axa, im)]:
        fig.colorbar(im_, ax=a, shrink=0.7, label="PM₂.₅ (µg m⁻³)", extend="both", ticks=WHO_T).ax.set_yticklabels(WHO_L, fontsize=7)
    for a in (axa, axb, axc):
        a.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        a.set_xticks([]); a.set_yticks([])
    _scale_bar(axa, lats, lons); _north_arrow(axc, lats, lons)
    # (d) partition bars
    axd = fig.add_subplot(gs[0, 3])
    x = pf["year"].astype(str)
    axd.bar(x, pf["B"], color="#6BAED6", label="regional / transboundary background $B$")
    axd.bar(x, pf["I"], bottom=pf["B"], color="#E6550D", label="local increment $T-B$ (actionable)")
    for i, r in pf.iterrows():
        axd.text(i, r["basin"] + 0.3, f"{r['local_pct']:.0f}%\nlocal", ha="center", fontsize=7.5)
    axd.set_ylabel("annual PM₂.₅ (µg m⁻³)")
    axd.set_title(f"(d) regional-vs-local partition\n~{pf['local_pct'].mean():.0f}% local, "
                  f"~{100-pf['local_pct'].mean():.0f}% regional — only the local part is locally actionable\n"
                  f"(fraction held constant; literature-bracketed ~15–40%)", fontsize=8.0)
    axd.legend(fontsize=7.2, loc="lower center"); axd.grid(axis="y", alpha=0.25)
    axd.set_ylim(0, pf["basin"].max() * 1.18)
    fig.suptitle("Additive decomposition: a uniform regional/transboundary background plus a spatially-structured "
                 "local increment — the honest intervention partition\n(local share ~25%, bracketed 15–40%: "
                 "World Bank 2022 South-Asia airsheds >50% transboundary; Seneviratne 2017 Kandy PMF regional-dominated)",
                 fontsize=9.8)
    fig.savefig(OUT / "figX8_additive_decomposition.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(pf.round(1).to_string(index=False))
    print(f"\n  mean local fraction {pf['local_pct'].mean():.0f}% | background {Bann:.1f} | "
          f"basin {pf['basin'].mean():.1f}")
    print(f"Wrote {OUT/'figX8_additive_decomposition.png'} + {DEC/'additive_partition.csv'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
