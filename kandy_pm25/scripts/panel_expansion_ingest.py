"""panel_expansion_ingest.py — download PM2.5 for the 40 shortlisted non-Chinese cities
from the PUBLIC OpenAQ S3 archive (unsigned; no API key, no API spend — gotcha #35),
aggregate to a city daily mean, and apply the remaining pre-registered criteria
E2 (completeness), E4 (magnitude sanity), E5 (QC), E6 (sensor grade).

Criteria are fixed in docs/panel_expansion_eligibility_2026-07-26.md. No model is run.

Resumable: per-city parquet cached under openaq_census/daily/; re-running skips done cities.

Out: data/processed/cnemc_panel/openaq_census/daily/{slug}.parquet
     data/processed/cnemc_panel/panel_expansion_ingested.csv   (E2/E4/E5/E6 verdicts)
"""
from __future__ import annotations

import io as _io
import gzip
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
CEN = REPO / "data" / "processed" / "cnemc_panel" / "openaq_census"
DAILY = CEN / "daily"
DAILY.mkdir(parents=True, exist_ok=True)
OUT = REPO / "data" / "processed" / "cnemc_panel" / "panel_expansion_ingested.csv"

BUCKET = "openaq-data-archive"
PREFIX = "records/csv.gz/locationid={loc}/"

# --- pre-registered thresholds (do not tune) ---
E2_COMPLETENESS = 0.60      # >=60% of days present in span
E4_LO, E4_HI = 5.0, 150.0   # annual mean sanity bound, ug/m3
E5_STUCK_MAX = 24           # >24 identical consecutive hourly values = stuck sensor
E5_EXTREME = 1000.0         # ug/m3, physically implausible
MIN_STATIONS_PER_DAY = 3    # a city-day needs >=3 reporting stations (consistent with E3)


def s3_client():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client("s3", config=Config(signature_version=UNSIGNED))


def fetch_location(s3, loc_id: int) -> pd.DataFrame:
    """Pull every csv.gz for one location. Returns hourly rows or empty frame."""
    keys = []
    tok = None
    while True:
        kw = {"Bucket": BUCKET, "Prefix": PREFIX.format(loc=loc_id), "MaxKeys": 1000}
        if tok:
            kw["ContinuationToken"] = tok
        r = s3.list_objects_v2(**kw)
        keys += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            break
        tok = r.get("NextContinuationToken")
    if not keys:
        return pd.DataFrame()
    parts = []
    for k in keys:
        try:
            body = s3.get_object(Bucket=BUCKET, Key=k)["Body"].read()
            d = pd.read_csv(_io.BytesIO(gzip.decompress(body)))
            parts.append(d)
        except Exception:
            continue
    if not parts:
        return pd.DataFrame()
    d = pd.concat(parts, ignore_index=True)
    pc = next((c for c in d.columns if c.lower() == "parameter"), None)
    if pc is not None:
        d = d[d[pc].astype(str).str.lower() == "pm25"]
    return d


def qc_e5(d: pd.DataFrame, vcol: str) -> pd.DataFrame:
    """E5: drop stuck runs and physically implausible values."""
    d = d[(d[vcol] >= 0) & (d[vcol] < E5_EXTREME)].copy()
    if d.empty:
        return d
    d = d.sort_values("dt")
    run = (d[vcol] != d[vcol].shift()).cumsum()
    sizes = d.groupby(run)[vcol].transform("size")
    return d[sizes <= E5_STUCK_MAX]


def main() -> int:
    sel = pd.read_csv(REPO / "data/processed/cnemc_panel/panel_expansion_shortlist.csv")
    lc = pd.read_csv(CEN / "locations_clustered.csv")
    s3 = s3_client()

    rows = []
    for i, r in sel.reset_index(drop=True).iterrows():
        slug = f"{r.iso}_{int(r.cluster)}"
        cache = DAILY / f"{slug}.parquet"
        print(f"[{i+1}/{len(sel)}] {slug} {r.country}", flush=True)

        if cache.exists():
            day = pd.read_parquet(cache)
        else:
            locs = lc[lc.cluster == r.cluster]
            # E6: reference-grade monitors only (LCS needs a calibration we do not have
            # for arbitrary networks; excluding them is stricter, not looser)
            if "is_monitor" in locs.columns:
                locs = locs[locs.is_monitor == True]  # noqa: E712
            if locs.empty:
                rows.append({"slug": slug, "iso": r.iso, "country": r.country,
                             "eligible": False, "fail": "E6_no_reference_monitor"})
                continue
            frames = []
            for lid in locs.loc_id.tolist():
                d = fetch_location(s3, int(lid))
                if d.empty:
                    continue
                dtc = next((c for c in d.columns if "datetime" in c.lower()), None)
                vc = next((c for c in d.columns if c.lower() == "value"), None)
                if dtc is None or vc is None:
                    continue
                d["dt"] = pd.to_datetime(d[dtc], errors="coerce", utc=True)
                d = d.dropna(subset=["dt", vc])
                d = qc_e5(d, vc)
                if d.empty:
                    continue
                frames.append(pd.DataFrame({"dt": d.dt, "v": d[vc], "loc": int(lid)}))
            if not frames:
                rows.append({"slug": slug, "iso": r.iso, "country": r.country,
                             "eligible": False, "fail": "no_data_after_E5"})
                continue
            h = pd.concat(frames, ignore_index=True)
            h["date"] = h.dt.dt.tz_convert("UTC").dt.tz_localize(None).dt.floor("D")
            g = h.groupby("date").agg(pm25=("v", "mean"), n_stn=("loc", "nunique"))
            day = g[g.n_stn >= MIN_STATIONS_PER_DAY].reset_index()
            day.to_parquet(cache, index=False)

        if day.empty:
            rows.append({"slug": slug, "iso": r.iso, "country": r.country,
                         "eligible": False, "fail": "no_qualifying_city_days"})
            continue

        span = (day.date.max() - day.date.min()).days + 1
        comp = len(day) / max(span, 1)
        ann = float(day.pm25.mean())
        e2 = comp >= E2_COMPLETENESS
        e4 = E4_LO <= ann <= E4_HI
        fail = "" if (e2 and e4) else (";".join(
            ([] if e2 else ["E2_completeness"]) + ([] if e4 else ["E4_magnitude"])))
        rows.append({"slug": slug, "iso": r.iso, "country": r.country,
                     "lat": r.lat if "lat" in sel.columns else np.nan,
                     "lon": r.lon if "lon" in sel.columns else np.nan,
                     "n_days": len(day), "span_days": span,
                     "completeness": round(comp, 3), "annual_mean": round(ann, 2),
                     "median_stations": int(day.n_stn.median()),
                     "date_first": str(day.date.min().date()),
                     "date_last": str(day.date.max().date()),
                     "eligible": bool(e2 and e4), "fail": fail})
        pd.DataFrame(rows).to_csv(OUT, index=False)

    res = pd.DataFrame(rows)
    res.to_csv(OUT, index=False)
    ok = res[res.eligible == True]  # noqa: E712
    print(f"\n=== INGEST COMPLETE ===")
    print(f"attempted   : {len(res)}")
    print(f"ELIGIBLE    : {len(ok)}  across {ok.iso.nunique()} countries")
    if len(res) > len(ok):
        print("exclusions by criterion:")
        for k, v in res[res.eligible != True].fail.value_counts().items():
            print(f"  {k}: {v}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
