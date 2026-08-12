"""visibility_partial_correlation.py — is the airport-visibility corroboration
independent of the model's own drivers? (2026-08-06, reviewer point 4)

THE OBJECTION
-------------
The paper describes Colombo (VCBI) horizontal visibility as "a fully independent
check" that "enters the model nowhere". The VARIABLE does not enter the model. But
visibility is strongly controlled by relative humidity and precipitation, and ERA5
humidity and precipitation ARE model drivers. So the reported r = -0.46 may be partly
a correlation between two quantities with a shared meteorological cause rather than
evidence that the model identifies polluted days.

THE TEST
--------
Take humidity and precipitation from the SAME station and the same hours as the
visibility observation, and compute the partial correlation of model daily PM2.5
with visibility, controlling for them. If the association survives, the corroboration
is stronger than the raw number suggests, because it is then specific to the aerosol
rather than to the weather. If it collapses, the line must be withdrawn.

Two control sets are used. Humidity comes from the METAR itself, so it is measured at
the same place and time as the visibility. Precipitation and boundary-layer height come
from the model's OWN ERA5 drivers over Kandy, which is the conservative choice: it
removes exactly the variance the model uses, so anything surviving cannot be the shared
meteorological pathway the objection describes. (VCBI's own `p01i` field is unusable —
the station reports no precipitation at all in this archive, the same defect noted for
SKMD in gotcha #60 — so a METAR-only rain control would be vacuous.)

Run:  .venv/Scripts/python.exe scripts/visibility_partial_correlation.py
Out:  data/processed/decomp/visibility_partial_correlation.{csv,json}
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
YEAR = 2022
STATION = "VCBI"


def fetch(station: str, y: int) -> pd.DataFrame:
    """Daily means of visibility, relative humidity and precipitation at one ASOS."""
    url = (f"https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station={station}"
           f"&data=vsby&data=relh&data=p01i&data=tmpf"
           f"&year1={y}&month1=1&day1=1&year2={y}&month2=12&day2=31"
           f"&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&trace=T")
    r = subprocess.run(["curl", "-s", "--max-time", "180", url],
                       capture_output=True, text=True)
    df = pd.read_csv(io.StringIO(r.stdout))
    for c in ("vsby", "relh", "p01i", "tmpf"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["date"] = pd.to_datetime(df.valid, errors="coerce").dt.date
    g = df.groupby("date")
    out = pd.DataFrame({
        "visibility_km": g.vsby.mean() * 1.60934,
        "rh_pct": g.relh.mean(),
        "rain_mm": g.p01i.sum() * 25.4,          # inches -> mm, daily total
        "temp_c": (g.tmpf.mean() - 32.0) * 5.0 / 9.0,
    }).dropna(subset=["visibility_km"])
    return out


def model_drivers(y: int) -> pd.DataFrame:
    """The model's OWN ERA5 drivers over Kandy, daily: precipitation and BLH.

    Conditioning on these is the conservative form of the test -- it removes the very
    variance the model consumes, so a surviving association cannot be the shared
    meteorological pathway.
    """
    d = pd.read_parquet(REPO / "data" / "processed" / "stage1_v3" /
                        "dataset_v3_hourly.parquet",
                        columns=["datetime_utc", "tp", "blh_m"])
    d["date"] = pd.to_datetime(d.datetime_utc, utc=True).dt.tz_convert(
        "Asia/Colombo").dt.date
    g = d.groupby("date")
    return pd.DataFrame({"era5_tp": g.tp.mean(), "era5_blh": g.blh_m.mean()}).dropna()


def model_daily_pm(y: int) -> pd.Series:
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive_v2.parquet",
                        columns=["time", "pm25_q50"])
    d["date"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo").dt.date
    return d.groupby("date").pm25_q50.mean()


def partial_corr(x, y, Z):
    """Pearson partial correlation of x and y given the columns of Z."""
    from scipy import stats
    Z = np.column_stack([np.ones(len(x))] + [np.asarray(z, float) for z in Z])
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    r, _ = stats.pearsonr(rx, ry)
    n, k = len(x), Z.shape[1] - 1
    dof = n - k - 2
    t = r * np.sqrt(dof / max(1e-12, 1 - r ** 2))
    p = 2 * stats.t.sf(abs(t), dof)
    return float(r), float(p), int(dof)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from scipy.stats import pearsonr
    print(f"=== visibility corroboration: is it independent of the model's drivers? ===")
    met = fetch(STATION, YEAR)
    pm = model_daily_pm(YEAR)
    drv = model_drivers(YEAR)
    df = (met.join(pm.rename("model_pm25"), how="inner")
             .join(drv, how="inner")
             .dropna(subset=["visibility_km", "rh_pct", "model_pm25",
                             "era5_tp", "era5_blh"]))
    print(f"  {STATION} {YEAR}: n = {len(df)} days with visibility, RH, model PM "
          f"and the model's own ERA5 rain + BLH")

    x = df.model_pm25.values.astype(float)
    y = df.visibility_km.values.astype(float)
    r_raw, p_raw = pearsonr(x, y)
    print(f"\n  RAW           model PM vs visibility   r = {r_raw:+.3f}  p = {p_raw:.2e}")

    tests = {
        "control_rh": (["rh_pct"], "controlling station RH"),
        "control_era5_rain": (["era5_tp"], "controlling the model's ERA5 rain"),
        "control_rh_era5rain": (["rh_pct", "era5_tp"], "controlling RH + ERA5 rain"),
        "control_all": (["rh_pct", "era5_tp", "era5_blh", "temp_c"],
                        "controlling RH + rain + BLH + T"),
    }
    res = {"n_days": int(len(df)), "year": YEAR, "station": STATION,
           "raw_r": round(r_raw, 4), "raw_p": float(p_raw)}
    for key, (cols, label) in tests.items():
        r, p, dof = partial_corr(x, y, [df[c].values for c in cols])
        res[key] = {"r": round(r, 4), "p": float(p), "dof": dof}
        keep = 100 * r / r_raw
        print(f"  PARTIAL  {label:<26} r = {r:+.3f}  p = {p:.2e}   "
              f"({keep:.0f}% of the raw association retained)")

    # how much of visibility does weather alone explain?
    from scipy.stats import pearsonr as pr
    print(f"\n  context: visibility vs RH   r = {pr(y, df.rh_pct.values)[0]:+.3f}"
          f" | visibility vs ERA5 rain r = {pr(y, df.era5_tp.values)[0]:+.3f}")
    print(f"           model PM vs RH     r = {pr(x, df.rh_pct.values)[0]:+.3f}"
          f" | model PM vs ERA5 rain   r = {pr(x, df.era5_tp.values)[0]:+.3f}")

    key = res["control_all"]
    if key["p"] < 0.05 and abs(key["r"]) > 0.15:
        verdict = ("SURVIVES: the association is specific to the aerosol, not to shared "
                   "weather. The corroboration stands and should be reported as a PARTIAL "
                   "correlation, not the raw one.")
    elif key["p"] < 0.05:
        verdict = ("WEAKENED but significant: report the partial correlation and state "
                   "plainly that most of the raw association is shared meteorology.")
    else:
        verdict = ("COLLAPSES: the raw association is explained by shared humidity and "
                   "precipitation. This corroboration line must be WITHDRAWN from the paper.")
    res["verdict"] = verdict
    print(f"\n  VERDICT: {verdict}")

    df.to_csv(DEC / "visibility_partial_correlation.csv")
    (DEC / "visibility_partial_correlation.json").write_text(
        json.dumps(res, indent=1), encoding="utf-8")
    print(f"\nwrote visibility_partial_correlation.{{csv,json}}")


if __name__ == "__main__":
    main()
