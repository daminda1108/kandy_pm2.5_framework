"""Figure 7: the ten-city scorecard.

Four quantities scored separately, because they fail independently. Temporal structure and
level transfer across every city; fine spatial rank does not.

SOURCE DISCIPLINE. The spatial column is read from spatial_significance_test.csv, the
per-hour network-mean-removal estimator with a per-city permutation null. It is NOT read from
the `spatial` column of validation_scorecard.csv, which is the superseded paired-hours
estimator; the two disagree substantially and by sign in places. See NUMBERS_LEDGER.md D5.

Output: results/figures/paper2026/F7_scorecard.{png,pdf}
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.stage1_satml.decomp import pubfig  # noqa: E402

MC = ROOT / "results" / "figures" / "multicity"
OUT = ROOT / "results" / "figures" / "paper2026"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1a1a1a"
PASS = "#2166ac"
FAIL = "#b2182b"
MUTED = "#9e9e9e"
BAND = "#eef3f8"


def load() -> pd.DataFrame:
    sc = pd.read_csv(MC / "validation_scorecard.csv")
    sc["key"] = sc["city"].str.split(" (", regex=False).str[0].str.strip()

    sig = pd.read_csv(MC / "spatial_significance_test.csv")
    sig["key"] = sig["city"].str.strip()

    df = sc.merge(sig[["key", "e1", "p", "null95"]], on="key", how="left")
    if df["e1"].notna().sum() != 9:
        raise RuntimeError(f"expected 9 estimable spatial ranks, got {df['e1'].notna().sum()}")
    df["short"] = df["key"].replace({"Kathmandu Valley": "Kathmandu",
                                     "Bazhong (Sichuan)": "Bazhong"})
    return df.sort_values("e1", ascending=True, na_position="first").reset_index(drop=True)


def _rows(ax, df):
    ax.set_ylim(-0.7, len(df) - 0.3)
    ax.set_yticks(range(len(df)))
    ax.tick_params(axis="y", length=0, right=False, which="both")
    ax.tick_params(axis="x", top=False, which="both")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    for yi in range(len(df)):
        if yi % 2 == 0:
            ax.axhspan(yi - 0.5, yi + 0.5, color="#fafafa", zorder=0)


def panel_corr(ax, df, col, title, lo):
    y = np.arange(len(df))
    ax.hlines(y, lo, df[col], color=MUTED, lw=0.7, zorder=2)
    good = df[col] >= 0.6
    ax.scatter(df[col][good], y[good], s=26, color=PASS, zorder=3,
               edgecolor="white", linewidth=0.5)
    ax.scatter(df[col][~good], y[~good], s=26, color=FAIL, zorder=3,
               edgecolor="white", linewidth=0.5)
    ax.set_xlim(lo, 1.02)
    ax.set_title(title, loc="left", fontsize=8.0)
    _rows(ax, df)
    ax.set_yticklabels([])


def panel_level(ax, df):
    y = np.arange(len(df))
    ax.axvspan(-10, 10, color=BAND, zorder=1)
    ax.axvline(0, color=MUTED, lw=0.7, zorder=2)
    v = df["level"]
    ax.hlines(y, 0, v, color=MUTED, lw=0.7, zorder=2)
    ok = v.abs() <= 15
    ax.scatter(v[ok], y[ok], s=26, color=PASS, zorder=3, edgecolor="white", linewidth=0.5)
    ax.scatter(v[~ok], y[~ok], s=26, color=FAIL, zorder=3, edgecolor="white", linewidth=0.5)
    ax.set_xlim(-12, 34)
    ax.set_title("(c)  level bias (%)", loc="left", fontsize=8.0)
    _rows(ax, df)
    ax.set_yticklabels([])
    ax.text(10, len(df) - 0.30, "within 10%", fontsize=6.2, color=MUTED, ha="right")


def panel_spatial(ax, df):
    y = np.arange(len(df))
    for yi, r in zip(y, df.itertuples()):
        if np.isnan(r.e1):
            ax.text(0.02, yi, "not estimable, no usable station pairs",
                    fontsize=6.4, va="center", color=MUTED, style="italic")
            continue
        sig = r.p < 0.05
        ax.hlines(yi, 0, r.e1, color=MUTED, lw=0.7, zorder=2)
        # the city's own permutation null, which is what significance is judged against
        ax.plot([r.null95, r.null95], [yi - 0.28, yi + 0.28], color=INK, lw=1.0,
                zorder=4)
        ax.scatter([r.e1], [yi], s=30, color=PASS if sig else FAIL, zorder=5,
                   edgecolor="white", linewidth=0.5)
        ax.text(max(r.e1, r.null95) + 0.03, yi, f"p {r.p:.3f}", fontsize=6.2,
                va="center", color=PASS if sig else FAIL)

    ax.set_xlim(0, 1.18)
    ax.set_title("(d)  fine spatial rank, against each city's own null", loc="left",
                 fontsize=8.0)
    _rows(ax, df)
    ax.set_yticklabels([])


def main() -> None:
    df = load()

    fig = plt.figure(figsize=(7.2, 4.0))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.0, 1.0, 1.0, 1.5], wspace=0.13)

    ax0 = fig.add_subplot(gs[0])
    panel_corr(ax0, df, "seasonal", "(a)  seasonal $r$", 0.90)
    ax0.set_yticklabels(df["short"], fontsize=7.2)

    panel_corr(fig.add_subplot(gs[1]), df, "diurnal", "(b)  diurnal $r$", -0.45)
    panel_level(fig.add_subplot(gs[2]), df)
    ax3 = fig.add_subplot(gs[3])
    panel_spatial(ax3, df)

    handles = [Line2D([], [], marker="o", ls="none", color=PASS, ms=5,
                      markeredgecolor="white", label="passes"),
               Line2D([], [], marker="o", ls="none", color=FAIL, ms=5,
                      markeredgecolor="white", label="does not"),
               Line2D([], [], color=INK, lw=1.0, label="95th percentile of the null")]
    ax3.legend(handles=handles, loc="upper center", ncol=3, fontsize=6.5,
               bbox_to_anchor=(-0.32, -0.06), borderaxespad=0.0)

    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"F7_scorecard.{ext}")
    plt.close(fig)

    n_sig = int((df["p"] < 0.05).sum())
    n_est = int(df["e1"].notna().sum())
    print(f"wrote F7_scorecard.png and .pdf to {OUT}")
    print(f"  seasonal r  {df.seasonal.min():.3f} to {df.seasonal.max():.3f}")
    print(f"  diurnal r   {df.diurnal.min():.3f} to {df.diurnal.max():.3f}")
    print(f"  level bias  {df.level.min():+.1f}% to {df.level.max():+.1f}%, "
          f"median {df.level.median():+.1f}%")
    print(f"  spatial     {n_sig} of {n_est} estimable significant at p < 0.05")


if __name__ == "__main__":
    main()
