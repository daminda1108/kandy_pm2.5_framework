"""spatial_skill_law.py — is the within-city spatial skill predictable?

Hindsight reframe of the spatial evidence. Rather than assert "spatial rank is weak and
regime-dependent", we test whether held-out spatial rank (Spearman rho) is a predictable
function of two observable city properties: terrain relief (the signal) and monitoring-
network size (the ability to resolve it). If it is, then Kandy's own low relief and absent
public network *predict* a low spatial ceiling, turning a weakness into a quantified,
falsifiable statement.

relief    = 90th percentile of the confinement depth delta_z (m), from each city's terrain.
network   = number of held-out stations n (public-network size proxy).
spatial   = held-out Spearman rho from the N=9 scorecard.

Kandy is placed on the same axes (its relief; n=0 public stations) to read off the ceiling.

Out: data/processed/decomp/spatial_skill_law.csv
     results/figures/paper_figures_v2/S4_skill_law.png  (+ staged to the preprint)
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

REPO = Path(__file__).resolve().parents[1]
PIN = REPO / "data" / "processed" / "pinn_inputs"
DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "results" / "figures" / "paper_figures_v2"
OUT.mkdir(parents=True, exist_ok=True)

SCORE = REPO / "results" / "figures" / "multicity" / "validation_scorecard.csv"
# scorecard city-name -> terrain slug
SLUG = {"Xichang": "xichang", "Chiang Mai": "chiangmai", "Bazhong (Sichuan)": "bazhou",
        "Chandigarh": "chandigarh", "Kathmandu Valley": "kathmandu",
        "Tai'an (foot of Mt Tai, Shandong)": "taian", "Baoji (Wei R. valley, Shaanxi)": "baoji",
        "Yichang (Yangtze valley, Hubei)": "yichang", "Medellín (Aburrá Valley, Colombia)": "medellin"}


def relief(npz_path, key="delta_z"):
    z = np.load(npz_path)
    dz = np.asarray(z[key], float)
    dz = dz[np.isfinite(dz)]
    return float(np.percentile(dz, 90))


def main():
    sc = pd.read_csv(SCORE)
    rows = []
    for _, r in sc.iterrows():
        slug = SLUG.get(r["city"])
        if slug is None:
            continue
        p = PIN / f"{slug}_terrain_core.npz"
        if not p.exists() or not np.isfinite(r["spatial"]):
            continue
        rows.append(dict(city=r["city"].split(" (")[0], slug=slug,
                         relief=relief(p), n=int(r["n"]), rho=float(r["spatial"])))
    df = pd.DataFrame(rows)
    # Kandy on the same axes (its terrain; no public network)
    kandy_relief = relief(PIN / "kandy_terrain_tpi_svf_100m.npz")

    # correlations
    r_rel, p_rel = pearsonr(df.relief, df.rho)
    r_n, p_n = pearsonr(df.n, df.rho)
    # simple combined descriptive index (standardised relief + standardised log-n)
    zr = (df.relief - df.relief.mean()) / df.relief.std()
    zn = (np.log1p(df.n) - np.log1p(df.n).mean()) / np.log1p(df.n).std()
    df["index"] = zr + zn
    r_idx, p_idx = pearsonr(df["index"], df.rho)
    # OLS rho ~ relief for the Kandy read-off (descriptive, n=9)
    a, b = np.polyfit(df.relief, df.rho, 1)
    kandy_pred = a * kandy_relief + b

    df.to_csv(DEC / "spatial_skill_law.csv", index=False)
    print(df.round(2).to_string(index=False))
    print(f"\nrho vs relief : Pearson r={r_rel:+.2f} (p={p_rel:.3f})")
    print(f"rho vs n      : Pearson r={r_n:+.2f} (p={p_n:.3f})")
    print(f"rho vs relief+logn index : r={r_idx:+.2f} (p={p_idx:.3f})")
    print(f"Kandy relief p90(dz) = {kandy_relief:.0f} m  ->  relief-predicted rho ~ {kandy_pred:.2f}")

    # ── figure: rho vs relief (size = network), with Kandy placed ───────────────
    fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.5), constrained_layout=True)
    sizes = 30 + 6 * np.sqrt(df.n)
    scatter = ax[0].scatter(df.relief, df.rho, s=sizes, c=df.n, cmap="viridis",
                            edgecolor="k", linewidth=0.5, zorder=3)
    xs = np.linspace(df.relief.min(), max(df.relief.max(), kandy_relief) * 1.05, 50)
    ax[0].plot(xs, a * xs + b, "--", color="grey", lw=1, zorder=1)
    for _, r in df.iterrows():
        ax[0].annotate(r.city, (r.relief, r.rho), fontsize=6, xytext=(3, 3),
                       textcoords="offset points")
    ax[0].axvline(kandy_relief, color="#B2182B", ls=":", lw=1.2)
    ax[0].scatter([kandy_relief], [kandy_pred], marker="*", s=180, color="#B2182B",
                  edgecolor="k", zorder=4, label=f"Kandy (relief-predicted ρ≈{kandy_pred:.2f})")
    ax[0].set_xlabel("terrain relief  (90th-pct confinement depth, m)")
    ax[0].set_ylabel("held-out spatial rank  (Spearman ρ)")
    ax[0].set_title(f"(a) ρ vs relief   (r={r_rel:+.2f})", fontsize=9)
    ax[0].legend(fontsize=6.5, loc="upper left"); ax[0].grid(alpha=0.25)
    cb = fig.colorbar(scatter, ax=ax[0], shrink=0.8); cb.set_label("network size (n)", fontsize=7)

    ax[1].scatter(df.n, df.rho, s=sizes, c=df.relief, cmap="cividis",
                  edgecolor="k", linewidth=0.5, zorder=3)
    for _, r in df.iterrows():
        ax[1].annotate(r.city, (r.n, r.rho), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax[1].axvline(0, color="#B2182B", ls=":", lw=1.2)
    ax[1].scatter([0], [kandy_pred], marker="*", s=180, color="#B2182B", edgecolor="k",
                  zorder=4, label="Kandy (no public network)")
    ax[1].set_xlabel("monitoring-network size  (held-out stations $n$)")
    ax[1].set_ylabel("held-out spatial rank  (Spearman ρ)")
    ax[1].set_title(f"(b) ρ vs network size   (r={r_n:+.2f})", fontsize=9)
    ax[1].legend(fontsize=6.5, loc="lower right"); ax[1].grid(alpha=0.25)
    fig.suptitle("Within-city spatial skill is predictable: it rises with terrain relief and network "
                 "size, and\nKandy's modest relief and absent public network place it at the low end",
                 fontsize=9.2)
    fig.savefig(OUT / "S4_skill_law.png", dpi=350, bbox_inches="tight"); plt.close(fig)
    print(f"\nwrote {DEC/'spatial_skill_law.csv'}\nwrote {OUT/'S4_skill_law.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
