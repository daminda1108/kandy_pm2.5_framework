"""Figure 11: the shipped interval is correctly scaled and incorrectly centred.

Two panels:

  (a) where the observations fall relative to the interval, before and after removing each
      sensor's own median offset. The failure is one-sided, which a single coverage number
      cannot show;
  (b) coverage by season, with the wet season worst, which is a fourth independent line on
      the wet-season high bias.

Values are read from data/processed/decomp/kandy_interval_coverage.json.

Output: results/figures/paper2026/F11_uncertainty.{png,pdf}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.stage1_satml.decomp import pubfig  # noqa: E402

SRC = ROOT / "data" / "processed" / "decomp" / "kandy_interval_coverage.json"
OUT = ROOT / "results" / "figures" / "paper2026"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1a1a1a"
BELOW = "#b2182b"       # observation under the lower bound
INSIDE = "#4393c3"
ABOVE = "#f4a582"
OUTSIDE = "#c7c7c7"
GOOD = "#2166ac"


def panel_a(ax, d):
    """Where observations fall relative to the interval, before and after re-centring."""
    nominal = d["nominal"]
    c = d["centring"]

    after_in = c["coverage_offset_removed"]
    # The artifact reports the below and above split only for the shipped interval. It does
    # not report how the residual 7.8 per cent divides after re-centring, so that row shows a
    # single undifferentiated outside block rather than an invented split.
    rows = [
        ("as shipped", [(c["miss_below"], BELOW), (d["pooled_coverage"], INSIDE),
                        (c["miss_above"], ABOVE)]),
        ("offset removed", [(after_in, INSIDE), (1.0 - after_in, OUTSIDE)]),
    ]
    y = [1, 0]
    for yi, (_, parts) in zip(y, rows):
        left = 0.0
        for val, col in parts:
            ax.barh(yi, val, left=left, height=0.42, color=col,
                    edgecolor="white", linewidth=0.8, zorder=3)
            if val > 0.06:
                ax.text(left + val / 2, yi, f"{100 * val:.1f}%", ha="center", va="center",
                        fontsize=7.0, color="white" if col is not ABOVE else INK)
            left += val

    ax.axvline(1.0 - nominal, color=INK, lw=0.8, ls=(0, (4, 2)), zorder=4)
    ax.text(1.0 - nominal, 1.52, "10% expected outside", ha="center", fontsize=6.5,
            color=INK)

    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.42, 1.55)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("share of the 19,585 sensor-hours")
    ax.set_title("(a)  the failure is one-sided, so the width is not the problem", loc="left")
    ax.tick_params(axis="y", length=0, right=False, which="both")
    ax.tick_params(axis="x", top=False, which="both")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)

    handles = [Patch(facecolor=BELOW, label="below the lower bound"),
               Patch(facecolor=INSIDE, label="inside the interval"),
               Patch(facecolor=ABOVE, label="above the upper bound"),
               Patch(facecolor=OUTSIDE, label="outside, split not reported")]
    ax.legend(handles=handles, loc="upper center", ncol=2, fontsize=6.4,
              bbox_to_anchor=(0.5, -0.20), borderaxespad=0.0)

    ax.text(0.995, 1.60, f"median offset +{c['median_offset_ug']:.2f} µg m$^{{-3}}$",
            ha="right", va="top", fontsize=6.8, color=INK)


def panel_b(ax, d):
    """Coverage by season against the nominal level."""
    order = ["DJF", "MAM", "JJA", "SON"]
    vals = [d["by_season"][s] for s in order]
    x = np.arange(len(order))

    cols = [GOOD if v >= 0.70 else BELOW for v in vals]
    ax.bar(x, vals, width=0.62, color=cols, zorder=3)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.012, f"{v:.3f}", ha="center", fontsize=6.8)

    ax.axhline(d["nominal"], color=INK, lw=0.9, ls=(0, (4, 2)), zorder=4)
    ax.text(len(order) - 0.5, d["nominal"] + 0.012, "nominal 0.90", ha="right",
            fontsize=6.5, color=INK)
    ax.axhline(d["pooled_coverage"], color=NEUTRAL_LINE, lw=0.9, zorder=4)
    ax.text(-0.44, d["pooled_coverage"] + 0.018,
            f"pooled {d['pooled_coverage']:.3f}", ha="left", fontsize=6.5,
            color=NEUTRAL_LINE)

    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("coverage of the 90% interval")
    ax.set_title("(b)  the wet season is worst", loc="left")
    ax.grid(axis="y", zorder=0)
    ax.tick_params(top=False, right=False, which="both")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


NEUTRAL_LINE = "#6e6e6e"


def main() -> None:
    d = json.loads(SRC.read_text())

    fig = plt.figure(figsize=(7.2, 2.7))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.30)
    panel_a(fig.add_subplot(gs[0, 0]), d)
    panel_b(fig.add_subplot(gs[0, 1]), d)

    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"F11_uncertainty.{ext}")
    plt.close(fig)

    c = d["centring"]
    print(f"wrote F11_uncertainty.png and .pdf to {OUT}")
    print(f"  pooled {d['pooled_coverage']:.4f} against {d['nominal']:.2f} nominal")
    print(f"  below {c['miss_below']:.4f}  above {c['miss_above']:.4f}  "
          f"offset +{c['median_offset_ug']:.3f}")
    print(f"  re-centred {c['coverage_offset_removed']:.4f} at the same width")


if __name__ == "__main__":
    main()
