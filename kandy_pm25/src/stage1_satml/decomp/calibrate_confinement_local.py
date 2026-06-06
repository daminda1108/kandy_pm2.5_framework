"""
calibrate_confinement_local.py — LOCAL calibration of the confinement amplitude
from the Kandy FECT floor-to-ridge pair (assume FECT calibration real, user
2026-06-03).

The 300-valley screen showed no PUBLIC network samples the floor-to-ridge
gradient. But Kandy's own non-public FECT sensors are sited across elevation:
  NIFS/KOALA  floor 477 m, confinement c=+0.91 (trapped)   → 24.5 µg/m³
  Hantana     ridge 755 m, confinement c=-1.69 (ventilated) → 10.5 µg/m³
giving an OBSERVED annual floor/ridge ratio of 24.5/10.5 = 2.33x. The current
model (kappa=0.15, linear M=1+kappa*w*c) reproduces only ~1.2-1.3x — it under-
traps. Here we calibrate kappa to the observed ratio.

The linear form cannot reach 2.33x without driving M negative on the ridge
(c=-1.69), so we also fit a positivity-safe log form  M = exp(kappa*w*c)/<.>.

Caveat: 2-3 points, conditional on FECT PurpleAir calibration; A_transport
ventilation of the ridge is set aside (folding it in would lower the kappa need).

Out: data/processed/decomp/M_confinement_calibrated_local.npz
     results/figures/kandy_decomp/geography/confinement_calibration.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.ndimage import zoom

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
DEC = HERE / "data" / "processed" / "decomp"
GRID = HERE / "data" / "processed" / "stage1_v3"
OUT = HERE / "results" / "figures" / "kandy_decomp" / "geography"
OUT.mkdir(parents=True, exist_ok=True)

NIFS = (7.2675, 80.5985, 24.5)
HANT = (7.265, 80.625, 10.5)
CITY = (7.2906, 80.6337, None)
H_RIDGE = 300.0
RATIO_OBS = NIFS[2] / HANT[2]


def wbar(h_ridge=H_RIDGE):
    """Time-mean trapping gate w̄ = <clip((H-BLH)/H,0,1)> over 2019-2023."""
    blh = []
    for y in range(2019, 2024):
        f = GRID / f"inference_grid_{y}_s12451.parquet"
        if f.exists():
            blh.append(pd.read_parquet(f, columns=["blh_m"])["blh_m"].values)
    blh = np.concatenate(blh)
    w = np.clip((h_ridge - blh) / h_ridge, 0, 1)
    return float(np.nanmean(w)), float(np.nanmean(blh))


def main():
    M = np.load(DEC / "M_confinement_kandy.npz")
    c, lats, lons = M["c"], M["lats"], M["lons"]
    S = np.load(DEC / "S_emit_kandy.npz")["S_emit"]

    def at(la, lo, A):
        i = int(np.argmin(np.abs(lats - la))); j = int(np.argmin(np.abs(lons - lo)))
        return A[i, j]
    c_n, c_h = at(*NIFS[:2], c), at(*HANT[:2], c)
    S_n, S_h = at(*NIFS[:2], S), at(*HANT[:2], S)
    w_bar, blh_bar = wbar()
    print(f"w̄ (trapping gate, H_ridge={H_RIDGE:.0f}) = {w_bar:.3f}   mean BLH {blh_bar:.0f} m")
    print(f"c: NIFS {c_n:+.2f}  Hantana {c_h:+.2f}   S: NIFS {S_n:.2f}  Hantana {S_h:.2f}")
    print(f"observed floor/ridge ratio = {RATIO_OBS:.2f}x")

    # current linear, kappa=0.15
    def ratio_lin(k):
        return (S_n * (1 + k * w_bar * c_n)) / (S_h * (1 + k * w_bar * c_h))
    print(f"\ncurrent model (kappa=0.15, linear) ratio = {ratio_lin(0.15):.2f}x  → under-traps")

    # solve linear kappa (watch positivity: M_h>0 needs kappa*w̄ < 1/1.69)
    k_pos_max = 1.0 / (w_bar * abs(c_h)) * 0.999
    try:
        k_lin = brentq(lambda k: ratio_lin(k) - RATIO_OBS, 0.01, k_pos_max)
        mh = 1 + k_lin * w_bar * c_h
        note = f"M_ridge={mh:.2f}" + ("" if mh > 0 else "  ← NEGATIVE/unphysical")
    except ValueError:
        k_lin, note = float("nan"), f"unreachable below positivity limit kappa<{k_pos_max:.2f}"
    print(f"linear kappa to hit {RATIO_OBS:.2f}x:  {k_lin:.2f}   ({note})")
    print(f"   linear max achievable ratio (at positivity limit) = {ratio_lin(k_pos_max):.2f}x")

    # log form: M=exp(kappa*w̄*c); ratio = (S_n/S_h)*exp(kappa*w̄*(c_n-c_h))
    k_log = (np.log(RATIO_OBS) - np.log(S_n / S_h)) / (w_bar * (c_n - c_h))
    print(f"\nlog form kappa to hit {RATIO_OBS:.2f}x:  {k_log:.2f}  (stays positive)")

    # build calibrated annual confinement field (log form, normalised mean 1)
    Mbar = np.exp(k_log * w_bar * c); Mbar /= Mbar.mean()
    cur = np.exp(0.15 * w_bar * c); cur /= cur.mean()    # not used; show linear current
    Mbar_cur = (1 + 0.15 * w_bar * c)

    np.savez(DEC / "M_confinement_calibrated_local.npz",
             c=c, lats=lats, lons=lons, kappa_log=k_log, kappa_linear=k_lin,
             w_bar=w_bar, H_ridge_m=H_RIDGE, Mbar_calibrated=Mbar,
             ratio_obs=RATIO_OBS, form="exp(kappa*wbar*c) normalised")

    # ── before/after annual-mean field (L · S · M̄) ──
    L = 23.76
    field_cur = L * S * Mbar_cur
    field_cal = L * S * Mbar
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    r_cur = at(*NIFS[:2], field_cur) / at(*HANT[:2], field_cur)
    r_cal = at(*NIFS[:2], field_cal) / at(*HANT[:2], field_cal)
    fig, ax = plt.subplots(1, 2, figsize=(11.4, 5.4), constrained_layout=True)
    vmin, vmax = 8, 30
    for a, F, ttl in [(ax[0], field_cur, f"(a) Current confinement (κ=0.15)\n"
                       f"NIFS/Hant {r_cur:.2f}× (model under-traps)"),
                      (ax[1], field_cal, f"(b) Locally-calibrated (κ_log={k_log:.2f})\n"
                       f"NIFS/Hant {r_cal:.2f}× → matches obs {RATIO_OBS:.2f}×")]:
        im = a.imshow(zoom(F, 8, order=3), origin="lower", extent=ext, cmap="YlOrRd",
                      vmin=vmin, vmax=vmax, aspect="auto", interpolation="bilinear")
        for nm, (la, lo, v) in {"NIFS 24.5": NIFS, "Hantana 10.5": HANT, "city": CITY}.items():
            a.plot(lo, la, "o", mfc="cyan", mec="k", mew=0.9, ms=7, zorder=5)
            a.annotate(nm, (lo, la), xytext=(5, 4), textcoords="offset points",
                       fontsize=7.5, fontweight="bold")
        a.set_title(ttl, fontsize=9); a.set_xlabel("Lon (°E)")
    ax[0].set_ylabel("Lat (°N)")
    fig.colorbar(im, ax=ax, label="annual PM₂.₅ (µg m⁻³)", extend="both", shrink=0.8)
    fig.suptitle("Local confinement calibration from the FECT floor-ridge pair — "
                 "strengthening κ makes the enclosed core emerge and the Hantana "
                 "ridge ventilate, reproducing the observed 2.33× (assumes FECT real)",
                 fontsize=10)
    fig.savefig(OUT / "confinement_calibration.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\nWrote {DEC/'M_confinement_calibrated_local.npz'}")
    print(f"Wrote {OUT/'confinement_calibration.png'}")


if __name__ == "__main__":
    main()
