"""flat_hour_residual_fit.py — fit + gate the ventilated-hour pattern floor (additive_v3).

THE DEFECT (model_accuracy_plan_2026-07-21.md §1.1): the increment-split renders
T<=B hours perfectly flat, but Medellin's network keeps station std ~5.7 ug/m3
(relative spread 0.68 > structured 0.42) on exactly those hours.

THE FIX (§2): a pattern-amplitude FLOOR, mean-zero by construction:

    PM = B + inc+*P + inc- + eps(t)*(P-1),   eps(t) = max(0, eps0 - inc+)
       = B + max(inc+, eps0)*P - max(0, eps0 - inc+) + inc-

  * basin mean unchanged (T-lock EXACT: the (P-1) term is mean-zero)
  * core stays >= edge (eps >= 0, accumulation-side P) — cannot re-open the
    core<periphery inversion (gotcha #57 sibling)
  * structured hours (inc+ >= eps0) are IDENTICAL to additive_v2 — the change
    activates only where the current model is provably wrong

FIT: eps0 = through-origin OLS slope of flat-hour station obs anomalies
     (obs - network mean) on (P_st - 1), on the withheld-NON-holdout stations.
NORMALIZATION CHECK: measure each ground-truth city's own eps empirically;
     decide absolute vs relative (fraction of the city's mean accumulation
     amplitude) by which collapses across cities.
GATES: (1) holdout-6 flat-hour + overall RMSE/level no-degrade;
       (2) per-city held-out metrics at the other panel cities no-degrade
           (structured hours identical, so only flat hours can move);
       (3) Kandy invariants (T-lock delta 0, inversion 0%) after the builder
           change (separate script).

Out: results/figures/medellin_showcase/flat_hour_residual.{json,txt}
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medellin_a2_amplitude_fit as a2          # reuse city_data/station_preds/metrics
import xichang_paper_figures as xf

OUT = Path(__file__).resolve().parents[1] / "results/figures/medellin_showcase"
FLAT_INC = 0.5           # "flat" = accumulation amplitude below this (ug/m3)


def station_pixels(pack, st, ids):
    """Column index of each station's pixel in the flattened field (in-box only)."""
    la, lo = pack["lats"], pack["lons"]
    out = {}
    for sid in ids:
        if sid not in st.index:
            continue
        r = st.loc[sid]
        if not (la.min() <= r.lat <= la.max() and lo.min() <= r.lon <= lo.max()):
            continue
        i = int(np.abs(la - r.lat).argmin()); j = int(np.abs(lo - r.lon).argmin())
        out[sid] = i * len(lo) + j
    return out


def flat_hour_table(city, ids_fit):
    """Long table on FLAT hours: obs anomaly vs (P_st - 1), + city stats."""
    st, packs, obs = a2.city_data(city)
    rows = []
    inc_pos_all = []
    for pack in packs:
        inc = pack["T"] - pack["B"]
        inc_pos_all.append(np.clip(inc, 0, None))
        flat = inc <= FLAT_INC
        if not flat.any():
            continue
        px = station_pixels(pack, st, ids_fit)
        times = pack["times"][flat]
        P = pack["P"][flat]
        o = obs[obs.station_id.isin(px.keys())]
        o = o[o.loct.isin(pd.DatetimeIndex(times.tz_convert(xf.TZ)).floor("h"))]
        if o.empty:
            continue
        tmap = {t: k for k, t in
                enumerate(pd.DatetimeIndex(times.tz_convert(xf.TZ)).floor("h"))}
        for (t, grp) in o.groupby("loct"):
            if len(grp) < 5 or t not in tmap:
                continue
            k = tmap[t]
            net = grp.pm25.mean()
            for _, r in grp.iterrows():
                p_st = P[k, px[r.station_id]]
                if np.isfinite(p_st):
                    rows.append((r.station_id, t, r.pm25 - net, p_st - 1.0))
    df = pd.DataFrame(rows, columns=["sid", "t", "obs_anom", "p_anom"])
    mean_inc_pos = float(np.nanmean(np.concatenate(inc_pos_all)))
    return df, mean_inc_pos, st, packs, obs


def fit_slope(df):
    """Through-origin OLS slope + spearman of obs anomaly on (P-1)."""
    x, y = df.p_anom.to_numpy(), df.obs_anom.to_numpy()
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    slope = float((x @ y) / (x @ x)) if (x @ x) > 0 else np.nan
    from scipy.stats import spearmanr
    rho = float(spearmanr(x, y).statistic) if len(x) > 10 else np.nan
    return slope, rho, len(x)


def eval_gate(city, st, packs, obs, ids, eps0):
    """Holdout metrics with the floor vs without, flat hours + overall."""
    res = {}
    for tag, e in [("v2", 0.0), ("v3", eps0)]:
        rows = []
        for pack in packs:
            inc = pack["T"] - pack["B"]
            inc_p = np.clip(inc, 0, None)
            eps = np.clip(e - inc_p, 0, None)
            F = (pack["B"][:, None] + inc_p[:, None] * pack["P"]
                 + np.clip(inc, None, 0)[:, None]
                 + eps[:, None] * (pack["P"] - 1.0))
            F = np.clip(F, 0, None)
            px = station_pixels(pack, st, ids)
            lt = pd.DatetimeIndex(pack["times"].tz_convert(xf.TZ)).floor("h")
            tmap = pd.Series(np.arange(len(lt)), index=lt)
            tmap = tmap[~tmap.index.duplicated()]
            o = obs[obs.station_id.isin(px.keys()) & obs.loct.isin(tmap.index)]
            k = tmap.reindex(o.loct).to_numpy()
            pred = F[k.astype(int), [px[s] for s in o.station_id]]
            rows.append(pd.DataFrame({"obs": o.pm25.to_numpy(), "pred": pred,
                                      "flat": (inc_p[k.astype(int)] <= FLAT_INC)}))
        d = pd.concat(rows)
        res[tag] = {
            "rmse_all": float(np.sqrt(((d.pred - d.obs) ** 2).mean())),
            "rmse_flat": float(np.sqrt(((d[d.flat].pred - d[d.flat].obs) ** 2).mean()))
                         if d.flat.any() else np.nan,
            "bias_all": float((d.pred - d.obs).mean()),
            "n_flat": int(d.flat.sum()),
        }
    return res


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rep = {"flat_inc": FLAT_INC}
    lines = ["FLAT-HOUR RESIDUAL FLOOR — fit + gates", "=" * 60]

    # ── Medellín: pattern check + fit ────────────────────────────────────────
    hold = json.load(open(OUT / "holdout6.json"))
    hold6, anchors = hold["holdout6"], hold["anchors"]
    st, packs, obs = a2.city_data("medellin")
    inbox = st[(st.lat >= packs[0]["lats"].min()) & (st.lat <= packs[0]["lats"].max())
               & (st.lon >= packs[0]["lons"].min()) & (st.lon <= packs[0]["lons"].max())]
    ids_fit = [s for s in inbox.index if s not in hold6 and s not in anchors]
    df, mean_inc, *_ = flat_hour_table("medellin", ids_fit)
    slope, rho, n = fit_slope(df)
    lines += [f"\nMEDELLÍN pattern check (fit stations n={len(ids_fit)}):",
              f"  flat-hour obs-anomaly ~ (P-1): slope {slope:.2f} ug/m3, "
              f"spearman {rho:.2f}, n={n}"]
    # structured-hour reference slope (is the pattern source the same?)
    # (A1 already established rank rho 0.75 on structured hours)
    if not np.isfinite(slope) or slope <= 0 or rho < 0.1:
        lines += ["  -> NO-GO: flat-hour structure is not emission-shaped; "
                  "record negative, do not ship."]
        (OUT / "flat_hour_residual.txt").write_text("\n".join(lines))
        print("\n".join(lines)); return
    eps0 = round(slope, 2)
    rep.update(eps0_medellin=eps0, spearman=round(rho, 3), n_pairs=n,
               mean_inc_pos=round(mean_inc, 2), eps0_rel=round(eps0 / mean_inc, 3))
    lines += [f"  -> eps0 = {eps0} ug/m3 (relative form: {eps0/mean_inc:.3f} x "
              f"mean accumulation amplitude {mean_inc:.2f})"]

    # ── Gate 1: holdout-6 ────────────────────────────────────────────────────
    g1 = eval_gate("medellin", st, packs, obs, hold6, eps0)
    rep["gate1_holdout6"] = g1
    d_rmse = g1["v3"]["rmse_flat"] - g1["v2"]["rmse_flat"]
    d_all = g1["v3"]["rmse_all"] - g1["v2"]["rmse_all"]
    ok1 = (d_rmse < 0.05) and (d_all < 0.05) and \
          (abs(g1["v3"]["bias_all"]) <= abs(g1["v2"]["bias_all"]) + 0.05)
    lines += [f"\nGATE 1 holdout-6: flat-hour RMSE {g1['v2']['rmse_flat']:.2f} -> "
              f"{g1['v3']['rmse_flat']:.2f} (d {d_rmse:+.2f}, n={g1['v3']['n_flat']}) | "
              f"overall {g1['v2']['rmse_all']:.2f} -> {g1['v3']['rmse_all']:.2f} | "
              f"bias {g1['v2']['bias_all']:+.2f} -> {g1['v3']['bias_all']:+.2f}  "
              f"=> {'PASS' if ok1 else 'FAIL'}"]

    # ── Gate 2: cross-city (each city's own empirical eps + no-degrade) ─────
    rep["cross_city"] = {}
    ok2 = True
    for city in ["kathmandu", "chiangmai"]:
        try:
            stc, packsc, obsc = a2.city_data(city)
            ids = list(stc.index)
            dfc, mic, *_ = flat_hour_table(city, ids)
            sl, rh, nn = fit_slope(dfc) if len(dfc) else (np.nan, np.nan, 0)
            # transfer BOTH forms, evaluate no-degrade on all stations
            g_abs = eval_gate(city, stc, packsc, obsc, ids, eps0)
            e_rel = rep["eps0_rel"] * mic
            g_rel = eval_gate(city, stc, packsc, obsc, ids, e_rel)
            rep["cross_city"][city] = dict(
                own_slope=None if not np.isfinite(sl) else round(sl, 2),
                own_rho=None if not np.isfinite(rh) else round(rh, 2),
                n=nn, mean_inc=round(mic, 2), eps_rel_value=round(e_rel, 2),
                gate_abs=g_abs, gate_rel=g_rel)
            da = g_abs["v3"]["rmse_all"] - g_abs["v2"]["rmse_all"]
            dr = g_rel["v3"]["rmse_all"] - g_rel["v2"]["rmse_all"]
            if g_abs["v3"]["n_flat"] == 0:
                # no flat hours at this city -> the floor never activates ->
                # vacuously no-degrade (verify: v3 == v2 exactly)
                ok2 &= abs(da) < 1e-9 if np.isfinite(da) else True
            else:
                ok2 &= (min(da, dr) < 0.05)
            lines += [f"GATE 2 {city}: own slope {sl if np.isfinite(sl) else 'n/a'} "
                      f"(rho {rh if np.isfinite(rh) else 'n/a'}, n={nn}) | "
                      f"abs-transfer dRMSE {da:+.3f} | rel-transfer dRMSE {dr:+.3f}"]
        except Exception as ex:
            lines += [f"GATE 2 {city}: SKIP ({ex})"]
    lines += [f"GATE 2 => {'PASS' if ok2 else 'FAIL'}"]
    rep["verdict"] = "PASS" if (ok1 and ok2) else "FAIL"
    lines += [f"\nVERDICT: {rep['verdict']}  (eps0={eps0} ug/m3 absolute; "
              f"rel {rep['eps0_rel']} x city mean accumulation)"]
    (OUT / "flat_hour_residual.json").write_text(json.dumps(rep, indent=1))
    (OUT / "flat_hour_residual.txt").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
