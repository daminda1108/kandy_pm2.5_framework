"""local_fraction_e3.py -- E3 of the local-fraction study: the 2020 curfew at the CEA Kandy AAQMS (context only)
(spec docs/local_fraction_study_spec_2026-10-11.md; ledger F.134).

rho = K / T on daily means, T = the temporal anchor (business-as-usual composition prior + meteorology).
D = 1 - <rho>_curfew / <rho>_reference; curfew 2020-03-20 .. 2020-05-10; reference = same window in 2019 and 2021.
D = f*a + (1-f)*r: a bound on f only if the regional change r is 0, which concurrent South Asian lockdowns make unlikely.
Out: data/processed/decomp/local_fraction_e3.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
TAN = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"
TZ = "Asia/Colombo"
W0, W1 = ("03-20", "05-10")
NB, SEED = 4000, 20261011


def main():
    h = pd.read_csv(REPO / "data" / "external" / "cea" / "kandy_aqms_hourly.csv", parse_dates=["t_local"]).dropna(subset=["pm2_5"])
    K = h.groupby(h.t_local.dt.floor("D")).pm2_5.agg(["mean", "size"])
    K = K[K["size"] >= 18]["mean"]
    T = pd.concat([pd.read_parquet(TAN / f"T_kandy_hourly_{y}.parquet", columns=["datetime_utc", "T_q50"]) for y in (2019, 2020, 2021)])
    T["d"] = pd.to_datetime(T.datetime_utc, utc=True).dt.tz_convert(TZ).dt.tz_localize(None).dt.floor("D")
    T = T.groupby("d").T_q50.mean()
    J = pd.DataFrame({"K": K, "T": T}).dropna()
    J["rho"] = J.K / J["T"]
    win = lambda y: J[(J.index >= f"{y}-{W0}") & (J.index <= f"{y}-{W1}")]
    cur, ref = win(2020), pd.concat([win(2019), win(2021)])
    D = 1 - cur.rho.mean() / ref.rho.mean()
    raw = 1 - cur.K.mean() / ref.K.mean()
    rng = np.random.default_rng(SEED)
    bs = [1 - rng.choice(cur.rho.to_numpy(), len(cur)).mean() / rng.choice(ref.rho.to_numpy(), len(ref)).mean() for _ in range(NB)]
    out = dict(curfew_days=int(len(cur)), reference_days=int(len(ref)),
               reference_years={int(y): int((ref.index.year == y).sum()) for y in (2019, 2021)},
               D_weather_adjusted=float(D), D_ci95=[float(x) for x in np.percentile(bs, [2.5, 97.5])],
               D_raw=float(raw), K_curfew=float(cur.K.mean()), K_reference=float(ref.K.mean()),
               note="context only: D = f*a + (1-f)*r; not a bound on f unless the regional change r = 0")
    p = DEC / "local_fraction_e3.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=1), encoding="utf-8"); os.replace(tmp, p)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
