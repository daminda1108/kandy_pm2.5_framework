"""independent_visibility.py — Phase 5 independent validation via airport visibility.

METAR horizontal visibility is a physically independent proxy for aerosol extinction
(Koschmieder) and is NOT used anywhere in the model. We pull Colombo/Bandaranaike (VCBI)
visibility from the Iowa Environmental Mesonet ASOS archive and correlate a full year of
daily-mean visibility against the model's daily Kandy basin PM2.5. Haze lowers visibility,
so a negative correlation is the independent corroboration.

Caveat carried in the paper: VCBI is coastal, ~90 km from Kandy, and visibility is also
lowered by rain/humidity, so this is a regional, noisy corroboration of the documented
island-wide episodes — not a Kandy point measurement.

Out: data/processed/decomp/independent_visibility_{year}.csv
     results/figures/paper_figures_v2/S3_visibility.png
"""
from __future__ import annotations
import io
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "results" / "figures" / "paper_figures_v2"
OUT.mkdir(parents=True, exist_ok=True)
YEAR = 2022
EPISODES = {"2022-12-07": "Dec 2022 haze"}  # documented, within YEAR


def fetch_vsby(station, y):
    url = (f"https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station={station}"
           f"&data=vsby&year1={y}&month1=1&day1=1&year2={y}&month2=12&day2=31"
           f"&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&trace=T")
    r = subprocess.run(["curl", "-s", "--max-time", "120", url], capture_output=True, text=True)
    df = pd.read_csv(io.StringIO(r.stdout))
    df["vsby"] = pd.to_numeric(df.vsby, errors="coerce")
    df["date"] = pd.to_datetime(df.valid, errors="coerce").dt.date
    daily = df.groupby("date").vsby.mean().dropna() * 1.60934   # miles -> km
    return daily


def model_daily_pm(y):
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive_v2.parquet",
                        columns=["time", "pm25_q50"])
    d["date"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo").dt.date
    return d.groupby("date").pm25_q50.mean()


def main():
    vis = fetch_vsby("VCBI", YEAR)
    pm = model_daily_pm(YEAR)
    df = pd.concat([vis.rename("visibility_km"), pm.rename("model_pm25")], axis=1).dropna()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    r, p = pearsonr(df.model_pm25, df.visibility_km)
    df.to_csv(DEC / f"independent_visibility_{YEAR}.csv")
    print(f"VCBI daily visibility vs model Kandy daily PM2.5, {YEAR}: n={len(df)} days, "
          f"Pearson r={r:+.2f} (p={p:.1e})")
    print(f"  visibility {df.visibility_km.min():.1f}-{df.visibility_km.max():.1f} km; "
          f"model PM {df.model_pm25.min():.1f}-{df.model_pm25.max():.1f}")

    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.2), constrained_layout=True)
    ax[0].plot(df.index, df.visibility_km, color="#1f6f8b", lw=0.9, label="VCBI visibility (km)")
    ax0b = ax[0].twinx()
    ax0b.plot(df.index, df.model_pm25, color="#B35806", lw=0.9, label="model Kandy PM$_{2.5}$")
    ax[0].set_ylabel("visibility (km)", color="#1f6f8b"); ax0b.set_ylabel("PM$_{2.5}$", color="#B35806")
    ax[0].set_title(f"(a) independent airport visibility vs model PM$_{{2.5}}$ ({YEAR})", fontsize=8.6)
    for d0, lab in EPISODES.items():
        ax[0].axvline(pd.to_datetime(d0), color="grey", ls="--", lw=0.8)
    ax[0].tick_params(axis="x", labelrotation=30, labelsize=6.5)

    ax[1].scatter(df.model_pm25, df.visibility_km, s=14, c="#B35806", edgecolor="k", linewidth=0.2, alpha=0.7)
    ax[1].set_xlabel("model Kandy daily PM$_{2.5}$ ($\\mu$g m$^{-3}$)")
    ax[1].set_ylabel("VCBI visibility (km)")
    ax[1].set_title(f"(b) r = {r:+.2f}  (n={len(df)} days)", fontsize=8.6)
    ax[1].grid(alpha=0.25)
    fig.suptitle("Independent corroboration: higher modelled PM$_{2.5}$ coincides with lower airport "
                 "visibility\n(Colombo VCBI, ~90 km, not a model input)", fontsize=8.8)
    fig.savefig(OUT / "S3_visibility.png", dpi=350, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {DEC/f'independent_visibility_{YEAR}.csv'}\nwrote {OUT/'S3_visibility.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
