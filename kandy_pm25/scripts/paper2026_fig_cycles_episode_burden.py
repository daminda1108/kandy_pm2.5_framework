"""Three Kandy figures, regenerated against the current post-cap fields.

The previous suite dates from 16 July; the fields were rebuilt on 10 August when the coherence
cap was imposed. The cap changes the background, therefore the increment, therefore the spatial
contrast of every rendered field. Reusing those figures would have put pre-cap structure into a
paper whose Section 4 argues for the post-cap partition.

  cycles   seasonal and diurnal cycles, model against the two sensors
  episode  the December 2022 episode, field and basin-mean trace
  burden   exposure weighting and attributable burden

Everything is read from the shipped additive_v3 parquets and the exposure and health CSVs.

Output: results/figures/paper2026/{F_cycles,F_episode,F_burden}.{png,pdf}
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import PowerNorm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.stage1_satml.decomp import pubfig  # noqa: E402
from figdata import emit  # noqa: E402

DEC = ROOT / "data" / "processed" / "decomp"
OBS = ROOT / "data" / "processed" / "stage1_v3" / "dataset_v3_hourly.parquet"
OUT = ROOT / "results" / "figures" / "paper2026"
OUT.mkdir(parents=True, exist_ok=True)

YEARS = [2019, 2020, 2021, 2022, 2023]
LT = 5.5                      # Sri Lanka standard time, hours from UTC
MODEL = "#b2182b"
OBSC = "#2166ac"
INK = "#1a1a1a"
GREY = "#8c8c8c"


def basin_hourly() -> pd.DataFrame:
    """Basin-mean concentration per hour across the anchored years, in local time."""
    frames = []
    for y in YEARS:
        f = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive_v3.parquet",
                            columns=["time", "pm25_q50"])
        frames.append(f.groupby("time")["pm25_q50"].mean().rename("model"))
    s = pd.concat(frames).to_frame().reset_index()
    s["lt"] = pd.to_datetime(s["time"]).dt.tz_convert(None) + pd.Timedelta(hours=LT)
    return s


def sensor_hourly() -> pd.DataFrame:
    d = pd.read_parquet(OBS, columns=["datetime_utc", "pm25_observed"]).dropna()
    d["lt"] = pd.to_datetime(d["datetime_utc"]).dt.tz_convert(None) + pd.Timedelta(hours=LT)
    d = d[(d["lt"].dt.year >= YEARS[0]) & (d["lt"].dt.year <= YEARS[-1])]
    return d.rename(columns={"pm25_observed": "obs"})


def _norm(v: np.ndarray) -> np.ndarray:
    return v / np.nanmean(v)


def fig_cycles() -> None:
    """Model against the two Kandy sensors.

    IN-SAMPLE BY CONSTRUCTION. The temporal anchor is trained on the FECT residual target and
    its diurnal and seasonal amplitude is sharpened to the observed FECT swing, so agreement
    here measures the calibration, not skill. Correlations near unity are therefore expected
    and are NOT evidence of transfer. The out-of-sample evidence is the ten-city panel. This
    figure exists to show the SHAPE the model carries, in particular the afternoon minimum,
    which is counter-intuitive and worth seeing.
    """
    m, o = basin_hourly(), sensor_hourly()
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))

    # (a) seasonal, normalised so shape is compared rather than level
    ms = m.groupby(m["lt"].dt.month)["model"].mean()
    os_ = o.groupby(o["lt"].dt.month)["obs"].mean()
    r_s = np.corrcoef(_norm(ms.values), _norm(os_.reindex(ms.index).values))[0, 1]
    ax[0].plot(ms.index, _norm(ms.values), marker="o", ms=3.5, color=MODEL, label="model")
    ax[0].plot(os_.index, _norm(os_.values), marker="s", ms=3.5, color=OBSC, ls="--",
               label="sensors")
    ax[0].axhline(1.0, color=GREY, lw=0.6, zorder=0)
    ax[0].set_xticks(range(1, 13))
    ax[0].set_xticklabels(list("JFMAMJJASOND"))
    ax[0].set_ylabel("normalised concentration")
    ax[0].set_title("(a)  seasonal shape", loc="left")

    # (b) diurnal
    md = m.groupby(m["lt"].dt.hour)["model"].mean()
    od = o.groupby(o["lt"].dt.hour)["obs"].mean()
    r_d = np.corrcoef(_norm(md.values), _norm(od.reindex(md.index).values))[0, 1]
    ax[1].plot(md.index, _norm(md.values), marker="o", ms=3.0, color=MODEL, label="model")
    ax[1].plot(od.index, _norm(od.values), marker="s", ms=3.0, color=OBSC, ls="--",
               label="sensors")
    ax[1].axhline(1.0, color=GREY, lw=0.6, zorder=0)
    ax[1].axvspan(12, 16, color=GREY, alpha=0.12, zorder=0)
    ax[1].annotate("afternoon\nminimum", xy=(14, 0.80), ha="center", fontsize=6.4, color=INK)
    ax[1].set_xticks(range(0, 24, 4))
    ax[1].set_xlabel("hour, local time")
    ax[1].set_title("(b)  diurnal shape, night above midday", loc="left")

    for a in ax:
        a.legend(fontsize=6.6)
        a.grid(axis="y", zorder=0)
        a.tick_params(top=False, right=False, which="both")
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    ax[0].set_xlabel("month")

    fig.text(0.5, -0.02,
             "In sample: the anchor is calibrated to these sensors, so agreement measures the "
             "calibration rather than skill.",
             ha="center", fontsize=6.3, color=GREY, style="italic")
    fig.tight_layout()
    for e in ("png", "pdf"):
        fig.savefig(OUT / f"F_cycles.{e}", bbox_inches="tight")
    plt.close(fig)
    print(f"  cycles   seasonal r {r_s:.3f}   diurnal r {r_d:.3f}")
    emit("F_cycles", seasonal_r=round(float(r_s), 3), diurnal_r=round(float(r_d), 3))
    return r_s, r_d


def fig_episode() -> None:
    f = pd.read_parquet(DEC / "kandy_decomp_predictions_2022_additive_v3.parquet",
                        columns=["time", "lat", "lon", "pm25_q50"])
    f["time"] = pd.to_datetime(f["time"])
    ep = f[(f.time >= "2022-12-07") & (f.time < "2022-12-09")]
    hourly = ep.groupby("time")["pm25_q50"].mean()
    peak = hourly.idxmax()
    fld = ep[ep.time == peak].pivot(index="lat", columns="lon", values="pm25_q50")

    fig = plt.figure(figsize=(7.2, 3.1))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.35], wspace=0.42)

    ax0 = fig.add_subplot(gs[0])
    # Adaptive range for this hour. A fixed 10 to 110 scale renders the basin as one flat
    # orange square and hides the very structure the panel exists to show.
    lo, hi = np.percentile(fld.values, [1, 99])
    im = ax0.imshow(fld.values, origin="lower", cmap="YlOrRd",
                    norm=PowerNorm(1.15, vmin=lo, vmax=hi),
                    extent=[fld.columns.min(), fld.columns.max(),
                            fld.index.min(), fld.index.max()], aspect="auto")
    cax = ax0.inset_axes([1.03, 0.0, 0.045, 1.0])
    cb = fig.colorbar(im, cax=cax)
    cb.ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)", fontsize=6.5, labelpad=2)
    cb.ax.tick_params(labelsize=6, length=2)
    cb.outline.set_linewidth(0.5)
    ax0.set_xlabel("longitude (°E)")
    ax0.set_ylabel("latitude (°N)")
    ax0.set_title(f"(a)  peak hour, {(peak + pd.Timedelta(hours=LT)):%d %b %H:%M} LT",
                  loc="left")
    ax0.tick_params(labelsize=6.5, top=False, right=False)

    ax1 = fig.add_subplot(gs[1])
    lt = hourly.index + pd.Timedelta(hours=LT)
    ax1.plot(lt, hourly.values, color=MODEL, lw=1.3)
    ax1.axhline(55, color=INK, lw=0.8, ls=(0, (4, 2)))
    ax1.annotate("WHO 24 h interim target 1", xy=(lt[1], 56.5), fontsize=6.2, color=INK)
    ax1.scatter([peak + pd.Timedelta(hours=LT)], [hourly.max()], s=26, color=INK, zorder=5)
    ax1.annotate(f"{hourly.max():.1f}", xy=(peak + pd.Timedelta(hours=LT), hourly.max()),
                 xytext=(6, 3), textcoords="offset points", fontsize=6.6)
    ax1.set_ylabel("basin mean (µg m$^{-3}$)")
    ax1.set_title(f"(b)  episode mean {hourly.mean():.1f} µg m$^{{-3}}$ over 48 h", loc="left")
    ax1.grid(axis="y", zorder=0)
    ax1.tick_params(top=False, right=False, which="both", labelsize=6.5)
    for sp in ("top", "right"):
        ax1.spines[sp].set_visible(False)
    import matplotlib.dates as mdates
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=12))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %H:%M"))

    for e in ("png", "pdf"):
        fig.savefig(OUT / f"F_episode.{e}", bbox_inches="tight")
    plt.close(fig)
    print(f"  episode  mean {hourly.mean():.1f}  peak {hourly.max():.1f} at {peak}")
    emit("F_episode", mean_ug=round(float(hourly.mean()), 1), peak_ug=round(float(hourly.max()), 1),
         hours=int(hourly.size), peak_time_utc=str(peak))


def fig_burden() -> None:
    ex = pd.read_csv(DEC / "exposure_weighting.csv")
    hb = pd.read_csv(DEC / "health_burden.csv")

    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.3, 1.0]})

    tiers = [("area_mean", "area mean"), ("residential", "residential"),
             ("core", "populated core"), ("dynamic", "population weighted")]
    x = np.arange(len(ex))
    for i, (col, lab) in enumerate(tiers):
        ax[0].plot(x, ex[col], marker="o", ms=3.4, lw=1.2,
                   color=plt.cm.YlOrRd(0.35 + 0.18 * i), label=lab)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels(ex["year"].astype(int))
    ax[0].set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
    ax[0].set_title("(a)  the area mean understates exposure", loc="left")
    ax[0].legend(fontsize=6.2, ncol=2)
    ax[0].grid(axis="y", zorder=0)

    r = hb.iloc[0]
    vals = [r.attributable_deaths_per_yr, r.avoidable_vs_WHO_AQG5]
    labs = ["attributable\nto PM$_{2.5}$", "avoidable against\nthe WHO guideline"]
    b = ax[1].bar(labs, vals, width=0.55, color=[MODEL, "#f4a582"], zorder=3)
    ax[1].errorbar([0], [r.attributable_deaths_per_yr],
                   yerr=[[r.attributable_deaths_per_yr - r.ci_low],
                         [r.ci_high - r.attributable_deaths_per_yr]],
                   fmt="none", ecolor=INK, capsize=4, lw=0.9, zorder=4)
    for rect, v in zip(b, vals):
        ax[1].text(rect.get_x() + rect.get_width() / 2, v + 18, f"{int(v)}",
                   ha="center", fontsize=7.2)
    ax[1].set_ylim(0, 720)
    ax[1].set_ylabel("deaths per year")
    ax[1].set_title(f"(b)  {int(r.year)} burden, population {int(r.population):,}", loc="left")
    ax[1].grid(axis="y", zorder=0)

    for a in ax:
        a.tick_params(top=False, right=False, which="both")
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)

    fig.tight_layout()
    for e in ("png", "pdf"):
        fig.savefig(OUT / f"F_burden.{e}")
    plt.close(fig)
    print(f"  burden   {int(r.attributable_deaths_per_yr)} "
          f"[{int(r.ci_low)}, {int(r.ci_high)}] deaths/yr, uplift {r.exposure_uplift_pct}%")


if __name__ == "__main__":
    print("regenerating against post-cap fields")
    fig_cycles()
    fig_episode()
    fig_burden()
