"""anchors.py — the frozen anchor-draw protocol (prereg §4).

At each panel city the recipe receives exactly TWO "anchor" stations (playing the
FECT role at Kandy); every other station is vault (scoring only). This module
implements the FROZEN draw protocol:

  * R = 5 draws, seeds = range(5) via numpy default_rng — reproducible.
  * Eligibility: stations with usable coverage in the score window, MINUS the
    single highest-mean and single lowest-mean station (the frozen "no extreme
    anchors" rule — anchors must be ordinary sites, mirroring the fact that Kandy
    did not get to choose FECT's siting).
  * A draw = 2 distinct eligible stations; vault(draw) = all stations − the pair.

Reading per-station PM2.5 means here is sanctioned by the frozen protocol (the
means are needed to exclude extremes); vault stations still never influence any
model component.

Implementation note (practical, applied blind & symmetrically before the draw):
a station must have ≥ MIN_OBS hourly observations inside the score window to be
an eligible anchor — an anchor with almost no data cannot train T(t). This mirrors
reality: FECT sensors had multi-year records. Vault membership is NOT affected
(low-coverage stations still score in the vault with whatever hours they have).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

R_DRAWS = 5          # frozen (prereg §4)
MIN_OBS = 4000       # practical anchor-eligibility floor (hourly rows in window)


@dataclass
class Draw:
    seed: int
    anchors: tuple[str, str]
    vault: tuple[str, ...]


def station_stats(cp, years=None):
    """Per-station n_obs + mean pm25 inside the score window (protocol input)."""
    import pandas as pd
    years = set(years or cp.score_years)
    df = pd.read_parquet(cp.station_parquet(),
                         columns=["datetime_utc", "station_id", "pm25"])
    df["datetime"] = pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)
    df = df.dropna(subset=["datetime", "pm25"])
    df = df[df["datetime"].dt.year.isin(years)]
    g = df.groupby("station_id")["pm25"].agg(n_obs="count", mean="mean").reset_index()
    return g.sort_values("mean").reset_index(drop=True)


def eligible_anchors(stats) -> list[str]:
    """Coverage floor, then drop the single lowest- and highest-mean station."""
    s = stats[stats.n_obs >= MIN_OBS].sort_values("mean").reset_index(drop=True)
    if len(s) < 4:
        raise ValueError(f"only {len(s)} stations pass the coverage floor — "
                         "cannot exclude extremes AND draw a pair")
    return list(s.station_id.iloc[1:-1])      # drop min-mean + max-mean


def draws(cp, years=None) -> list[Draw]:
    """Anchor draws for a city, per its anchor_mode (prereg §4 + Amendment 2).

    "draws":         up to R=5 DISTINCT pairs. Small pools (≤5 possible pairs)
                     enumerate all distinct pairs deterministically; larger pools
                     use seeded sampling de-duplicated to R distinct pairs.
    "fixed_longest": single deterministic draw — the 2 stations with the longest
                     records over the parquet's full history (the city's own
                     "FECT pair"); the recent dense network is the vault.
    """
    from itertools import combinations
    stats = station_stats(cp, years)
    all_st = list(stats.station_id)

    if cp.anchor_mode == "fixed_longest":
        hist = station_stats(cp, years=range(2015, 2027))    # full history
        pair = tuple(sorted(hist.sort_values("n_obs").station_id.iloc[-2:].tolist()))
        vault = tuple(s for s in all_st if s not in pair)
        return [Draw(seed=-1, anchors=pair, vault=vault)]

    pool = eligible_anchors(stats)
    pairs = [tuple(sorted(p)) for p in combinations(pool, 2)]
    if len(pairs) > R_DRAWS:
        rng = np.random.default_rng(0)
        chosen: list[tuple] = []
        while len(chosen) < R_DRAWS:
            p = tuple(sorted(rng.choice(pool, size=2, replace=False).tolist()))
            if p not in chosen:
                chosen.append(p)
        pairs = chosen
    return [Draw(seed=i, anchors=p,
                 vault=tuple(s for s in all_st if s not in p))
            for i, p in enumerate(pairs)]


def _selftest() -> int:
    from .citypack import get
    for slug in ("xichang", "kathmandu"):
        cp = get(slug)
        stats = station_stats(cp)
        ds = draws(cp)
        pool = (f"{len(eligible_anchors(stats))} anchor-eligible"
                if cp.anchor_mode == "draws" else "fixed_longest mode")
        print(f"\n=== {slug} ===  ({len(stats)} stations in window, {pool})")
        if len(stats) <= 12:
            print(stats.round(1).to_string(index=False))
        for d in ds:
            print(f"  seed {d.seed}: anchors={d.anchors}  vault n={len(d.vault)}")
    print("\nANCHORS SELFTEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
