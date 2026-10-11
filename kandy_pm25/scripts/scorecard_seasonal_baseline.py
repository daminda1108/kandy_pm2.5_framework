"""scorecard_seasonal_baseline.py -- null baselines for the ten-city seasonal correlation (2026-10-11, ledger F.135).

A review pointed out that a seasonal correlation of 0.94-1.00 says little unless simpler predictors are scored the same
way: the composition prior carries a seasonal cycle, and the two anchor stations set the level. For each scorecard city,
on exactly the scorecard's rows (withheld "vault" stations, the years whose delivered field exists), compute the
Pearson correlation of the 12 calendar-month means of:
  model     the delivered field at the vault stations (re-read from validation_scorecard.csv, same computation);
  prior     the GEOS-CF composition prior (c_prior) at the vault stations, on the same station-hours as the observations;
  anchors   the two anchor stations' own observed monthly means (the information the construction is given);
against the vault stations' observed monthly means. Also the RMSE of the monthly means after scaling each predictor to
the observed annual mean (shape error), which separates shape agreement from amplitude.
Out: results/figures/multicity/scorecard_seasonal_baseline.csv (+ .json summary)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf   # noqa: E402

CITIES = ["xichang", "chiangmai", "bazhou", "chandigarh", "kathmandu", "baoji", "taian", "yichang", "medellin", "bogota"]
OUT = REPO / "results" / "figures" / "multicity"


def monthly(df, col):
    return df.assign(m=df.loct.dt.month).groupby("m")[col].mean()


def shape_rmse(pred, obs):
    j = pd.concat([pred.rename("p"), obs.rename("o")], axis=1).dropna()
    p = j.p * (j.o.mean() / j.p.mean())
    return float(np.sqrt(((p - j.o) ** 2).mean()) / j.o.mean())


def r12(pred, obs):
    j = pd.concat([pred.rename("p"), obs.rename("o")], axis=1).dropna()
    return float(pearsonr(j.p, j.o)[0]), int(len(j))


def main():
    sc = pd.read_csv(OUT / "validation_scorecard.csv")
    rows = []
    for i, slug in enumerate(CITIES):
        xf._setup(slug)
        st, anc = xf._stations_split()
        vault = [s for s in st.index if int(s) not in anc]
        cp = xf.cp_xichang()
        d = pd.read_parquet(cp.station_parquet(), columns=["datetime_utc", "station_id", "pm25", "c_prior"])
        d = d.dropna(subset=["pm25"])
        d["loct"] = pd.to_datetime(d.datetime_utc, utc=True).dt.tz_convert(xf.TZ)
        years = [y for y in xf.xp.YEARS
                 if (xf.DEC / f"{xf.CITY}_decomp_predictions_{y}_additive_v2.parquet").exists()]
        d = d[d.loct.dt.year.isin(years)]
        V = d[d.station_id.isin(vault)]
        A = d[d.station_id.astype(int).isin(anc)]
        om = monthly(V, "pm25")
        prior_m = monthly(V.dropna(subset=["c_prior"]), "c_prior")
        anchor_m = monthly(A, "pm25")
        r_prior, n_p = r12(prior_m, om)
        r_anchor, n_a = r12(anchor_m, om) if len(A) else (np.nan, 0)
        rows.append(dict(city=slug, scorecard_name=sc.city.iloc[i], n_vault=len(vault), years=f"{min(years)}-{max(years)}",
                         months=int(om.notna().sum()), r_model=float(sc.seasonal.iloc[i]),
                         r_prior=r_prior, r_anchors=r_anchor,
                         shape_rmse_prior=shape_rmse(prior_m, om),
                         shape_rmse_anchors=shape_rmse(anchor_m, om) if len(A) else np.nan,
                         prior_cover=float(V.c_prior.notna().mean())))
        print(f"{slug:11s} model {rows[-1]['r_model']:.3f}  prior {r_prior:.3f}  anchors {r_anchor:.3f}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "scorecard_seasonal_baseline.csv", index=False)
    summ = {k: dict(min=float(df[k].min()), median=float(df[k].median()), max=float(df[k].max()))
            for k in ("r_model", "r_prior", "r_anchors")}
    summ["model_minus_prior_median"] = float((df.r_model - df.r_prior).median())
    summ["model_minus_anchors_median"] = float((df.r_model - df.r_anchors).median())
    summ["cities_model_above_prior"] = int((df.r_model > df.r_prior).sum())
    summ["cities_model_above_anchors"] = int((df.r_model > df.r_anchors).sum())
    p = OUT / "scorecard_seasonal_baseline.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(summ, indent=1), encoding="utf-8"); os.replace(tmp, p)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
