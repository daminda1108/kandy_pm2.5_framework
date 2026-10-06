"""F3 of test B (OSF fu59b), exploratory, declared in the registration: the tropical arm.

The registration: if three or more tropical or deep-tropical cities qualify, their curves are reported
separately as a tropical arm, with its own detection limit, against the temperate envelope (as X8).
X8 in the frozen summary builds its envelope from ALL primary cities, which on full records include two
tropical ones, so it is not the registered comparison for F3. Here:
  arm       = band-arm cities (|lat| < 23.5, >= 12 sites) of the frame
  envelope  = min-max of E3's per-city median curve over the NON-tropical primary cities, per k
  per city  = share of k at which its E3 curve lies inside / above / below the envelope; first k at which
              E3 or E5 beats the raster (E0) by the frozen crossover rule's output where available
  detection limit = the registered mde_for(number of countries in the arm)
Reads the frozen summary's outputs; computes nothing new from PM2.5.
"""
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import spatial_curve_analysis as A                                      # noqa: E402

NEW = REPO / "data" / "processed" / "modular" / "spatial_curve_full"
TROP = ("tropical", "deep_tropical")


def run(tag: str) -> dict:
    sfx = f"_{tag}" if tag else ""
    C = pd.read_csv(NEW / f"frame_cities{sfx}.csv")
    ck = pd.read_csv(NEW / f"analysis{sfx}" / "curve_q1_city.csv")
    arm = C[C.band_arm.astype(bool)]
    temp = C[C.primary.astype(bool) & ~C.band.isin(TROP)].cluster
    env = ck[(ck.est == "E3") & ck.cluster.isin(temp)].groupby("k").rho.agg(["min", "max", "median"])
    out = {"envelope_cities": int(len(temp)), "arm_cities": int(len(arm)),
           "arm_countries": int(arm.country.nunique()),
           "detection_limit": A.mde_for(int(arm.country.nunique())), "cities": {}}
    for r in arm.itertuples():
        g = ck[(ck.cluster == r.cluster) & (ck.est == "E3")].set_index("k").rho
        j = g.to_frame().join(env, how="inner")
        if j.empty:
            out["cities"][int(r.cluster)] = dict(country=r.country, band=r.band, sites=int(r.sites), k_scored=0)
            continue
        e0 = ck[(ck.cluster == r.cluster) & (ck.est == "E0")].set_index("k").rho
        cross = {}
        for e in ("E3", "E5"):
            ge = ck[(ck.cluster == r.cluster) & (ck.est == e)].set_index("k").rho
            d = (ge - e0).dropna()
            cross[e] = int(d[d > 0].index.min()) if (d > 0).any() else None
        out["cities"][int(r.cluster)] = dict(
            country=r.country, band=r.band, sites=int(r.sites), primary=bool(r.primary),
            k_scored=int(len(j)),
            inside=float(((j.rho >= j["min"]) & (j.rho <= j["max"])).mean()),
            above=float((j.rho > j["max"]).mean()), below=float((j.rho < j["min"]).mean()),
            median_gap_to_envelope_median=float((j.rho - j["median"]).median()),
            first_k_beating_raster=cross)
    return out


if __name__ == "__main__":
    res = {tag or "registered": run(tag) for tag in ("", "s70")}
    p = NEW / "F3_tropical_arm.json"
    p.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
