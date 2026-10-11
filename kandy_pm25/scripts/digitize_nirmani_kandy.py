"""digitize_nirmani_kandy.py -- recover the daily PM2.5 series at the NBRO Kandy station (2021, 2022) from the
published figure of Nirmani et al. (2025), CLEAN Soil Air Water, doi:10.1002/clen.70051, Figure 3 (Kandy panel).

EXPLORATORY (2026-10-11). The daily data were obtained by the authors from NBRO on official request and are not
published as numbers; the figure is the only public form. Digitisation:
  * axes calibrated from the panel's own gridlines: value 80 at pixel row 715.5, 40 at 768.5 (so 0 at 821.5;
    the 25 ug/m3 standard line falls at row 788 as predicted); 1 January at column 110, 365 days across 1260 px;
  * the 2021 series is the cyan line, 2022 the orange line, separated by colour; monthly-mean triangles (blue,
    red), the standard line (green-grey) and the guideline (black dashes) are excluded by colour;
  * each column's line position is the median row of its line pixels; a day's value is the median over the
    columns that fall in that day; days with no line pixels are missing (record gaps or occlusion).
Self-check: the digitised annual means must match the published annual means (Table 3.1 of the thesis:
19.6 for 2021, 22.7 for 2022) within digitisation error. Monthly means are also digitised from the triangles.

Input:  the figure image extracted from the paper PDF (page 6, second image)
Out:    data/external/nbro/nirmani2025_kandy_daily_digitised.csv, ..._monthly_digitised.csv, ..._check.json
"""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "external" / "nbro"
PAPER = glob.glob(str(REPO.parent / "references" / "papers" / "CLEAN Soil Air Water - 2025 - Nirmani*.pdf"))[0]
ROW_0, PX_PER_UG = 821.5, 53.0 / 40.0
X0, PX_PER_DAY = 110.0, 1260.0 / 365.0
PANEL = (712, 823)                       # Kandy panel plotting rows (80 down to 0)
PUBLISHED = {2021: 19.6, 2022: 22.7}


def load_image() -> np.ndarray:
    import fitz
    from PIL import Image
    import io
    d = fitz.open(PAPER)
    x = d[5].get_images()[1]
    im = Image.open(io.BytesIO(d.extract_image(x[0])["image"])).convert("RGB")
    return np.asarray(im).astype(int)


def masks(sub):
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    cyan = (b > 150) & (g > 150) & (r < 150) & (b - r > 60)            # 2021 line
    orange = (r > 190) & (g > 100) & (g < 200) & (b < 110) & (r - b > 110)  # 2022 line
    blue_tri = (b > 150) & (r < 90) & (g < 120)
    red_tri = (r > 150) & (g < 80) & (b < 80)
    return cyan, orange, blue_tri, red_tri


def daily(mask):
    rows = np.arange(PANEL[0], PANEL[1])
    vals = {}
    for x in range(int(X0), int(X0 + 365 * PX_PER_DAY)):
        col = mask[:, x]
        if col.sum() == 0:
            continue
        y = np.median(rows[col])
        day = int((x - X0) // PX_PER_DAY)
        vals.setdefault(day, []).append((ROW_0 - y) / PX_PER_UG)
    return {d: float(np.median(v)) for d, v in vals.items() if 0 <= d < 365}


def triangles(mask):
    """Centroids of triangle blobs -> (day, value); the triangle's apex sits near the plotted point, so use the
    blob centroid row as the marker centre."""
    from scipy import ndimage
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 25:
            continue
        y = ys.mean() + PANEL[0]; x = xs.mean()
        out.append(((x - X0) / PX_PER_DAY, (ROW_0 - y) / PX_PER_UG))
    return sorted(out)


def main():
    im = load_image()
    sub = im[PANEL[0]:PANEL[1]]
    cyan, orange, blue, red = masks(sub)
    OUT.mkdir(parents=True, exist_ok=True)
    rows, check = [], {}
    for year, m in ((2021, cyan), (2022, orange)):
        d = daily(m)
        dates = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(sorted(d), unit="D")
        s = pd.Series([d[k] for k in sorted(d)], index=dates)
        rows.append(pd.DataFrame({"date": s.index.date, "pm25_digitised": s.values, "year": year}))
        check[year] = dict(days=int(len(s)), digitised_mean=round(float(s.mean()), 2),
                           published_mean=PUBLISHED[year],
                           diff_pct=round(100 * (s.mean() - PUBLISHED[year]) / PUBLISHED[year], 1))
    D = pd.concat(rows, ignore_index=True)
    tri = [dict(year=2021, day=d, value=v) for d, v in triangles(blue)] + \
          [dict(year=2022, day=d, value=v) for d, v in triangles(red)]
    T = pd.DataFrame(tri)
    T["month"] = (pd.to_datetime(T.year.astype(str) + "-01-01") + pd.to_timedelta(T.day, unit="D")).dt.month
    for name, df in (("daily", D), ("monthly", T)):
        p = OUT / f"nirmani2025_kandy_{name}_digitised.csv"; tmp = p.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False); os.replace(tmp, p)
    p = OUT / "nirmani2025_kandy_check.json"
    p.write_text(json.dumps(check, indent=2), encoding="utf-8")
    print(json.dumps(check, indent=2)); print(f"monthly markers: {len(T)}")


if __name__ == "__main__":
    main()
