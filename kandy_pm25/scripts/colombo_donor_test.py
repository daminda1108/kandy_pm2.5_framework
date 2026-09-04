"""Is Colombo a usable regional-background donor for Kandy?  (ledger F.63, re-run 2026-09-04)

WHY THIS EXISTS TWICE. The test was run once, reported in the ledger and quoted in the paper
(93 km, r = 0.604, against a benchmark of 0.923) and its output was never written to a file.
An uncomputed number in a manuscript is exactly what `build_claims.py` exists to prevent, so it
is re-run here and its result emitted, rather than the three literals being trusted.

THE QUESTION. §4 measures the regional-background rung as the largest single gain in the
programme. Kandy has no regional station. Sri Lanka's only reference-grade record inside the
admissible 30-300 km donor window is the US Embassy monitor in Colombo. If Colombo tracks Kandy
day to day as well as a typical donor tracks its target, the cheapest acquisition on the ladder
is already free. If it does not, the rung stays unbought.

THE COMPARISON. A correlation is meaningless without a scale, so Colombo is scored against the
same quantity computed for every panel donor pair: the daily correlation between the target
city's held-out stations and the donor city's daily 10th percentile, over their common days.
The panel pairs are re-derived here from the same seed and the same station-holdout as
`independent_background.py`, so the benchmark is the distribution this project actually built
and not a number remembered from one.

⚠ ATTENUATION. Kandy's series is two low-cost sensors and the panel's targets are mostly
reference networks, so Kandy's correlation is attenuated by measurement error the panel pairs do
not carry. The disattenuated value is reported alongside the raw one and BOTH are emitted; the
conclusion has to survive the generous version to be worth stating.

Usage: .venv/Scripts/python.exe scripts/colombo_donor_test.py
Out:   data/processed/modular/colombo_donor_test.csv
       data/processed/paper_figures/colombo_donor.json   (read by build_claims.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from figdata import emit                                   # noqa: E402
import modular_validation_all as mv                        # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
SEED = 0                     # the seed independent_background.py was built with
MIN_COMMON_DAYS = 120        # same threshold as the donor search
BAND_KM = 30.0               # half-width of the distance-matched benchmark band

# Donor separation is a CITY-to-city quantity: every panel pair is measured between city
# coordinates, so Kandy must be too or the comparison is not like for like. Kandy city centre,
# not the sensor mean -- the two FECT sensors sit 91.7 and 96.4 km from Colombo and averaging
# their positions would silently redefine the statistic for one row of the table.
KANDY_CENTRE = (7.2906, 80.6337)

# Kandy's two FECT sensors. Reliability for the disattenuation is their between-sensor
# correlation on common days -- measured below, never assumed.
KANDY_OBS = REPO / "data" / "processed" / "stage1_v3" / "dataset_v3_hourly.parquet"
COLOMBO = REPO / "data" / "processed" / "stage1_v2" / "dataset_v2_colombo_daily.parquet"


def haversine(a_lat, a_lon, b_lat, b_lon):
    r = 6371.0
    p1, p2 = np.radians(a_lat), np.radians(b_lat)
    dp, dl = p2 - p1, np.radians(b_lon - a_lon)
    h = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(h))


def kandy_daily() -> tuple[pd.Series, float, float, float]:
    """Kandy daily mean PM2.5 from the FECT sensors, plus their mean position and reliability."""
    d = pd.read_parquet(KANDY_OBS, columns=["datetime_utc", "sensor_id", "pm25_observed",
                                            "lat", "lon"])
    d = d.dropna(subset=["pm25_observed"])
    d["date"] = pd.to_datetime(d.datetime_utc).dt.tz_localize(None).dt.floor("D")

    # reliability: how well do the two sensors agree with each other on common days? That is
    # the ceiling any correlation with Kandy can reach, and it sets the disattenuation.
    per = d.groupby(["date", "sensor_id"]).pm25_observed.mean().unstack()
    rel = np.nan
    if per.shape[1] >= 2:
        pair = per.dropna()
        if len(pair) >= 30:
            rel = float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))

    daily = d.groupby("date").pm25_observed.mean()
    return daily, float(d.lat.mean()), float(d.lon.mean()), rel


def colombo_daily() -> tuple[pd.Series, float, float]:
    c = pd.read_parquet(COLOMBO, columns=["date", "pm25_observed", "lat", "lon"])
    c["date"] = pd.to_datetime(c.date).dt.tz_localize(None).dt.floor("D")
    return (c.groupby("date").pm25_observed.mean(), float(c.lat.iloc[0]), float(c.lon.iloc[0]))


def panel_benchmark() -> pd.DataFrame:
    """Re-derive the daily target-donor correlation for every panel pair that has a donor."""
    ib = pd.read_csv(MOD / "independent_background.csv")
    ib = ib[ib.status == "ok"]
    sample = pd.read_csv(MOD / "validation_sample.csv")
    sample["cid"] = np.where(sample.src == "OpenAQ",
                             sample.cluster.fillna(-1).astype(int).astype(str),
                             sample.slug.astype(str))
    src = sample.set_index("cid").src.to_dict()

    rng_master = np.random.default_rng(SEED)
    rows = []
    for r in ib.itertuples():
        cid, dcid = str(r.city), str(r.donor)
        try:
            st = (mv.stations_openaq(int(cid)) if src.get(cid) == "OpenAQ"
                  else mv.stations_cnemc(cid))
            ds = (mv.stations_openaq(int(dcid)) if src.get(dcid) == "OpenAQ"
                  else mv.stations_cnemc(dcid))
        except Exception as e:                                     # noqa: BLE001
            rows.append(dict(city=cid, donor=dcid, d_km=r.d_km, r=np.nan, n=0, why=str(e)[:60]))
            continue
        if st is None or ds is None or st.empty or ds.empty:
            rows.append(dict(city=cid, donor=dcid, d_km=r.d_km, r=np.nan, n=0, why="empty"))
            continue

        # identical holdout to independent_background.py: same seed, same shuffle, same split
        rng = np.random.default_rng(SEED)
        ids = np.array(sorted(st.station_id.unique()))
        rng.shuffle(ids)
        held = ids[:max(3, len(ids) // 3)]
        obs = st[st.station_id.isin(held)].groupby("date").pm25.mean().rename("obs")
        bg = ds.groupby("date").pm25.quantile(0.10).rename("bg")
        j = pd.concat([obs, bg], axis=1).dropna()
        if len(j) < MIN_COMMON_DAYS:
            rows.append(dict(city=cid, donor=dcid, d_km=r.d_km, r=np.nan, n=len(j),
                             why="too few common days"))
            continue
        rows.append(dict(city=cid, donor=dcid, d_km=float(r.d_km),
                         r=float(j.obs.corr(j.bg)), n=len(j), why=""))
    _ = rng_master
    return pd.DataFrame(rows)


def main() -> int:
    print("Colombo as a background donor for Kandy  (F.63 re-run)\n")

    kd, slat, slon, rel = kandy_daily()
    cd, clat, clon = colombo_daily()
    d_km = float(haversine(*KANDY_CENTRE, clat, clon))
    klat, klon = KANDY_CENTRE

    j = pd.concat([kd.rename("kandy"), cd.rename("colombo")], axis=1).dropna()
    r_raw = float(j.kandy.corr(j.colombo))
    # Spearman too: a low Pearson can be a tail artefact, and it is not one here.
    r_rank = float(j.kandy.corr(j.colombo, method="spearman"))
    r_corr = r_raw / np.sqrt(rel) if np.isfinite(rel) and rel > 0 else np.nan

    print(f"  Kandy centre {klat:.3f}N {klon:.3f}E, sensors {slat:.3f}N {slon:.3f}E, "
          f"Colombo {clat:.3f}N {clon:.3f}E")
    print(f"  separation           {d_km:.1f} km   (admissible donor window is 30-300 km)")
    print(f"  common days          {len(j):,}")
    print(f"  between-sensor r     {rel:.3f}   (Kandy's own reliability ceiling)")
    print(f"  Kandy-Colombo r      {r_raw:.3f}   rank {r_rank:.3f}")
    print(f"  disattenuated        {r_corr:.3f}\n")

    b = panel_benchmark()
    ok = b.dropna(subset=["r"])
    med = float(ok.r.median())
    band = ok[(ok.d_km >= d_km - BAND_KM) & (ok.d_km <= d_km + BAND_KM)]
    med_band = float(band.r.median())
    nearest = ok.iloc[(ok.d_km - d_km).abs().argsort()].iloc[0]

    print(f"  panel donor pairs    {len(ok)} scored of {len(b)} attempted")
    print(f"  benchmark median r   {med:.3f}   range {ok.r.min():.3f} to {ok.r.max():.3f}")
    print(f"  distance-matched     {med_band:.3f}   median of {len(band)} pairs within "
          f"+/-{BAND_KM:.0f} km of {d_km:.0f} km")
    print(f"  nearest single pair  {nearest.r:.3f} at {nearest.d_km:.1f} km "
          f"({nearest.city} <- {nearest.donor})")
    worse = int((ok.r < r_raw).sum())
    worse_band = int((band.r < r_raw).sum())
    print(f"  pairs below Kandy    {worse} of {len(ok)} overall, "
          f"{worse_band} of {len(band)} in the distance band\n")

    # The recorded ledger figure was a "distance-matched benchmark of 0.923". Nothing here is
    # 0.923: the pooled median is {med:.3f} and the matched median {med_band:.3f}. The nearest
    # single pair is {nearest.r:.3f}, which is where that number almost certainly came from --
    # one pair's value quoted as a median. Flag it rather than quietly publishing the new one.
    if abs(nearest.r - 0.923) < 0.02 and abs(med - 0.923) > 0.02:
        print(f"  NOTE: the retired 0.923 matches the NEAREST PAIR ({nearest.r:.3f}), not a "
              f"median. The benchmark is {med:.3f} pooled / {med_band:.3f} matched.\n")

    out = ok.assign(kind="panel")[["city", "donor", "d_km", "r", "n", "kind"]]
    out = pd.concat([out, pd.DataFrame([dict(city="kandy", donor="colombo", d_km=d_km,
                                             r=r_raw, n=len(j), kind="target")])],
                    ignore_index=True)
    out.to_csv(MOD / "colombo_donor_test.csv", index=False)
    print(f"  wrote {(MOD / 'colombo_donor_test.csv').relative_to(REPO)}")

    emit("colombo_donor",
         d_km=round(d_km, 1),
         r_daily=round(r_raw, 3),
         r_rank=round(r_rank, 3),
         r_disattenuated=round(float(r_corr), 3) if np.isfinite(r_corr) else None,
         sensor_reliability=round(rel, 3) if np.isfinite(rel) else None,
         common_days=int(len(j)),
         benchmark_median=round(med, 3),
         benchmark_median_distance_matched=round(med_band, 3),
         benchmark_band_pairs=int(len(band)),
         benchmark_band_km=BAND_KM,
         benchmark_min=round(float(ok.r.min()), 3),
         benchmark_max=round(float(ok.r.max()), 3),
         benchmark_pairs=int(len(ok)),
         nearest_pair_r=round(float(nearest.r), 3),
         nearest_pair_km=round(float(nearest.d_km), 1),
         pairs_below_kandy=worse,
         pairs_below_kandy_in_band=worse_band)
    return 0


if __name__ == "__main__":
    sys.exit(main())
