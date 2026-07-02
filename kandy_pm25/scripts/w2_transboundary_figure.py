"""w2_transboundary_figure.py — the transboundary-context panel for the preprint (§6).
Three panels from the W2 outputs: (a) trajectory-origin composition by season,
(b) reference PM by air-mass origin, (c) the seasonal switch (obs vs background).
Out: docs/reports/fig_preprint/transboundary.png
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
try:
    from src.stage1_satml.decomp import pubfig  # noqa: F401 (style)
except Exception:
    pass

W2 = REPO / "data" / "processed" / "decomp" / "w2"
OUT = REPO / "docs" / "reports" / "fig_preprint"
OUT.mkdir(parents=True, exist_ok=True)

# colours: continental/Indian = warm, marine = cool
COL = {"IGP_E_India": "#a11d33", "BoB_marine": "#d98c3f", "Penin_India": "#c2603a",
       "local_recirc": "#7a7f87", "SW_marine": "#2f6f8f"}
LAB = {"IGP_E_India": "Indo-Gangetic", "BoB_marine": "Bay of Bengal",
       "Penin_India": "Peninsular India", "local_recirc": "local recirc.",
       "SW_marine": "SW marine"}
ORDER = ["IGP_E_India", "BoB_marine", "Penin_India", "local_recirc", "SW_marine"]

traj = pd.read_parquet(W2 / "d1_trajectories_850.parquet")
traj["month"] = pd.to_datetime(traj["date"]).dt.month
sec = pd.read_csv(W2 / "d1_sector_pm_850.csv").set_index("sector")
seas = pd.read_csv(W2 / "d2_seasonal.csv")

fig, ax = plt.subplots(1, 3, figsize=(10.2, 3.1), constrained_layout=True)

# (a) origin composition by season ------------------------------------------------
def comp(months):
    s = traj[traj.month.isin(months)].sector.value_counts(normalize=True)
    return [100 * s.get(k, 0) for k in ORDER]
djf, jja = comp([12, 1, 2]), comp([6, 7, 8])
x = np.arange(2); bottom = np.zeros(2)
for i, k in enumerate(ORDER):
    vals = np.array([djf[i], jja[i]])
    ax[0].bar(x, vals, bottom=bottom, color=COL[k], label=LAB[k], width=0.62,
              edgecolor="white", linewidth=0.6)
    bottom += vals
ax[0].set_xticks(x); ax[0].set_xticklabels(["NE monsoon\n(DJF)", "SW monsoon\n(JJA)"])
ax[0].set_ylabel("trajectory origin (%)"); ax[0].set_ylim(0, 100)
ax[0].set_title("(a) where the air comes from", fontsize=9)
ax[0].legend(fontsize=6.0, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False)

# (b) PM by air-mass origin -------------------------------------------------------
med = [sec.loc[k, "median"] for k in ORDER]
bars = ax[1].bar(range(len(ORDER)), med, color=[COL[k] for k in ORDER],
                 edgecolor="k", linewidth=0.5)
ax[1].set_xticks(range(len(ORDER)))
ax[1].set_xticklabels([LAB[k] for k in ORDER], rotation=35, ha="right", fontsize=7)
ax[1].set_ylabel(r"reference PM$_{2.5}$ ($\mu$g m$^{-3}$)")
ax[1].set_title("(b) loading by origin", fontsize=9)
for b, v in zip(bars, med):
    ax[1].text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.0f}", ha="center", fontsize=6.5)

# (c) seasonal switch -------------------------------------------------------------
ax[2].plot(seas.month, seas.fect_obs, "o-", color="#a11d33", label="observed")
ax[2].plot(seas.month, seas.B_background, "s--", color="#2f6f8f", label="background $B(t)$")
ax[2].axhspan(0, 8, color="#2f6f8f", alpha=0.08)
ax[2].text(7.5, 5.5, "marine floor", fontsize=6.5, color="#2f6f8f")
ax[2].set_xticks(range(1, 13, 2)); ax[2].set_xlabel("month")
ax[2].set_ylabel(r"PM$_{2.5}$ ($\mu$g m$^{-3}$)"); ax[2].set_ylim(0, None)
ax[2].set_title("(c) the seasonal switch", fontsize=9)
ax[2].legend(fontsize=7, frameon=False)

for a in ax:
    a.grid(alpha=0.25, linewidth=0.4)
    a.spines[["top", "right"]].set_visible(False)

fig.savefig(OUT / "transboundary.png", dpi=350, bbox_inches="tight")
print("wrote", OUT / "transboundary.png")
print(f"  DJF Indian+BoB = {djf[0]+djf[1]+djf[2]:.0f}%, JJA SW-marine = {jja[4]:.0f}%")
print(f"  IGP {sec.loc['IGP_E_India','median']:.1f} vs SW-marine {sec.loc['SW_marine','median']:.1f}")
