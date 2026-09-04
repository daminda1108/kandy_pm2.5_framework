"""Figure 3: the information bound.

Three panels, each a measurement rather than an illustration:

  (a) the rigid ansatz, showing where each bounded parameter came to rest inside its
      admissible range, with the literature range marked for the two that saturated;
  (b) the neural process, showing point accuracy rising while interval coverage falls;
  (c) the two-sensor fine tuning, showing the delivered field keyed to sensor position.

All values are read from data/processed/decomp/model_progression.json so the figure cannot
drift from the ledger.

Output: results/figures/paper2026/F3_information_bound.{png,pdf}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.stage1_satml.decomp import pubfig  # noqa: E402  (applies the style on import)

SRC = ROOT / "data" / "processed" / "decomp" / "model_progression.json"
OUT = ROOT / "results" / "figures" / "paper2026"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1a1a1a"
ACCENT = "#b2182b"      # the failure being diagnosed
NEUTRAL = "#4d4d4d"
LIGHT = "#bdbdbd"
GOOD = "#2166ac"

PRETTY = {"H_trap_m": "trapping depth", "alpha_valley": "valley amplification",
          "BLH_ref_m": "reference BLH", "u_ref_ms": "reference wind speed"}
# NOTE. An earlier version overlaid a "literature range" band on two parameters, taken from
# a source-code comment citing "Chemel 2015" for a valley amplification of 1.5 to 3. That
# attribution could not be verified against the paper (Chemel et al. 2016 concerns valley heat
# deficit and does not supply that range), so the band was removed. The identifiability finding
# does not need it: the admissible ranges were set as physically plausible bounds when the model
# was written, and the fit went to the extreme low end of two of them.


def panel_a(ax, d):
    """Where each bounded ansatz parameter came to rest inside its admissible range."""
    params = [p for p in PRETTY if p in d["parameters"]]
    y = np.arange(len(params))[::-1]

    for yi, name in zip(y, params):
        info = d["parameters"][name]
        lo, hi = info["bounds"]
        pos = info["position_in_range"]
        saturated = info["on_lower_bound"]

        ax.plot([0, 1], [yi, yi], color=LIGHT, lw=1.2, solid_capstyle="round", zorder=1)

        ax.scatter([pos], [yi], s=34, zorder=3, clip_on=False,
                   color=ACCENT if saturated else NEUTRAL,
                   marker="o" if saturated else "s",
                   edgecolor="white", linewidth=0.6)

    ax.set_yticks(y)
    ax.set_yticklabels([PRETTY[p] for p in params])
    ax.set_xlim(-0.04, 1.04)
    ax.set_ylim(-0.7, len(params) - 0.4)
    ax.set_xticks([0, 0.5, 1])
    ax.set_xticklabels(["lower bound", "mid-range", "upper bound"])
    ax.set_title("(a)  rigid ansatz: two parameters pinned at the low extreme of their range",
                 loc="left")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0, right=False, which="both")
    ax.tick_params(axis="x", top=False, which="both")

    ax.scatter([], [], s=30, color=ACCENT, edgecolor="white", linewidth=0.6,
               label="on its bound")
    ax.scatter([], [], s=30, marker="s", color=NEUTRAL, edgecolor="white", linewidth=0.6,
               label="interior")
    ax.legend(loc="upper right", ncol=2, fontsize=6.6,
              bbox_to_anchor=(1.005, -0.30), borderaxespad=0.0)


CITY_LABEL = {"medellin": "Medellín", "chiangmai": "Chiang Mai",
              "kathmandu": "Kathmandu"}


def panel_b(ax, d):
    """Per city, what changed when the likelihood was made heavier-tailed.

    A grouped bar chart hid the result, because the coverage ranges of the two
    likelihoods overlap. Per-city slopes show it: correlation rises in two cities of
    three while coverage falls in two of three, and both means move the wrong way
    relative to each other.
    """
    v13, v14 = d["v13_gaussian"]["per_city"], d["v14_student_t"]["per_city"]
    cities = [c for c in CITY_LABEL if c in v13 and c in v14]

    ax.axhline(0.90, color=INK, lw=0.8, ls=(0, (4, 2)), zorder=2)
    ax.text(1.02, 0.925, "nominal 0.90", va="bottom", fontsize=6.4, color=INK,
            ha="right")

    for c in cities:
        ax.plot([0, 1], [v13[c]["r"], v14[c]["r"]], color=GOOD, lw=1.0,
                marker="o", ms=3.4, zorder=3)
        ax.plot([0, 1], [v13[c]["coverage90"], v14[c]["coverage90"]], color=ACCENT,
                lw=1.0, marker="o", ms=3.4, zorder=3)
        ax.text(-0.055, v13[c]["r"], CITY_LABEL[c], ha="right", va="center",
                fontsize=6.2, color=GOOD)
        ax.text(-0.055, v13[c]["coverage90"], CITY_LABEL[c], ha="right", va="center",
                fontsize=6.2, color=ACCENT)

    mr13 = np.mean([v13[c]["r"] for c in cities])
    mr14 = np.mean([v14[c]["r"] for c in cities])
    mc13 = np.mean([v13[c]["coverage90"] for c in cities])
    mc14 = np.mean([v14[c]["coverage90"] for c in cities])
    ax.plot([0, 1], [mr13, mr14], color=GOOD, lw=2.4, zorder=4)
    ax.plot([0, 1], [mc13, mc14], color=ACCENT, lw=2.4, zorder=4)
    ax.text(1.03, mr14, f"mean r\n{mr13:.3f} to {mr14:.3f}", va="center",
            fontsize=6.4, color=GOOD)
    ax.text(1.03, mc14 - 0.055, f"mean coverage\n{mc13:.3f} to {mc14:.3f}", va="center",
            fontsize=6.4, color=ACCENT)

    ax.set_xlim(-0.42, 1.62)
    ax.set_ylim(0.20, 1.0)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Gaussian", "Student-t"])
    ax.set_ylabel("correlation and 90% coverage")
    ax.set_title("(b)  neural process: accuracy up, calibration down", loc="left")
    ax.tick_params(top=False, right=False, which="both")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def panel_c(ax, d):
    """Annual mean against distance from the nearest tuning sensor."""
    rows = d["by_distance_km_from_nearest_tuning_sensor"]
    lab = [r["bin"] for r in rows]
    x = np.arange(len(rows))
    zs = [r["zero_shot"] for r in rows]
    ft = [r["fine_tuned"] for r in rows]

    ax.axhspan(17, 25, color=GOOD, alpha=0.10, zorder=0)
    ax.annotate("plausible basin mean", xy=(0.02, 26.0), ha="left",
                fontsize=6.6, color=GOOD)

    ax.plot(x, zs, marker="s", ms=4, color=NEUTRAL, label="zero shot", zorder=3)
    ax.plot(x, ft, marker="o", ms=4.5, color=ACCENT, label="tuned on two sensors", zorder=4)

    ax.annotate(f"{ft[0]:.1f}", xy=(x[0], ft[0]), xytext=(x[0] + 0.12, ft[0] + 2.4),
                fontsize=6.8, color=ACCENT)
    ax.annotate(f"{ft[-1]:.2f}", xy=(x[-1], ft[-1]), xytext=(x[-1] - 0.16, ft[-1] + 3.6),
                ha="right", fontsize=6.8, color=ACCENT)

    ax.set_xticks(x)
    ax.set_xticklabels(lab)
    ax.set_xlabel("distance from the nearest tuning sensor (km)")
    ax.set_ylabel("annual mean PM$_{2.5}$ (µg m$^{-3}$)")
    ax.set_ylim(0, 50)
    ax.set_title("(c)  two sensors: the field keys on sensor position", loc="left")
    ax.legend(loc="lower left", fontsize=6.6)
    ax.grid(axis="y", zorder=0)
    ax.tick_params(top=False, right=False, which="both")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def main() -> None:
    d = json.loads(SRC.read_text())

    fig = plt.figure(figsize=(7.2, 5.0))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.55, 1.45],
                          hspace=0.42, wspace=0.34)
    panel_a(fig.add_subplot(gs[0, :]), d["stage_2_rigid_ansatz"])
    panel_b(fig.add_subplot(gs[1, 0]), d["stage_3_neural_process"])
    panel_c(fig.add_subplot(gs[1, 1]),
            d["stage_4_two_sensor_fine_tuning"]["spatial_signature"])

    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"F3_information_bound.{ext}")
    plt.close(fig)

    print(f"wrote F3_information_bound.png and .pdf to {OUT}")
    an = d["stage_2_rigid_ansatz"]
    print(f"  panel a: {an['n_on_bound']} of 6 on a bound -> {', '.join(an['on_bound'])}")
    print(f"  panel b: r {d['stage_3_neural_process']['v13_gaussian']['mean_r']:.3f} "
          f"to {d['stage_3_neural_process']['v14_student_t']['mean_r']:.3f}")
    sig = d["stage_4_two_sensor_fine_tuning"]["spatial_signature"]
    rows = sig["by_distance_km_from_nearest_tuning_sensor"]
    print(f"  panel c: {rows[0]['fine_tuned']:.1f} near a sensor, "
          f"{rows[-1]['fine_tuned']:.2f} beyond 10 km")


if __name__ == "__main__":
    main()
