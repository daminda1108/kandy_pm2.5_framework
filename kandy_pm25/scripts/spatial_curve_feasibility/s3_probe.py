"""Measure what one reference station costs to pull from the public OpenAQ archive.

Picks a Bangkok reference station from the discovery file, lists its S3 keys (unsigned, no
API spend, gotcha #35), and reports object count, bytes, and bytes per station-year. Downloads
ONE daily file to confirm the schema and the value column. Nothing else is written.
"""
import gzip
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(r"D:\ProjectCD\kandy_pm25")
d = pd.read_csv(REPO / "data/external/openaq/discovery/global_locations.csv")
d = d[d.is_monitor & (d.country == "TH")].copy()
lat0, lon0 = 13.749, 100.557
d["km"] = 111 * np.hypot(d.lat - lat0, (d.lon - lon0) * np.cos(np.radians(lat0)))
d = d[d.km < 25].sort_values("km")
print(f"Bangkok reference stations within 25 km in discovery: {len(d)}")
loc = int(d.iloc[0].id)
print(f"probing location {loc}: {d.iloc[0]['name']} ({d.iloc[0]['first']} to {d.iloc[0]['last']})")

import boto3
from botocore import UNSIGNED
from botocore.config import Config

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
keys, size, token = [], 0, None
while True:
    kw = {"Bucket": "openaq-data-archive", "Prefix": f"records/csv.gz/locationid={loc}/",
          "MaxKeys": 1000}
    if token:
        kw["ContinuationToken"] = token
    r = s3.list_objects_v2(**kw)
    for o in r.get("Contents", []):
        keys.append(o["Key"]); size += o["Size"]
    if not r.get("IsTruncated"):
        break
    token = r["NextContinuationToken"]

years = sorted({k.split("year=")[1][:4] for k in keys if "year=" in k})
print(f"objects {len(keys):,} | total {size / 1e6:.1f} MB | years {years[0]}..{years[-1]} "
      f"({len(years)}) | {size / 1e6 / max(1, len(years)):.2f} MB per station-year")

body = s3.get_object(Bucket="openaq-data-archive", Key=keys[-1])["Body"].read()
df = pd.read_csv(io.BytesIO(gzip.decompress(body)))
print(f"\nsample object {keys[-1].split('/')[-1]}: {len(df)} rows")
print(f"columns: {df.columns.tolist()}")
print(df[df.parameter.eq('pm25')].head(3).to_string() if "parameter" in df else df.head(3))
