"""spatial_curve_freeze.py -- D3 of the spatial learning curve (OSF rqn4y, registered 2026-09-10).

Freezes the frame by the registered eligibility rule, applied to what the ingest downloaded. The
rule is Section 3 of docs/prereg_spatial_learning_curve_2026-09-11.md and is implemented here in
the order the registration states it:

  1. reference grade             (already so: only isMonitor locations were downloaded)
  2. 25 km clusters              (already so: carried from candidates.csv)
  3. merge stations within 100 m into one SITE, whose hourly value is the mean of its members
  4. UTC                         (already so: the ingest stored UTC)
  5. QC: [0, 1000), runs of > 24 identical hourly values removed; site mean in [5, 150]
  6. analysis window: the 365 consecutive UTC days maximising the number of sites present on
     >= 75 per cent of days, a day counting as present with >= 18 hourly values
  7. frames: primary >= 20 sites, secondary 15-19, band arm = |lat| < 23.5 with >= 12

THE STOP RULE is enforced, not merely printed: fewer than 10 primary cities exits with status 2.

WHY QC PRECEDES THE MERGE HERE, and why that is not a deviation. The registration lists the merge
(rule 3) before QC (rule 5). The hourly value checks in rule 5 are per-instrument properties -- a
stuck sensor is stuck whatever it is merged with -- so they are applied to each location before
its values enter a site mean. Merging first would let one stuck instrument dilute into a site mean
where the run-length test can no longer see it. The site-mean bound in rule 5 is applied after the
merge, as written.

⚠ OBJECT DATES ARE LOCAL. The archive names each object by the station's LOCAL calendar day, so
after conversion to UTC the first and last few hours of a download fall outside the nominal
window. Harmless: the download carries 60 days of margin either side, and the analysis window is
chosen in UTC days inside it, where a partial edge day fails the 18-hour rule on its own.

Usage: .venv/Scripts/python.exe scripts/spatial_curve_freeze.py
Out:   data/processed/modular/spatial_curve/frame_sites.csv
       data/processed/modular/spatial_curve/frame_daily.parquet
       data/processed/modular/spatial_curve/frame_cities.csv
       data/processed/modular/spatial_curve/frame_summary.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
SC = REPO / "data" / "processed" / "modular" / "spatial_curve"
RAW = SC / "raw"

# ── registered constants: do not tune ─────────────────────────────────────────────────────────
MERGE_M = 100.0
VAL_LO, VAL_HI = 0.0, 1000.0
STUCK_MAX = 24
MEAN_LO, MEAN_HI = 5.0, 150.0
WINDOW = 365
PRESENT_FRAC = 0.75
MIN_HOURS_PER_DAY = 18
PRIMARY, SECONDARY_LO, BAND_ARM = 20, 15, 12
TROPIC_LAT = 23.5
STOP_BELOW = 10


def qc_hourly(d: pd.DataFrame) -> pd.DataFrame:
    """Rule 5, per instrument: plausible range, then remove stuck runs."""
    d = d[(d.pm25 >= VAL_LO) & (d.pm25 < VAL_HI)].sort_values("datetime_utc")
    if d.empty:
        return d
    run = (d.pm25 != d.pm25.shift()).cumsum()
    return d[d.groupby(run).pm25.transform("size") <= STUCK_MAX]


def merge_sites(locs: pd.DataFrame) -> pd.Series:
    """Rule 3. Greedy merge at MERGE_M, deterministic: seeds taken in location_id order."""
    locs = locs.sort_values("location_id").reset_index(drop=True)
    la, lo = locs.lat.to_numpy(), locs.lon.to_numpy()
    lat0 = float(np.mean(la))
    sid = -np.ones(len(locs), int)
    c = 0
    for i in range(len(locs)):
        if sid[i] >= 0:
            continue
        d_m = 111_000 * np.hypot(la - la[i], (lo - lo[i]) * np.cos(np.radians(lat0)))
        sid[(d_m <= MERGE_M) & (sid < 0)] = c
        c += 1
    return pd.Series(sid, index=locs.location_id.to_numpy())


def best_window(pres: pd.DataFrame) -> tuple[pd.Timestamp | None, int]:
    """Rule 6. pres: daily boolean, index = every UTC day in range, columns = sites.

    Returns the START of the 365-day window maximising the count of sites present on at least
    75 per cent of its days. Ties resolve to the earliest start, so the choice is deterministic.
    """
    if len(pres) < WINDOW:
        return None, 0
    need = int(np.ceil(PRESENT_FRAC * WINDOW))
    counts = pres.astype(int).rolling(WINDOW, min_periods=WINDOW).sum()   # indexed by window END
    # only COMPLETE windows: the first WINDOW-1 rows are NaN for every site, since pres is
    # reindexed to the full day range and so has no gaps of its own
    ok = (counts >= need).sum(axis=1).iloc[WINDOW - 1:]
    best = int(ok.max())
    end = ok[ok == best].index[0]
    return end - pd.Timedelta(days=WINDOW - 1), best


def freeze_cluster(cl: int, rows: pd.DataFrame) -> tuple[list, list, dict]:
    locs = rows[["location_id", "lat", "lon"]].drop_duplicates("location_id")
    hourly = []
    for loc in locs.location_id:
        f = RAW / f"{int(loc)}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(f)
        if d.empty:
            continue
        d = qc_hourly(d)
        if not d.empty:
            d["location_id"] = int(loc)
            hourly.append(d)
    meta = dict(cluster=int(cl), band=rows.band.iloc[0], country=rows.country.iloc[0],
                lat=round(float(rows.lat.mean()), 4), lon=round(float(rows.lon.mean()), 4),
                locations_downloaded=len(locs), locations_with_data=len(hourly))
    if not hourly:
        return [], [], {**meta, "sites": 0, "reason": "no data"}

    H = pd.concat(hourly, ignore_index=True)
    present = locs[locs.location_id.isin(H.location_id.unique())]
    sid = merge_sites(present)
    H["site"] = H.location_id.map(sid)

    # site hourly value: mean of member instruments reporting that hour
    S = H.groupby(["site", "datetime_utc"], as_index=False).pm25.mean()
    S["day"] = S.datetime_utc.dt.floor("D")
    day = S.groupby(["site", "day"]).agg(pm25=("pm25", "mean"), hours=("pm25", "size")).reset_index()
    day = day[day.hours >= MIN_HOURS_PER_DAY]
    if day.empty:
        return [], [], {**meta, "sites": 0, "reason": "no day with >= 18 hours"}

    # endpoints are already UTC-aware; passing tz= as well can be refused as a conflict
    full = pd.date_range(day.day.min(), day.day.max(), freq="D")
    pres = day.pivot(index="day", columns="site", values="pm25").reindex(full).notna()
    w0, _ = best_window(pres)
    if w0 is None:
        return [], [], {**meta, "sites": 0, "reason": "record shorter than 365 days"}
    w1 = w0 + pd.Timedelta(days=WINDOW - 1)
    win = pres.loc[w0:w1]
    keep = win.columns[win.mean() >= PRESENT_FRAC]

    dw = day[day.site.isin(keep) & (day.day >= w0) & (day.day <= w1)]
    static = dw.groupby("site").pm25.mean()
    keep = static[(static >= MEAN_LO) & (static <= MEAN_HI)].index        # rule 5, site mean
    dw = dw[dw.site.isin(keep)]

    members = present.assign(site=present.location_id.map(sid))
    site_rows = []
    for s in keep:
        m = members[members.site == s]
        site_rows.append(dict(
            cluster=int(cl), site=f"{cl}_{int(s)}", lat=float(m.lat.mean()), lon=float(m.lon.mean()),
            n_members=len(m), member_location_ids="|".join(str(int(x)) for x in m.location_id),
            static_mean=float(static[s]), days_present=int(win[s].sum())))
    daily_rows = dw.assign(site=dw.site.map(lambda s: f"{cl}_{int(s)}"), cluster=int(cl))[
        ["cluster", "site", "day", "pm25"]]

    n = len(site_rows)
    tropics = abs(meta["lat"]) < TROPIC_LAT
    meta.update(sites_before_window=int(pres.shape[1]), sites=n,
                window_start=w0.date().isoformat(), window_end=w1.date().isoformat(),
                primary=n >= PRIMARY, secondary=SECONDARY_LO <= n < PRIMARY,
                band_arm=bool(tropics and n >= BAND_ARM))
    return site_rows, [daily_rows], meta


def main() -> int:
    global PRESENT_FRAC
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--present-frac", type=float, default=PRESENT_FRAC,
                    help="day-coverage threshold; 0.75 is the registered rule")
    ap.add_argument("--tag", default="", help="suffix for a sensitivity frame, e.g. s70")
    a = ap.parse_args()
    # A sensitivity run must never overwrite the registered frame's files.
    if not a.tag and a.present_frac != PRESENT_FRAC:
        raise SystemExit("a non-registered coverage threshold needs --tag, so the registered "
                         "frame files cannot be overwritten")
    PRESENT_FRAC = a.present_frac
    sfx = f"_{a.tag}" if a.tag else ""
    cand = pd.read_csv(SC / "candidates.csv")
    print(f"freezing {cand.cluster.nunique()} candidate clusters, {len(cand):,} locations\n")
    sites, daily, cities = [], [], []
    for cl, rows in cand.groupby("cluster"):
        s, d, m = freeze_cluster(int(cl), rows)
        sites += s
        daily += d
        cities.append(m)
        tag = ("PRIMARY" if m.get("primary") else "secondary" if m.get("secondary") else "")
        tag += (" +band" if m.get("band_arm") else "")
        print(f"  {int(cl):4d} {m['band']:13s} {m['country']}  sites {m.get('sites', 0):3d}  {tag}")

    C = pd.DataFrame(cities)
    # clusters that failed early carry no frame flags; guarantee the columns so that a run in
    # which EVERY cluster failed still reports that, instead of raising on a missing key
    for col in ("primary", "secondary", "band_arm"):
        C[col] = C[col].fillna(False).astype(bool) if col in C else False
    if "sites" not in C:
        C["sites"] = 0
    C.to_csv(SC / f"frame_cities{sfx}.csv", index=False)
    pd.DataFrame(sites).to_csv(SC / f"frame_sites{sfx}.csv", index=False)
    if daily:
        pd.concat(daily, ignore_index=True).to_parquet(SC / f"frame_daily{sfx}.parquet", index=False)

    prim, sec, arm = C[C.primary], C[C.secondary], C[C.band_arm]
    summary = dict(
        registration="OSF rqn4y", present_frac=PRESENT_FRAC, tag=a.tag or None,
        registered_rule=bool(PRESENT_FRAC == 0.75 and not a.tag),
        primary_cities=int(len(prim)), primary_sites=int(prim.sites.sum()) if len(prim) else 0,
        primary_countries=int(prim.country.nunique()) if len(prim) else 0,
        secondary_cities=int(len(sec)), band_arm_cities=int(len(arm)),
        band_arm=arm[["cluster", "country", "band", "sites"]].to_dict("records"),
        primary_bands=prim.band.value_counts().to_dict() if len(prim) else {},
        stop_rule_threshold=STOP_BELOW, stop=bool(len(prim) < STOP_BELOW))
    (SC / f"frame_summary{sfx}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nPRIMARY   {summary['primary_cities']} cities, {summary['primary_sites']} sites, "
          f"{summary['primary_countries']} countries  {summary['primary_bands']}")
    print(f"SECONDARY {summary['secondary_cities']} cities")
    print(f"BAND ARM  {summary['band_arm_cities']} cities: "
          f"{[(r['country'], r['sites']) for r in summary['band_arm']]}")
    if summary["stop"]:
        print(f"\nSTOP. Fewer than {STOP_BELOW} primary cities. The registered detection limits do "
              f"not hold; the analysis does not proceed. Report this.")
        return 2
    print(f"\nStop rule passed ({summary['primary_cities']} >= {STOP_BELOW}). Frame frozen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
