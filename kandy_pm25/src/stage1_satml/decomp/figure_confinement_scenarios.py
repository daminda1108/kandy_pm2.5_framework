"""
figure_confinement_scenarios.py — confinement-amplitude scenario suite.

Renders the literature-bracketed confinement range (assume FECT real, user
2026-06-03), using the fast annual-mean approximation
    PM_annual(x,y) ≈ L(year) · S_emit(x,y) · M̄(x,y),   M̄ = exp(κ w̄ c)/<·>
so the basin mean stays L (M̄ has spatial mean 1 → pure redistribution).

Figures (results/figures/kandy_decomp/confinement/):
  scenarios.png        ratio-vs-κ curve + weak/central/strong annual fields
  multiyear.png        2019-2023 annual maps under the central calibrated κ
  day_night.png        day vs night spatial contrast under central κ
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

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
DEC = HERE / "data" / "processed" / "decomp"
GRID = HERE / "data" / "processed" / "stage1_v3"
OUT = HERE / "results" / "figures" / "kandy_decomp" / "confinement"
OUT.mkdir(parents=True, exist_ok=True)

NIFS = (7.2675, 80.5985, 24.5, "^"); HANT = (7.265, 80.625, 10.5, "s")
CITY = (7.2906, 80.6337, None, "o")
H_RIDGE = 300.0; RATIO_OBS = 24.5 / 10.5
LANDMARKS = {"NIFS 24.5": NIFS, "Hantana 10.5": HANT, "city": CITY}


def load():
    cal = np.load(DEC / "M_confinement_calibrated_local.npz")
    c, lats, lons, w_bar = cal["c"], cal["lats"], cal["lons"], float(cal["w_bar"])
    S = np.load(DEC / "S_emit_kandy.npz")["S_emit"]
    L = pd.read_csv(GRID / "vandonkelaar_kandy_annual.csv").set_index("year")["L_corrected"]
    return c, lats, lons, w_bar, S, L


def at(lats, lons, A, la, lo):
    return A[int(np.argmin(np.abs(lats - la))), int(np.argmin(np.abs(lons - lo)))]


def Mbar(c, kappa, w_bar):
    M = np.exp(kappa * w_bar * c); return M / M.mean()


def kappa_for(ratio, w_bar, c, lats, lons, S):
    c_n, c_h = at(lats, lons, c, *NIFS[:2]), at(lats, lons, c, *HANT[:2])
    Sr = at(lats, lons, S, *NIFS[:2]) / at(lats, lons, S, *HANT[:2])
    return float(np.log(ratio / Sr) / (w_bar * (c_n - c_h)))


def _map(ax, F, lats, lons, vmin, vmax, ttl, marks=True):
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax.imshow(zoom(F, 8, order=3), origin="lower", extent=ext, cmap="YlOrRd",
                   vmin=vmin, vmax=vmax, aspect="auto", interpolation="bilinear")
    if marks:
        for nm, (la, lo, v, mk) in LANDMARKS.items():
            ax.plot(lo, la, mk, mfc="cyan", mec="k", mew=0.8, ms=6, zorder=5)
    ax.set_title(ttl, fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    return im


def main():
    c, lats, lons, w_bar, S, L = load()
    Lc = float(L.loc[2019:2023].mean())
    k_weak = kappa_for(1.30, w_bar, c, lats, lons, S)     # literature event-scale lower
    k_cent = kappa_for(1.70, w_bar, c, lats, lons, S)     # central
    k_strong = kappa_for(RATIO_OBS, w_bar, c, lats, lons, S)  # FECT
    print(f"w̄={w_bar:.3f}  κ: weak {k_weak:.2f} / central {k_cent:.2f} / strong {k_strong:.2f}")

    # ── Figure 1: ratio-vs-κ + three annual fields ──
    fig = plt.figure(figsize=(15, 4.8), constrained_layout=True)
    gs = fig.add_gridspec(1, 4)
    axc = fig.add_subplot(gs[0, 0])
    ks = np.linspace(0, 1.8, 120)
    c_n, c_h = at(lats, lons, c, *NIFS[:2]), at(lats, lons, c, *HANT[:2])
    Sr = at(lats, lons, S, *NIFS[:2]) / at(lats, lons, S, *HANT[:2])
    ratios = Sr * np.exp(ks * w_bar * (c_n - c_h))
    axc.plot(ks, ratios, "k-", lw=1.6)
    axc.axhline(RATIO_OBS, color="crimson", ls="--", lw=1.2, label=f"FECT obs {RATIO_OBS:.2f}×")
    axc.axhspan(1.2, 1.5, color="steelblue", alpha=0.18, label="literature CAP (~30%/300 m)")
    axc.plot(0.15 * 1, 1.11, "bo", ms=6)  # current model approx
    axc.annotate("current κ=0.15\n(1.11×)", (0.15, 1.11), fontsize=7, xytext=(0.3, 1.3),
                 arrowprops=dict(arrowstyle="->", lw=0.7))
    for k, lab in [(k_weak, "weak"), (k_cent, "central"), (k_strong, "strong")]:
        axc.axvline(k, color="green", ls=":", lw=0.8); axc.text(k, 0.7, lab, fontsize=6.5,
                    rotation=90, color="green", va="bottom")
    axc.set_xlabel("confinement κ (log form)"); axc.set_ylabel("NIFS/Hantana floor-ridge ratio")
    axc.set_title("(a) Floor-ridge ratio vs κ\n(local FECT pair calibrates κ)", fontsize=9)
    axc.legend(fontsize=6.5, loc="upper left"); axc.set_ylim(0.6, 2.6)

    vmin, vmax = 10, 30
    im = None
    for col, (k, tag) in zip(range(1, 4), [(k_weak, "weak (lit. ~1.3×)"),
                             (k_cent, "central (~1.7×)"), (k_strong, "strong (FECT 2.33×)")]):
        F = Lc * S * Mbar(c, k, w_bar)
        ax = fig.add_subplot(gs[0, col])
        im = _map(ax, F, lats, lons, vmin, vmax,
                  f"({'bcd'[col-1]}) κ={k:.2f}  {tag}\nbasin {F.mean():.1f} "
                  f"(preserved)  core {F.max():.0f}")
    fig.colorbar(im, ax=fig.axes[1:], label="annual PM₂.₅ (µg m⁻³)", extend="both", shrink=0.7)
    fig.suptitle("Confinement-amplitude scenarios (assume FECT real): the current model "
                 "under-traps even vs cold-air-pool literature; the FECT floor-ridge pair "
                 "brackets a much stronger κ — basin mean preserved throughout", fontsize=10)
    fig.savefig(OUT / "scenarios.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # ── Figure 2: per-year 2019-2023 under central κ ──
    fig2, ax2 = plt.subplots(1, 5, figsize=(18, 4.0), constrained_layout=True)
    im = None
    for ax, y in zip(ax2, range(2019, 2024)):
        F = float(L.loc[y]) * S * Mbar(c, k_cent, w_bar)
        im = _map(ax, F, lats, lons, 10, 32, f"{y}   basin {F.mean():.1f} µg m⁻³")
        ax.plot(CITY[1], CITY[0], "o", mfc="cyan", mec="k", mew=0.7, ms=5)
    fig2.colorbar(im, ax=ax2, label="annual PM₂.₅ (µg m⁻³)", extend="both", shrink=0.65)
    fig2.suptitle(f"Kandy 2019–2023 under the central calibrated confinement (κ={k_cent:.2f}) "
                  f"— per-year Van Donkelaar level, core hotspot from emission × trapping",
                  fontsize=10.5)
    fig2.savefig(OUT / "multiyear.png", dpi=200, bbox_inches="tight")
    plt.close(fig2)

    # ── Figure 3: day vs night spatial contrast (central κ) ──
    # day ≈ well-mixed (w→0, M≈1 flat); night ≈ strong trapping (w→1)
    Mday = Mbar(c, k_cent, 0.02); Mnight = Mbar(c, k_cent, 1.0)
    fig3, ax3 = plt.subplots(1, 2, figsize=(10.6, 5.2), constrained_layout=True)
    for ax, M, tag in [(ax3[0], Mday, "day (well-mixed)"), (ax3[1], Mnight, "night (trapped)")]:
        F = Lc * S * M
        im = _map(ax, F, lats, lons, 6, 40,
                  f"{tag}\ncore/ridge {at(lats,lons,F,*NIFS[:2])/at(lats,lons,F,*HANT[:2]):.2f}×")
    fig3.colorbar(im, ax=ax3, label="PM₂.₅ (µg m⁻³)", extend="both", shrink=0.8)
    fig3.suptitle("Diurnal confinement (central κ): near-flat by day, strong floor-ridge "
                  "contrast at night under the shallow boundary layer", fontsize=10)
    fig3.savefig(OUT / "day_night.png", dpi=200, bbox_inches="tight")
    plt.close(fig3)
    for f in ["scenarios", "multiyear", "day_night"]:
        print(f"Wrote {OUT/(f+'.png')}")


if __name__ == "__main__":
    main()
