"""The model's FIELD against the NBRO Kandy record  (ledger F.65, re-run 2026-09-04)

WHY THIS EXISTS. §6.5 states that the NBRO comparison is genuinely out of sample because the
pixel containing that station sits 15.6 per cent above the basin mean, and that the whole of the
lift is imposed physics never fitted to a Kandy station. That is the load-bearing sentence in
the paper's only external check, and the 15.6 was a literal typed into prose. It is regenerated
here from the shipped field.

WHAT MAKES THE TEST OUT OF SAMPLE. The temporal anchor is calibrated to the two FECT sensors, so
the model's basin MEAN is not independent of Kandy observations. The spatial pattern is not: it
is an emission proxy times a confinement term, both imposed, neither fitted to anything measured
in this city. So the quantity under test is the lift -- how far the field rises from the basin
mean to that particular pixel -- and not the level. If the lift were zero the comparison would
reduce to a check on the anchor and would carry no spatial information at all.

⚠ The observed record is 24-hour means over 360 days per year and the model is hourly over the
full year, so the comparison is of annual means and nothing finer is claimed.

Usage: .venv/Scripts/python.exe scripts/nbro_pixel_check.py
Out:   data/processed/decomp/nbro_pixel_check.csv
       data/processed/paper_figures/nbro_pixel.json   (read by build_claims.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from figdata import emit  # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"

# NBRO's Kandy station, from the network's own hourly feed (data/external/nbro/). Read from the
# feed rather than transcribed: a coordinate typed by hand is how gotcha #49 happened.
NBRO_FEED = REPO / "data" / "external" / "nbro" / "nbro_live_hourly.parquet"
NBRO_NAME = "Kandy"

# Nirmani et al. (2025), CLEAN Soil Air Water, 10.1002/clen.70051, Table 1. Obtained from NBRO
# by official request; N = 360 days in each year. EXTERNAL values -- cited, never tokenised.
OBSERVED = {2021: 19.6, 2022: 22.7}


def station_coord() -> tuple[float, float]:
    d = pd.read_parquet(NBRO_FEED, columns=["name", "latitude", "longitude"])
    row = d[d.name.str.strip().str.casefold() == NBRO_NAME.casefold()].iloc[0]
    return float(row.latitude), float(row.longitude)


def main() -> int:
    slat, slon = station_coord()
    print(f"NBRO Kandy station at {slat:.4f}N {slon:.4f}E  (from the network feed)\n")

    rows = []
    for year, obs in OBSERVED.items():
        p = DEC / f"kandy_decomp_predictions_{year}_additive_v3.parquet"
        if not p.exists():
            print(f"  {year}: no shipped field")
            continue
        f = pd.read_parquet(p, columns=["lat", "lon", "pm25_q50"])
        cell = f.groupby(["lat", "lon"]).pm25_q50.mean()

        lats = np.array(sorted({i[0] for i in cell.index}))
        lons = np.array(sorted({i[1] for i in cell.index}))
        plat = float(lats[np.abs(lats - slat).argmin()])
        plon = float(lons[np.abs(lons - slon).argmin()])
        # how far the station sits from the centre of the cell it lands in -- reported so the
        # reader can see the pixel really does contain the station
        off_km = 111.0 * float(np.hypot(plat - slat, (plon - slon) * np.cos(np.radians(slat))))

        pix = float(cell.loc[(plat, plon)])
        area = float(cell.mean())
        rows.append(dict(year=year, observed=obs, model_pixel=pix, model_area=area,
                         lift_pct=100.0 * (pix / area - 1.0),
                         diff_pct=100.0 * (pix / obs - 1.0),
                         pixel_lat=plat, pixel_lon=plon, station_offset_km=off_km))
        print(f"  {year}   observed {obs:5.1f}   pixel {pix:6.2f}   area {area:6.2f}"
              f"   lift {rows[-1]['lift_pct']:+5.1f}%   model-obs {rows[-1]['diff_pct']:+5.1f}%")

    if not rows:
        return 1
    d = pd.DataFrame(rows)
    d.to_csv(DEC / "nbro_pixel_check.csv", index=False)
    print(f"\n  station sits {rows[0]['station_offset_km']:.2f} km from its cell centre")
    print(f"  wrote {(DEC / 'nbro_pixel_check.csv').relative_to(REPO)}")

    # The lift differs by year, and the paper quoted one year's value as though it were the
    # property. Emit both plus the mean, and let the prose say which it means.
    emit("nbro_pixel",
         lift_pct_2021=round(float(d[d.year == 2021].lift_pct.iloc[0]), 1),
         lift_pct_2022=round(float(d[d.year == 2022].lift_pct.iloc[0]), 1),
         lift_pct_mean=round(float(d.lift_pct.mean()), 1),
         model_pixel_2021=round(float(d[d.year == 2021].model_pixel.iloc[0]), 2),
         model_pixel_2022=round(float(d[d.year == 2022].model_pixel.iloc[0]), 2),
         model_area_2021=round(float(d[d.year == 2021].model_area.iloc[0]), 2),
         model_area_2022=round(float(d[d.year == 2022].model_area.iloc[0]), 2),
         diff_pct_2021=round(float(d[d.year == 2021].diff_pct.iloc[0]), 1),
         diff_pct_2022=round(float(d[d.year == 2022].diff_pct.iloc[0]), 1),
         station_offset_km=round(float(rows[0]["station_offset_km"]), 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
