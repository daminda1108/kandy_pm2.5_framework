"""
Panel expansion — CANDIDATE INVENTORY (data-availability census only).

Integrity: cities are screened on DATA QUALITY ONLY, blind to model performance.
See docs/panel_expansion_eligibility_2026-07-26.md. NO model is run, fitted or scored here.

Step 1: enumerate every OpenAQ PM2.5 location worldwide (paginated /v3/locations).
Step 2: cluster locations into "cities" (country + spatial clustering ~25 km).
Step 3: for clusters that could plausibly pass E1/E3, pull per-sensor coverage+summary
        (/v3/sensors/{id}) to estimate span, completeness and annual mean.
Step 4: apply E1-E7 and write the inventory CSV.

Usage:
  python scripts/panel_expansion_census.py --stage enumerate
  python scripts/panel_expansion_census.py --stage sensors
  python scripts/panel_expansion_census.py --stage screen
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).parents[1]
OUT_DIR = ROOT / "data" / "processed" / "cnemc_panel"
CACHE = OUT_DIR / "openaq_census"
CACHE.mkdir(parents=True, exist_ok=True)

API = "https://api.openaq.org/v3"
PM25 = 2


def key() -> str:
    for line in (ROOT.parent / "API.txt").read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("openaq"):
            return line.split(":", 1)[1].strip()
    raise SystemExit("no OpenAQ key")


HEAD = {"X-API-Key": key()}


def get(url, params=None, tries=5):
    """GET with rate-limit awareness. OpenAQ free tier = 60 requests / 60 s window;
    we read X-Ratelimit-Remaining/Reset and pause rather than eating 429 penalties."""
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEAD, params=params, timeout=90)
        except Exception as e:  # noqa
            time.sleep(2 + 3 * i)
            continue
        try:
            rem = int(r.headers.get("X-Ratelimit-Remaining", "99"))
            rst = int(r.headers.get("X-Ratelimit-Reset", "0"))
            if rem <= 2 and rst > 0:
                time.sleep(rst + 1)
        except Exception:
            pass
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(10 + 10 * i)
            continue
        if r.status_code in (404, 410):
            return None
        time.sleep(2 + 3 * i)
    return None


# ----------------------------------------------------------------- stage 1
def enumerate_locations():
    out = CACHE / "locations_pm25.json"
    rows, page = [], 1
    while True:
        d = get(f"{API}/locations", {"parameters_id": PM25, "limit": 1000, "page": page})
        if d is None:
            print(f"  page {page}: request failed, stopping")
            break
        res = d.get("results", [])
        if not res:
            break
        rows.extend(res)
        print(f"  page {page}: +{len(res)} (total {len(rows)})", flush=True)
        if len(res) < 1000:
            break
        page += 1
        time.sleep(0.4)
    out.write_text(json.dumps(rows), encoding="utf-8")
    print(f"wrote {len(rows)} locations -> {out}")


# ----------------------------------------------------------------- stage 2
def flatten() -> pd.DataFrame:
    raw = json.loads((CACHE / "locations_pm25.json").read_text(encoding="utf-8"))
    recs = []
    for L in raw:
        c = L.get("coordinates") or {}
        if c.get("latitude") is None:
            continue
        pm_sensors = [s for s in (L.get("sensors") or [])
                      if (s.get("parameter") or {}).get("id") == PM25]
        if not pm_sensors:
            continue
        recs.append(dict(
            loc_id=L["id"],
            name=L.get("name"),
            locality=L.get("locality"),
            country=(L.get("country") or {}).get("name"),
            iso=(L.get("country") or {}).get("code"),
            provider=(L.get("provider") or {}).get("name"),
            is_monitor=bool(L.get("isMonitor")),
            is_mobile=bool(L.get("isMobile")),
            lat=c["latitude"], lon=c["longitude"],
            sensor_id=pm_sensors[0]["id"],
            dt_first=(L.get("datetimeFirst") or {}).get("utc") if isinstance(L.get("datetimeFirst"), dict) else L.get("datetimeFirst"),
            dt_last=(L.get("datetimeLast") or {}).get("utc") if isinstance(L.get("datetimeLast"), dict) else L.get("datetimeLast"),
        ))
    return pd.DataFrame(recs)


def cluster(df: pd.DataFrame, radius_km: float = 25.0) -> pd.DataFrame:
    """Greedy single-link-ish clustering within a country: seed at densest point."""
    from sklearn.cluster import DBSCAN
    df = df.copy()
    df["cluster"] = -1
    cid = 0
    for iso, g in df.groupby("iso"):
        if len(g) == 0:
            continue
        X = np.radians(g[["lat", "lon"]].to_numpy())
        db = DBSCAN(eps=radius_km / 6371.0, min_samples=1, metric="haversine").fit(X)
        lab = db.labels_
        df.loc[g.index, "cluster"] = lab + cid
        cid += lab.max() + 1
    return df


# ----------------------------------------------------------------- stage 3
def fetch_sensors(sensor_ids):
    out = CACHE / "sensors.json"
    have = {}
    if out.exists():
        have = json.loads(out.read_text(encoding="utf-8"))
    todo = [s for s in sensor_ids if str(s) not in have]
    print(f"sensors: {len(have)} cached, {len(todo)} to fetch")
    for i, sid in enumerate(todo):
        d = get(f"{API}/sensors/{sid}")
        have[str(sid)] = (d or {}).get("results", [None])[0] if d else None
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(todo)}", flush=True)
            out.write_text(json.dumps(have), encoding="utf-8")
    out.write_text(json.dumps(have), encoding="utf-8")
    return have


def max_concurrent(t0s, t1s):
    ev = sorted([(t, 1) for t in t0s] + [(t, -1) for t in t1s])
    n = best = 0
    for _, delta in ev:
        n += delta
        best = max(best, n)
    return best


def longest_window_ge(t0s, t1s, k):
    """Longest continuous window with >= k stations active. Returns (days, w0, w1)."""
    ev = sorted([(t, 1) for t in t0s] + [(t, -1) for t in t1s])
    n, best, start, w0, w1 = 0, pd.Timedelta(0), None, None, None
    for t, delta in ev:
        prev = n
        n += delta
        if prev < k <= n:
            start = t
        elif prev >= k > n and start is not None:
            if t - start > best:
                best, w0, w1 = t - start, start, t
            start = None
    return best.days, w0, w1


def prescreen(min_stations=3, min_span_days=730):
    """Cluster and pre-screen on LOCATION-level metadata (cheap, no extra API calls).

    Criteria applied LITERALLY as written in the eligibility doc:
      E1 - the city's record span (first obs to last obs) >= 2 years
      E3 - at least 3 stations report CONCURRENTLY at some point
    These are separate conditions; the doc does not require 3 stations throughout the
    2 years. The stricter joint version is reported later as an informational column.
    Location datetimeFirst/Last is an upper bound on the PM2.5 sensor window ->
    permissive here on purpose; the sensor stage tightens it.
    """
    d = pd.read_csv(CACHE / "locations_flat.csv")
    n0 = len(d)
    d = d[d.iso != "CN"]                       # mainland China already in the panel
    n_cn = n0 - len(d)
    d = d[~d.is_mobile]                        # mobile sensors are not city stations
    d = d[d.dt_first.notna() & d.dt_last.notna()]
    d["t0"] = pd.to_datetime(d.dt_first, utc=True, errors="coerce")
    d["t1"] = pd.to_datetime(d.dt_last, utc=True, errors="coerce")
    d = d.dropna(subset=["t0", "t1"])
    d = cluster(d)
    print(f"{n0} locations | -{n_cn} CN | {len(d)} usable | {d.cluster.nunique()} clusters")

    keep = []
    for cid, g in d.groupby("cluster"):
        if len(g) < min_stations:
            continue
        conc = max_concurrent(list(g.t0), list(g.t1))
        span_days = (g.t1.max() - g.t0.min()).days
        if conc >= min_stations and span_days >= min_span_days:
            keep.append(dict(cluster=cid, iso=g.iso.iloc[0], country=g.country.iloc[0],
                             n_loc=len(g), max_concurrent=conc,
                             lat=g.lat.mean(), lon=g.lon.mean(),
                             win_start=g.t0.min(), win_end=g.t1.max(), win_days=span_days))
    cl = pd.DataFrame(keep).sort_values(["iso", "n_loc"], ascending=[True, False])
    d.to_csv(CACHE / "locations_clustered.csv", index=False)
    cl.to_csv(CACHE / "clusters_prescreen.csv", index=False)
    print(f"pre-passing clusters: {len(cl)} across {cl.iso.nunique()} countries")
    print(cl.iso.value_counts().head(40))
    print("stations to fetch:", d[d.cluster.isin(cl.cluster)].groupby("cluster").size().clip(upper=20).sum())
    return cl


# ----------------------------------------------------------------- stage 4
REFERENCE_PROVIDERS = {
    "AirNow", "EEA", "CPCB", "Air4Thai", "Sinaica Mexico", "South Africa",
    "Chile - SINCA", "Korea Air Ministry of Environment", "US EPA AirNow",
    "Ministry of the Environment Air Pollutant Wide Area Monitoring System",
    "Türkiye", "T�rkiye", "Environment and Climate Change Canada",
    "DEFRA", "Japan Ministry of the Environment", "MET Norway",
}
LCS_PROVIDERS = {"AirGradient", "Clarity", "PurpleAir", "HabitatMap", "Hawanama",
                 "Sensor.Community", "IQAir"}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def _interval_hours(s):
    if not s:
        return np.nan
    try:
        h, m, sec = str(s).split(":")
        return int(h) + int(m) / 60 + int(sec) / 3600
    except Exception:
        return np.nan


def screen():
    d = pd.read_csv(CACHE / "locations_clustered.csv")
    cl = pd.read_csv(CACHE / "clusters_prescreen.csv")
    sens = json.loads((CACHE / "sensors.json").read_text(encoding="utf-8"))
    d = d[d.cluster.isin(cl.cluster)].copy()
    d["t0"] = pd.to_datetime(d.t0, utc=True)
    d["t1"] = pd.to_datetime(d.t1, utc=True)

    # attach sensor facts
    rows = []
    for _, r in d.iterrows():
        S = sens.get(str(int(r.sensor_id)))
        if not S:
            continue
        cov = S.get("coverage") or {}
        smy = S.get("summary") or {}
        t0 = ((S.get("datetimeFirst") or {}) or {}).get("utc")
        t1 = ((S.get("datetimeLast") or {}) or {}).get("utc")
        if not t0 or not t1:
            continue
        ih = _interval_hours(cov.get("expectedInterval"))
        obs = cov.get("observedCount")
        rows.append(dict(cluster=r.cluster, iso=r.iso, country=r.country, loc_id=r.loc_id,
                         name=r["name"], provider=r.provider, is_monitor=bool(r.is_monitor),
                         lat=r.lat, lon=r.lon,
                         t0=pd.Timestamp(t0), t1=pd.Timestamp(t1),
                         obs_h=(obs * ih) if (obs and ih == ih) else np.nan,
                         avg=smy.get("avg"), vmin=smy.get("min"), vmax=smy.get("max")))
    S = pd.DataFrame(rows)
    S["span_h"] = (S.t1 - S.t0).dt.total_seconds() / 3600
    S["compl"] = (S.obs_h / S.span_h).clip(upper=1.0)

    out = []
    for cid, gall in d.groupby("cluster"):
        # medoid + 25 km cut (guards DBSCAN single-link chaining across a conurbation)
        lat0, lon0 = gall.lat.median(), gall.lon.median()
        dist = haversine(lat0, lon0, gall.lat.values, gall.lon.values)
        extent = float(np.nanmax(dist)) if len(dist) else 0.0
        gall = gall[dist <= 25.0]
        if len(gall) == 0:
            continue
        g = S[S.cluster == cid]          # the <=10 sampled stations with sensor detail
        g = g[haversine(lat0, lon0, g.lat.values, g.lon.values) <= 25.0] if len(g) else g

        # --- E1/E3, applied literally and independently --------------------
        # station count/spans come from the FULL location list (no sampling bias)
        n_conc = max_concurrent(list(gall.t0), list(gall.t1))
        w0, w1 = gall.t0.min(), gall.t1.max()
        span_days = (w1 - w0).days
        span_years = span_days / 365.25
        # informational only (a stricter reading of E1+E3 combined)
        d3_days, _, _ = longest_window_ge(list(gall.t0), list(gall.t1), 3)

        c = g.compl.dropna()
        union = float(1 - np.prod(1 - c.values)) if len(c) else np.nan
        mean_c = float(c.mean()) if len(c) else np.nan
        mag = float(g.avg.dropna().median()) if len(g) and g.avg.notna().any() else np.nan

        prov = gall.provider.value_counts()
        n_ref = int(gall.is_monitor.sum())
        grade = ("reference" if n_ref >= 3 else "mixed" if n_ref >= 1 else "lcs")
        vmax_ok = bool(g.vmax.dropna().lt(2000).all()) if len(g) and g.vmax.notna().any() else None

        e1 = span_days >= 730
        e2 = (union >= 0.60) if union == union else None
        e3 = n_conc >= 3
        e4 = (5.0 <= mag <= 150.0) if mag == mag else None
        e5 = vmax_ok                     # provisional: full stuck-run QC needs the data pull
        e6 = grade in ("reference", "mixed")
        e7 = True                        # ERA5-Land + GEOS-CF are global over land

        notes = []
        if extent > 60:
            notes.append(f"raw cluster extent {extent:.0f}km, trimmed to 25km of medoid")
        if grade == "mixed":
            notes.append(f"{n_ref}/{len(gall)} reference-grade; LCS calibratable against them")
        if grade == "lcs":
            notes.append("LCS-only, no co-located reference -> no derivable calibration (E6 fail)")
        if e2 is False:
            notes.append("union completeness below 60%")
        if d3_days < 730:
            notes.append(f"only {d3_days}d with >=3 stations concurrent (E1+E3 jointly would fail)")
        notes.append("E2 = union-of-stations ESTIMATE from sensor coverage counts, not a data pull")
        notes.append("E5 provisional: value-range check only; stuck-run QC deferred to ingest")
        if len(g) == 0:
            notes.append("UNCERTAIN: no sensor detail retrieved; E2/E4/E5 not assessed")

        out.append(dict(
            cluster=cid, iso=gall.iso.iloc[0], country=gall.country.iloc[0],
            lat=round(float(gall.lat.mean()), 4), lon=round(float(gall.lon.mean()), 4),
            n_stations=int(len(gall)), n_concurrent_max=n_conc, n_reference=n_ref,
            date_first=str(w0.date()), date_last=str(w1.date()),
            span_years=round(span_years, 2),
            days_with_ge3_stations=int(d3_days),
            completeness_pct=round(100 * union, 1) if union == union else np.nan,
            mean_station_completeness_pct=round(100 * mean_c, 1) if mean_c == mean_c else np.nan,
            annual_mean_ugm3=round(mag, 1) if mag == mag else np.nan,
            sensor_grade=grade, providers="|".join(prov.index[:3]),
            n_sampled_for_quality=int(len(g)), extent_km=round(extent, 1),
            E1=e1, E2=e2, E3=e3, E4=e4, E5=e5, E6=e6, E7=e7,
            eligible=bool(e1 and e2 and e3 and (e4 is True) and (e5 is True) and e6 and e7),
            notes="; ".join(notes)))

    R = pd.DataFrame(out).sort_values(["eligible", "iso", "n_stations"],
                                      ascending=[False, True, False])
    R.to_csv(CACHE / "screened_raw.csv", index=False)
    print(f"screened clusters: {len(R)}  eligible: {int(R.eligible.sum())} "
          f"across {R[R.eligible].iso.nunique()} countries")
    for k in ["E1", "E2", "E3", "E4", "E5", "E6"]:
        print(f"  fail {k}: {int((R[k] == False).sum())}   unknown: {int(R[k].isna().sum())}")
    print(R[R.eligible].iso.value_counts())
    return R


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    a = ap.parse_args()
    if a.stage == "enumerate":
        enumerate_locations()
    elif a.stage == "flatten":
        d = flatten()
        d.to_csv(CACHE / "locations_flat.csv", index=False)
        print(d.shape, d.iso.nunique(), "countries")
        print(d.iso.value_counts().head(30))
    elif a.stage == "prescreen":
        prescreen()
    elif a.stage == "sensors":
        d = pd.read_csv(CACHE / "locations_clustered.csv")
        cl = pd.read_csv(CACHE / "clusters_prescreen.csv")
        d = d[d.cluster.isin(cl.cluster)].copy()
        d["span"] = pd.to_datetime(d.t1, utc=True) - pd.to_datetime(d.t0, utc=True)
        # Sample <=10 stations per cluster for the quality metrics (API rate limit is
        # ~60 req/min). Station COUNT still comes from the full location list; only the
        # completeness/magnitude estimates use this sample. Ordering is by data quality
        # (reference-grade first, then longest record) -- never by anything model-related.
        d = (d.sort_values(["is_monitor", "span"], ascending=False)
               .groupby("cluster").head(10))
        fetch_sensors(d.sensor_id.astype(int).tolist())
    elif a.stage == "screen":
        screen()
