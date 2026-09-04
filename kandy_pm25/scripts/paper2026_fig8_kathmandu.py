"""Figure 8: Kathmandu, the deepest single test in the panel.

Thirty-nine monitors withheld against the two the model was given. Three panels, matching the
three quantities the scorecard reports separately:

  (a) seasonal cycle, model against the withheld network mean
  (b) diurnal cycle, same
  (c) fine spatial rank, per-station anomaly after the network mean is removed within each hour

Panels (a) and (b) are OUT OF SAMPLE, unlike the equivalent Kandy figure: the model saw two
stations and is scored against the other thirty-nine. That contrast is the reason this figure
exists.

Output: results/figures/paper2026/F8_kathmandu.{png,pdf}
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.stage1_satml.decomp import pubfig  # noqa: E402
from figdata import emit  # noqa: E402

KTM = ROOT / "data" / "processed" / "decomp_kathmandu"
OBS = ROOT / "data" / "processed" / "stage2" / "kathmandu_perstation_v13.parquet"
OUT = ROOT / "results" / "figures" / "paper2026"
OUT.mkdir(parents=True, exist_ok=True)

YEARS = [2024, 2025]
LT = 5.75                     # Nepal standard time
MODEL = "#b2182b"
OBSC = "#2166ac"
INK = "#1a1a1a"
GREY = "#8c8c8c"


def load_field() -> pd.DataFrame:
    f = pd.concat([pd.read_parquet(KTM / f"kathmandu_decomp_predictions_{y}_additive_v2.parquet",
                                   columns=["time", "lat", "lon", "pm25_q50"])
                   for y in YEARS], ignore_index=True)
    # the field carries tz-aware timestamps and the station table does not;
    # normalise both to naive UTC or the merge silently fails
    f["time"] = pd.to_datetime(f["time"], utc=True).dt.tz_localize(None)
    return f


def load_obs() -> pd.DataFrame:
    o = pd.read_parquet(OBS, columns=["datetime_utc", "station_id", "lat", "lon", "pm25"])
    o = o.dropna(subset=["pm25"])
    o["time"] = pd.to_datetime(o["datetime_utc"], utc=True).dt.tz_localize(None)
    return o[(o.time.dt.year >= YEARS[0]) & (o.time.dt.year <= YEARS[-1])]


def at_stations(field: pd.DataFrame, stations: pd.DataFrame) -> pd.DataFrame:
    """Interpolate the field to station coordinates, hour by hour.

    fill_value=None would extrapolate; a station outside the box then returns an absurd value
    and poisons every network mean it enters. NaN and drop instead.
    """
    lats = np.sort(field.lat.unique())
    lons = np.sort(field.lon.unique())
    pts = stations[["lat", "lon"]].to_numpy()
    out = []
    for t, g in field.groupby("time"):
        grid = (g.sort_values(["lat", "lon"])["pm25_q50"].to_numpy()
                .reshape(len(lats), len(lons)))
        itp = RegularGridInterpolator((lats, lons), grid, bounds_error=False, fill_value=np.nan)
        out.append(pd.DataFrame({"time": t, "station_id": stations.station_id.values,
                                 "model": itp(pts)}))
    return pd.concat(out, ignore_index=True).dropna()


def main() -> None:
    field, obs = load_field(), load_obs()
    stations = obs.groupby("station_id")[["lat", "lon"]].first().reset_index()
    mod = at_stations(field, stations)

    df = obs.merge(mod, on=["time", "station_id"], how="inner")
    df["lt"] = df["time"] + pd.Timedelta(hours=LT)
    n_st = df.station_id.nunique()

    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.6),
                           gridspec_kw={"width_ratios": [1.0, 1.0, 0.95]})

    # (a) seasonal, network means
    ms = df.groupby(df["lt"].dt.month)["model"].mean()
    os_ = df.groupby(df["lt"].dt.month)["pm25"].mean()
    r_s = np.corrcoef(ms.values, os_.reindex(ms.index).values)[0, 1]
    ax[0].plot(ms.index, ms.values, marker="o", ms=3.2, color=MODEL, label="model")
    ax[0].plot(os_.index, os_.values, marker="s", ms=3.2, color=OBSC, ls="--", label="withheld")
    ax[0].set_xticks(range(1, 13))
    ax[0].set_xticklabels(list("JFMAMJJASOND"), fontsize=6)
    ax[0].set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
    ax[0].set_title("(a)  seasonal cycle", loc="left")

    # (b) diurnal
    md = df.groupby(df["lt"].dt.hour)["model"].mean()
    od = df.groupby(df["lt"].dt.hour)["pm25"].mean()
    r_d = np.corrcoef(md.values, od.reindex(md.index).values)[0, 1]
    ax[1].plot(md.index, md.values, marker="o", ms=2.8, color=MODEL, label="model")
    ax[1].plot(od.index, od.values, marker="s", ms=2.8, color=OBSC, ls="--", label="withheld")
    ax[1].set_xticks(range(0, 24, 6))
    ax[1].set_xlabel("hour, local time")
    ax[1].set_title("(b)  diurnal cycle", loc="left")

    # (c) spatial rank: remove the network mean within each hour, then compare station means
    for col in ("model", "pm25"):
        df[col + "_a"] = df[col] - df.groupby("time")[col].transform("mean")
    st = df.groupby("station_id")[["model_a", "pm25_a"]].mean()
    rho = spearmanr(st.model_a, st.pm25_a).statistic
    ax[2].axhline(0, color=GREY, lw=0.6, zorder=0)
    ax[2].axvline(0, color=GREY, lw=0.6, zorder=0)
    ax[2].scatter(st.model_a, st.pm25_a, s=16, color=MODEL, alpha=0.75,
                  edgecolor="white", linewidth=0.4, zorder=3)
    ax[2].set_xlabel("modelled anomaly (µg m$^{-3}$)")
    ax[2].set_ylabel("observed anomaly")
    ax[2].set_title("(c)  fine spatial rank", loc="left")

    ax[0].legend(fontsize=6.2)
    for a in ax:
        a.grid(axis="y", zorder=0)
        a.tick_params(top=False, right=False, which="both", labelsize=6.5)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    ax[0].set_xlabel("month")

    fig.text(0.5, -0.03,
             f"Out of sample: the model was given two stations and is scored against the "
             f"other {n_st - 2}. Scored values are in Table 1.", ha="center", fontsize=6.3, color=GREY, style="italic")
    fig.tight_layout()
    for e in ("png", "pdf"):
        fig.savefig(OUT / f"F8_kathmandu.{e}", bbox_inches="tight")
    plt.close(fig)

    print(f"wrote F8_kathmandu  stations {n_st}, hours {df.time.nunique():,}")
    print(f"  seasonal r {r_s:.3f}   diurnal r {r_d:.3f}   spatial rho {rho:.3f}")
    lvl = 100 * (df.model.mean() / df.pm25.mean() - 1)
    print(f"  level bias {lvl:+.1f}%")

    # published so the manuscript quotes these rather than recomputing them (see figdata.py)
    emit("F8_kathmandu", stations=int(n_st), scored_stations=int(n_st - 2),
         hours=int(df.time.nunique()), seasonal_r=round(float(r_s), 3),
         diurnal_r=round(float(r_d), 3), spatial_rho=round(float(rho), 3),
         level_bias_pct=round(float(lvl), 1))


if __name__ == "__main__":
    main()
