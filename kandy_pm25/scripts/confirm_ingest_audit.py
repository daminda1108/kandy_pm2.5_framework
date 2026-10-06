"""confirm_ingest_audit.py -- did the confirmation ingest silently lose daily files?

`ingest_openaq_sample.fetch_loc_year` skips any daily S3 object that fails to download or parse
(`except Exception: continue`), and returns None if a listing fails. A network drop therefore
looks like missing data. A plain count of listed objects against days present cannot tell loss
from legitimate absence: a location's daily file also exists on days it reported no PM2.5 (other
parameters only) or only invalid values. So, per city:

  1. re-list every (station, requested year) and take the file date from each key
     (`location-<id>-YYYYMMDD.csv.gz`); requested years = the city's last two years of coverage,
     exactly as `ios.city_years` chose them (the last year present in the parquet and the one before);
  2. "absent" = listed file dates with no hour of that station in the parquet within +-1 day
     (files are local-day, the parquet is UTC);
  3. download a random sample of up to 40 absent files and test whether each holds any PM2.5 value
     in (0, 1000). Estimated silent loss = absent x (valid fraction in sample) / listed.

Cities with an estimated loss above 1 % are re-fetched (delete the parquet, re-run the shard; same
frozen rule) and re-audited.

Usage: python scripts/confirm_ingest_audit.py [--cities a,b]
"""
from __future__ import annotations

import argparse
import gzip
import io
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import ingest_openaq_sample as ios                                      # noqa: E402

CD = REPO / "data" / "processed" / "modular" / "confirmation"
SAMPLE = 40


def _valid(s3, key: str) -> bool:
    body = s3.get_object(Bucket=ios.S3_BUCKET, Key=key)["Body"].read()
    with gzip.GzipFile(fileobj=io.BytesIO(body)) as f:
        d = pd.read_csv(f)
    if "parameter" in d.columns:
        d = d[d.parameter.astype(str).str.lower() == "pm25"]
    v = pd.to_numeric(d.get("value"), errors="coerce")
    return bool(((v > 0) & (v < 1000)).any())


def audit_city(f: Path, rng) -> dict:
    d = pd.read_parquet(f, columns=["station_id", "datetime_utc"])
    last = int(d.datetime_utc.dt.year.value_counts().loc[lambda s: s >= 30].index.max())
    years = [last - 1, last]
    s3 = ios.s3_client()
    tasks = [(int(s), y) for s in d.station_id.unique() for y in years]
    with ThreadPoolExecutor(16) as ex:
        keys = list(ex.map(lambda t: ios._list_year_keys(s3, *t), tasks))
    listed = [(t[0], k) for t, ks in zip(tasks, keys) for k in ks]
    L = pd.DataFrame(listed, columns=["station_id", "key"])
    L["day"] = pd.to_datetime(L.key.str.extract(r"-(\d{8})\.csv\.gz$")[0], format="%Y%m%d")
    L = L.dropna(subset=["day"]).drop_duplicates(["station_id", "day"])
    have = set(zip(d.station_id.astype(int), d.datetime_utc.dt.floor("D")))
    one = pd.Timedelta(days=1)
    absent = L[[not ({(s, t - one), (s, t), (s, t + one)} & have)
                for s, t in zip(L.station_id, L.day)]]
    samp = absent.sample(min(SAMPLE, len(absent)), random_state=rng) if len(absent) else absent
    with ThreadPoolExecutor(16) as ex:
        ok = list(ex.map(lambda k: _valid(s3, k), samp.key))
    frac = float(np.mean(ok)) if ok else 0.0
    return dict(city=f.stem, years=f"{years[0]}-{years[1]}", listed=len(L), absent=len(absent),
                sampled=len(samp), sampled_valid=int(sum(ok)),
                est_loss=len(absent) * frac / max(1, len(L)))


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--cities", default="")
    a = ap.parse_args()
    files = sorted((CD / "openaq").glob("*.parquet"))
    if a.cities:
        files = [f for f in files if f.stem in a.cities.split(",")]
    rows = []
    for i, f in enumerate(files):
        r = audit_city(f, 20260928 + i)
        rows.append(r)
        print(f"  {r['city']:<16} listed {r['listed']:>5} absent {r['absent']:>5} "
              f"sample valid {r['sampled_valid']}/{r['sampled']}  est. loss {100 * r['est_loss']:5.2f}%",
              flush=True)
    out = pd.DataFrame(rows)
    p = CD / "ingest_audit.csv"
    if a.cities and p.exists():
        old = pd.read_csv(p); out = pd.concat([old[~old.city.isin(out.city)], out], ignore_index=True)
    out.to_csv(p, index=False)
    print(f"\n{len(out)} cities; median est. loss {100 * out.est_loss.median():.2f}%, "
          f"max {100 * out.est_loss.max():.2f}%; cities > 1%: {list(out.city[out.est_loss > 0.01])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
