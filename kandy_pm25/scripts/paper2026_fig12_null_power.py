"""Figure 12: what the spatial null tests could actually have detected.

A null result is only as strong as the effect the test could have found. The earth-observation
embedding test is the one spatial null for which a power calculation was carried out, and it
shows the nulls exclude only large residual correlations. That is a weaker and more honest
statement than "no spatial signal exists", and it is the statement the paper makes.

The other spatial nulls are described in the text rather than plotted, because their effect
sizes and detection limits were not retained as artifacts. Plotting them from memory would
reintroduce exactly the drift that the numbers ledger exists to remove.

Reads results/figures/multicity/reviewer_response_stats.json.

Output: results/figures/paper2026/F12_null_power.{png,pdf}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.stage1_satml.decomp import pubfig  # noqa: E402

SRC = ROOT / "results" / "figures" / "multicity" / "reviewer_response_stats.json"
OUT = ROOT / "results" / "figures" / "paper2026"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1a1a1a"
MEASURED = "#4d4d4d"
UNDETECTABLE = "#e8e8e8"
DETECTABLE = "#b2182b"
GOOD = "#2166ac"

PRETTY_CITY = {"Medellin": "Medellín"}


def main() -> None:
    d = json.loads(SRC.read_text())
    rows = d["embedding_power"]
    rows = sorted(rows, key=lambda r: r["min_detectable_r"])

    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    y = np.arange(len(rows))[::-1]

    for yi, r in zip(y, rows):
        mdr = r["min_detectable_r"]
        # the band the test was blind to
        ax.barh(yi, mdr, left=0.0, height=0.44, color=UNDETECTABLE,
                edgecolor="white", linewidth=0.8, zorder=2)
        # the band it could have found, and did not
        ax.barh(yi, 1.0 - mdr, left=mdr, height=0.44, color=DETECTABLE, alpha=0.30,
                edgecolor="white", linewidth=0.8, zorder=2)
        ax.plot([mdr, mdr], [yi - 0.24, yi + 0.24], color=DETECTABLE, lw=1.4, zorder=4)

        ax.scatter([abs(r["partial_rho"])], [yi], s=42, color=MEASURED, zorder=5,
                   edgecolor="white", linewidth=0.7)
        ax.text(abs(r["partial_rho"]), yi + 0.30, f"{r['partial_rho']:+.3f}",
                ha="center", fontsize=6.6, color=MEASURED)
        inside = mdr < 0.88          # keep the label on the plot for a high threshold
        ax.text(mdr + (0.012 if inside else -0.012), yi - 0.02,
                f"detectable above {mdr:.2f}", va="center",
                ha="left" if inside else "right",
                fontsize=6.6, color=DETECTABLE)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{PRETTY_CITY.get(r['city'], r['city'])}  (n = {r['n']})"
                        for r in rows])
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.62, len(rows) - 0.38)
    ax.set_xlabel("absolute residual partial correlation")
    ax.set_title("what the earth-observation embedding null could have detected, at 80% power",
                 loc="left")
    ax.tick_params(axis="y", length=0, right=False, which="both")
    ax.tick_params(axis="x", top=False, which="both")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)

    handles = [Patch(facecolor=UNDETECTABLE, label="the test was blind to this range"),
               Patch(facecolor=DETECTABLE, alpha=0.30,
                     label="the test could have found this, and did not"),
               plt.Line2D([], [], marker="o", ls="none", color=MEASURED, ms=5,
                          markeredgecolor="white", label="measured")]
    ax.legend(handles=handles, loc="upper center", ncol=3, fontsize=6.6,
              bbox_to_anchor=(0.5, -0.30), borderaxespad=0.0)

    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"F12_null_power.{ext}")
    plt.close(fig)

    print(f"wrote F12_null_power.png and .pdf to {OUT}")
    for r in rows:
        print(f"  {r['city']:<12} n={r['n']:>3}  measured {r['partial_rho']:+.3f} "
              f"(p {r['p']:.2f})  detectable above {r['min_detectable_r']:.2f}")
    print("\n  " + d["embedding_power_verdict"][:110])


if __name__ == "__main__":
    main()
