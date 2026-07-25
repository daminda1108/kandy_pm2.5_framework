"""score_additive_v3.py — score the BUILT additive_v3 fields against the withheld network.

Why this exists. The ventilated-hour floor (additive_v3) was fitted at Medellín and
gated on the fit-time packs (flat_hour_residual_fit.py). That made it "Medellín-fitted".
This script scores the **shipped parquets** — the actual product — against the
deliberately withheld stations, which is what makes it **Medellín-validated**, and is
the claim upgrade that matters: at Kandy the floor can only ever be imposed (no network),
so its evidence has to come from here.

Design notes
  * nearest-pixel extraction (the 1 km grid vs a station coordinate) — the same
    convention the fit used, and it avoids the extrapolation trap in
    `_pred_at_stations` (which also silently ignores its `kind` argument and always
    reads v2, so it cannot be used to compare tiers).
  * scored on BOTH station sets: holdout-6 (never touched by any tier, the strict
    test) and the wider vault (all withheld non-anchor stations).
  * the headline metric is FLAT-HOUR RMSE — the hours the floor targets. Overall
    metrics are reported to prove nothing else degraded.

Out: results/figures/medellin_showcase/additive_v3_validation.{csv,txt}
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xichang_paper_figures as xf

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "figures" / "medellin_showcase"
FLAT_INC = 0.5             # "flat" hour = accumulation amplitude at or below this


def station_pixels(lats, lons, st, ids):
    """Nearest flattened pixel index for each in-box station."""
    out = {}
    for sid in ids:
        if sid not in st.index:
            continue
        r = st.loc[sid]
        if not (lats.min() <= r.lat <= lats.max() and lons.min() <= r.lon <= lons.max()):
            continue
        i = int(np.abs(lats - r.lat).argmin()); j = int(np.abs(lons - r.lon).argmin())
        out[sid] = i * len(lons) + j
    return out


def load_tier(city, year, tier):
    """(times, F[times,npx], lats, lons) for a built tier."""
    dec = REPO / "data" / "processed" / f"decomp_{city}"
    fp = dec / f"{city}_decomp_predictions_{year}_{tier}.parquet"
    if not fp.exists():
        return None
    d = pd.read_parquet(fp, columns=["time", "lat", "lon", "pm25_q50"])
    d["time"] = pd.to_datetime(d.time, utc=True)
    d = d.sort_values(["time", "lat", "lon"])
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    times = pd.DatetimeIndex(d.time.unique())
    F = d.pm25_q50.to_numpy().reshape(len(times), len(lats) * len(lons))
    return times, np.clip(F, 0, None), lats, lons        # display floor, as shipped


def metrics(df):
    e = df.pred - df.obs
    return dict(n=int(len(df)),
                rmse=float(np.sqrt((e ** 2).mean())),
                bias=float(e.mean()),
                mae=float(e.abs().mean()))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    city = "medellin"
    xf._setup(city)
    st, _ = xf._stations_split()
    hold = json.load(open(OUT / "holdout6.json"))
    hold6, anchors = hold["holdout6"], hold["anchors"]
    from city_config import cfg
    years = [y for y in cfg(city)["years"]]

    rows = []
    for year in years:
        v2 = load_tier(city, year, "additive_v2")
        v3 = load_tier(city, year, "additive_v3")
        if v2 is None or v3 is None:
            continue
        times, F2, lats, lons = v2
        _, F3, _, _ = v3
        # background to identify the ventilated (flat) hours the floor targets
        b = pd.read_parquet(REPO / "data" / "processed" / f"decomp_{city}"
                            / f"B_background_hourly_{year}_{city}.parquet")
        b["time"] = pd.to_datetime(b.datetime_utc, utc=True)
        B = b.set_index("time")["B"].reindex(times).to_numpy()
        T = F2.mean(axis=1)                       # basin mean == the anchor
        flat_h = (T - B) <= FLAT_INC

        obs = xf._obs(year)
        obs["loct"] = obs.loct.dt.floor("h")
        lt = pd.DatetimeIndex(times.tz_convert(xf.TZ)).floor("h")
        tmap = pd.Series(np.arange(len(lt)), index=lt)
        tmap = tmap[~tmap.index.duplicated()]

        for setname, ids in (("holdout6", hold6),
                            ("vault", [s for s in st.index
                                       if s not in anchors and s not in hold6])):
            px = station_pixels(lats, lons, st, ids)
            if not px:
                continue
            o = obs[obs.station_id.isin(px.keys()) & obs.loct.isin(tmap.index)]
            if o.empty:
                continue
            k = tmap.reindex(o.loct).to_numpy().astype(int)
            cols = np.array([px[s] for s in o.station_id])
            d = pd.DataFrame({"obs": o.pm25.to_numpy(),
                              "v2": F2[k, cols], "v3": F3[k, cols],
                              "flat": flat_h[k]})
            for tier in ("v2", "v3"):
                sub = d.rename(columns={tier: "pred"})
                for scope, mask in (("all", np.ones(len(d), bool)),
                                    ("flat", d.flat.to_numpy())):
                    if mask.sum() < 20:
                        continue
                    m = metrics(sub[mask])
                    rows.append(dict(year=year, station_set=setname, tier=tier,
                                     scope=scope, **m))

    t = pd.DataFrame(rows)
    t.to_csv(OUT / "additive_v3_validation.csv", index=False)

    lines = ["additive_v3 vs additive_v2 — scored on the WITHHELD network (built fields)",
             "=" * 78,
             f"flat hour := accumulation amplitude (T-B) <= {FLAT_INC} ug/m3", ""]
    verdict_ok = True
    for setname in t.station_set.unique():
        s = t[t.station_set == setname]
        lines.append(f"[{setname}]")
        for scope in ("flat", "all"):
            a = s[(s.scope == scope) & (s.tier == "v2")]
            b_ = s[(s.scope == scope) & (s.tier == "v3")]
            if a.empty or b_.empty:
                continue
            # pool across years by observation count
            def pool(x):
                w = x.n.to_numpy()
                return (float(np.sqrt(np.average(x.rmse ** 2, weights=w))),
                        float(np.average(x.bias, weights=w)), int(w.sum()))
            r2, b2, n2 = pool(a); r3, b3, n3 = pool(b_)
            d = r3 - r2
            tag = "IMPROVED" if d < -0.005 else ("no change" if abs(d) <= 0.005 else "DEGRADED")
            if scope == "flat" and d > 0.005:
                verdict_ok = False
            if scope == "all" and d > 0.05:
                verdict_ok = False
            lines.append(f"  {scope:4s} n={n2:7d} | RMSE {r2:6.3f} -> {r3:6.3f} "
                         f"({d:+.3f})  bias {b2:+6.3f} -> {b3:+6.3f}   {tag}")
        lines.append("")
    lines.append(f"VERDICT: {'PASS' if verdict_ok else 'FAIL'} — v3 improves (or holds) "
                 f"flat-hour error with no material overall degradation")
    txt = "\n".join(lines)
    (OUT / "additive_v3_validation.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
