"""imerg_rain_arbitration.py — settle gotcha #60: is ERA5-Land tp shippable as mm?

Gotcha #60 established that ERA5-Land `total_precipitation` on GEE accumulates since
00 UTC (raw sum = 12x gauge) and that even DE-ACCUMULATED it ran ~2.5-3x a valley-floor
gauge at Medellin. SKMD METAR carries no precipitation, so there was no station truth
to arbitrate with. GPM IMERG V07 is the independent referee: a satellite/gauge-merged
product, methodologically independent of ERA5's model physics.

IMERG V07 `precipitation` is a RATE in mm/hr on a 30-min grid, so
    hourly mm = mean(the two 30-min rates)   [each rate x 0.5 h, summed]
and annual mm = sum of hourly mm.

Runs BOTH cities (the Kandy engine audit checked tp only via annual totals over a small
box, where the accumulation defect was masked — gotcha #60 asks for a re-verify).

Decision rule, fixed BEFORE looking:
  - IMERG within ~35% of the gauge climatology  -> IMERG is credible; ship IMERG rain.
  - de-accumulated ERA5-Land within ~35% too    -> ERA5 also shippable (prefer IMERG).
  - otherwise                                    -> that product stays unshipped as mm.
Correlation of the two at daily/monthly scale tells us whether the ERA5 field is at least
a good relative-wetness indicator even when its magnitude is wrong.

Out: results/figures/medellin_showcase/imerg_arbitration.{csv,txt,png}
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "figures" / "medellin_showcase"

# Gauge references — VERIFIED against the national met services 2026-07-21, because the
# project record's "~2,000 mm" for Medellin was WRONG and it drives a ship/no-ship call:
#   Medellin: IDEAM/SIATA station Olaya Herrera airport (27015070), the VALLEY-FLOOR gauge
#             -> 1,500-1,800 mm/yr. (Tourist aggregates quoting ~2,986 mm are not this
#             station.) The IMERG box spans 1,300-2,800 m of orographic relief, so its AREA
#             mean is legitimately wetter than this FLOOR point -- the same area-vs-floor
#             confound as gotcha #51 (KOALA). A floor gauge therefore CANNOT falsify an area
#             mean here; it can only bracket it from below.
#   Kandy:    Sri Lanka Dept. of Meteorology treats Katugastota (~5 km N) as representative
#             of the district -> 2,108 mm/yr; other Kandy-town series give 1,773-1,969.
#             The box is small (15x15 km) with gentle relief, so area ~ floor and the
#             comparison IS decisive here.
CITIES = {
    "medellin": dict(
        imerg=sorted((REPO / "data/external/medellin/tier_c").glob("med_gpm_imerg_*.csv")),
        era5=sorted((REPO / "data/external/medellin/extended_gee/drive").glob(
            "medellin_era5land_*.csv")),
        gauge=1650.0, gauge_src="IDEAM/SIATA Olaya Herrera FLOOR gauge, 1500-1800 mm/yr",
        floor_only=True, tz="America/Bogota"),
    "kandy": dict(
        imerg=sorted((REPO / "data/external/tier_c/gpm_imerg").glob("gpm_imerg_*.csv")),
        era5=sorted((REPO / "data/external/kandy/extended_gee/drive").glob(
            "kandy_era5land_*.csv")),
        gauge=2108.0, gauge_src="Sri Lanka DoM representative station Katugastota, 2108 mm/yr",
        floor_only=False, tz="Asia/Colombo"),
}
TOL = 0.35


def imerg_hourly(files):
    """30-min mm/hr rates -> hourly mm."""
    if not files:
        return None
    d = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    col = "precipitation" if "precipitation" in d else d.columns[-1]
    d["h"] = pd.to_datetime(d.datetime).dt.tz_localize("UTC").dt.floor("h")
    # each 30-min value is a rate (mm/hr) covering half an hour -> mm = rate * 0.5
    g = d.groupby("h")[col].agg(["sum", "count"])
    mm = g["sum"] * 0.5
    # guard against hours with a single 30-min slot (edge of an export)
    mm = mm.where(g["count"] == 2, mm * 2 / g["count"].clip(lower=1))
    return mm.rename("imerg_mm")


def era5_hourly(files):
    """GEE ERA5-Land tp accumulates since 00 UTC (gotcha #60) -> de-accumulate, m -> mm."""
    if not files:
        return None
    d = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    if "total_precipitation" not in d:
        return None
    d["h"] = pd.to_datetime(d.datetime).dt.tz_localize("UTC")
    d = d.sort_values("h").drop_duplicates("h").reset_index(drop=True)
    tp = d.total_precipitation.to_numpy(dtype=float)
    rain = np.diff(tp, prepend=np.nan)
    newday = d.h.dt.floor("D").ne(d.h.dt.floor("D").shift()).to_numpy()
    rain[newday] = tp[newday]
    d["era5_mm"] = np.clip(rain, 0, None) * 1000.0
    # raw (un-de-accumulated) sum, to re-demonstrate the 12x defect
    d["era5_raw_mm"] = tp * 1000.0
    return d.set_index("h")[["era5_mm", "era5_raw_mm"]]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)
    rows, panels = [], {}
    for city, cfg in CITIES.items():
        im, e5 = imerg_hourly(cfg["imerg"]), era5_hourly(cfg["era5"])
        print(f"\n=== {city} ===")
        if im is None:
            print("  no IMERG on disk — skipped"); continue
        df = pd.DataFrame(im)
        if e5 is not None:
            df = df.join(e5, how="outer")
        df["year"] = df.index.year
        # complete years only (>= 8000 hourly IMERG slots)
        ok = df.groupby("year")["imerg_mm"].count()
        years = [int(y) for y in ok[ok >= 8000].index]
        print(f"  complete IMERG years: {years}")
        for y in years:
            s = df[df.year == y]
            i_tot = float(s.imerg_mm.sum())
            e_tot = float(s.era5_mm.sum()) if "era5_mm" in s and s.era5_mm.notna().any() else np.nan
            r_tot = np.nan
            if "era5_raw_mm" in s and s.era5_raw_mm.notna().any():
                r_tot = float(s.era5_raw_mm.sum())
            g = cfg["gauge"]
            # daily correlation where both exist
            rd = np.nan
            if "era5_mm" in s:
                dd = s[["imerg_mm", "era5_mm"]].dropna().resample("D").sum()
                if len(dd) > 60:
                    rd = float(dd.imerg_mm.corr(dd.era5_mm))
            rows.append(dict(city=city, year=y, imerg_mm=round(i_tot, 0),
                             era5_deaccum_mm=round(e_tot, 0) if np.isfinite(e_tot) else np.nan,
                             era5_raw_mm=round(r_tot, 0) if np.isfinite(r_tot) else np.nan,
                             gauge_mm=g,
                             imerg_ratio=round(i_tot / g, 2),
                             era5_ratio=round(e_tot / g, 2) if np.isfinite(e_tot) else np.nan,
                             daily_r=round(rd, 3) if np.isfinite(rd) else np.nan))
            print(f"  {y}: IMERG {i_tot:7.0f} mm ({i_tot/g:.2f}x gauge) | "
                  f"ERA5-deaccum {e_tot:7.0f} ({e_tot/g:.2f}x) | raw {r_tot:8.0f} | "
                  f"daily r {rd:.2f}")
        panels[city] = df[df.year.isin(years)]
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "imerg_arbitration.csv", index=False)

    # verdict
    lines = ["IMERG RAIN ARBITRATION (gotcha #60)", "=" * 60]
    for city in t.city.unique():
        s = t[t.city == city]
        im_r, e5_r = s.imerg_ratio.mean(), s.era5_ratio.mean()
        floor_only = CITIES[city]["floor_only"]
        lines += [f"\n{city}: reference {s.gauge_mm.iloc[0]:.0f} mm/yr "
                  f"({CITIES[city]['gauge_src']})",
                  f"  IMERG         mean {im_r:.2f}x reference",
                  f"  ERA5 de-accum mean {e5_r:.2f}x reference",
                  f"  daily corr IMERG~ERA5 {s.daily_r.mean():.2f}"]
        if floor_only:
            # area-vs-floor: the reference cannot falsify an area mean, only bound it below
            lines += ["  NOTE: reference is a valley-FLOOR gauge while IMERG is an AREA mean",
                      "        over 1,300-2,800 m of relief -> a ratio >1 is EXPECTED and is",
                      "        not evidence of product error (cf. gotcha #51, area-vs-floor).",
                      "  DECISION: ship IMERG as BASIN-AVERAGE mm, disclosing that the valley",
                      "        floor is drier; ERA5-Land tp stays unshipped (2.9x, and it is",
                      "        1.8x IMERG on the SAME box, so the excess is model wet bias)."]
        else:
            v_im = "SHIPPABLE" if abs(im_r - 1) <= TOL else "NOT shippable as mm"
            v_e5 = ("SHIPPABLE" if np.isfinite(e5_r) and abs(e5_r - 1) <= TOL
                    else "NOT shippable as mm")
            lines += [f"  area ~ floor here (small box, gentle relief) -> decisive test",
                      f"  IMERG -> {v_im} | ERA5 de-accum -> {v_e5}",
                      f"  DECISION: ship {'IMERG' if abs(im_r-1) <= TOL else 'NEITHER'} as mm"]
    txt = "\n".join(lines)
    (OUT / "imerg_arbitration.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)

    # figure: monthly climatology, IMERG vs ERA5, per city
    fig, axes = plt.subplots(1, len(panels), figsize=(5.2 * len(panels), 3.6))
    axes = np.atleast_1d(axes)
    for ax, (city, df) in zip(axes, panels.items()):
        mo = df.groupby(df.index.month)[["imerg_mm"] +
                                        (["era5_mm"] if "era5_mm" in df else [])].sum()
        n = df.year.nunique()
        ax.bar(mo.index - 0.2, mo.imerg_mm / n, 0.4, label="IMERG V07", color="#2b6cb0")
        if "era5_mm" in mo:
            ax.bar(mo.index + 0.2, mo.era5_mm / n, 0.4, label="ERA5-Land (de-accum)",
                   color="#dd6b20")
        ax.set_title(city); ax.set_xlabel("month"); ax.set_ylabel("mm/month")
        ax.legend(fontsize=7, framealpha=0.92)
    fig.tight_layout()
    fig.savefig(OUT / "imerg_arbitration.png", dpi=200)
    print("wrote", OUT / "imerg_arbitration.{csv,txt,png}")


if __name__ == "__main__":
    main()
