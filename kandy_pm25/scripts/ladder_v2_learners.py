"""ladder_v2_learners.py -- learner-robustness test of the confirmed ladder (registration draft
docs/prereg_learner_robustness_2026-09-28_DRAFT.md).

Only the Bud0c learner changes; `ladder_v2.run` (frozen, e6b744b) is otherwise untouched. Out-of-city
Bud0 predictions from a learner are INJECTED by replacing `ladder_v2.bagged_bud0` for the duration of
one run (the frozen file is not edited):

  L0  HGB as confirmed, passed through the injection path (parity gate against ueyfr)
  L1  TabPFN 8.5.0 (v3), Kaggle T4           -> predictions from scripts/bud0_learners_kaggle.py
  L2  GRU over 14-day windows, Kaggle T4     -> same
  L3  HGB + four physics features (local; no injection, features appended)

Modes
  --export       writes the frame for Kaggle. Before registration ONLY with --synthetic (the outcome
                 replaced by noise independent of every predictor, as in ladder_v2_rich.synthetic).
  --dry-run      local end-to-end on the synthetic outcome, L0 and L3 only (L1/L2 run on Kaggle).
  --score        the registered run; refuses without learners/REGISTERED.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
LD = MOD / "learners"
OUTD = MOD / "ladder_v2"
PHYS = ["vc", "inv_vc", "inv_vc_3d", "aod_over_blh"]


def physics(p: pd.DataFrame) -> pd.DataFrame:
    """Adds PHYS WITHOUT changing row order: HGB's automatic early-stopping split is drawn by row
    position, so a re-sorted frame would break parity with the registered run."""
    q = p.copy()
    q["vc"] = q.boundary_layer_height * q.wind
    q["inv_vc"] = 1.0 / q.vc.clip(lower=1.0)
    srt = q.sort_values(["city", "date"])
    q["inv_vc_3d"] = (srt.groupby("city").inv_vc
                      .transform(lambda s: s.rolling(3, min_periods=1).mean())).reindex(q.index)
    q["aod_over_blh"] = q.aod / q.boundary_layer_height.clip(lower=10.0)
    assert (q.index == p.index).all()
    return q


def frame(synthetic_target: bool):
    import ladder_v2_confirm as lvc
    (st, p, met, geo_f, sat), meta, conf, dropped = lvc.union("maiac")
    if synthetic_target:
        from ladder_v2_rich import synthetic
        st, p = synthetic(st, p)
    p = physics(p)
    return st, p, met, geo_f, sat, meta, conf


def _require_registered():
    f = LD / "REGISTERED.json"
    if not f.exists() or not json.loads(f.read_text(encoding="utf-8")).get("osf"):
        raise SystemExit("REFUSED: learner-robustness scoring runs only after its registration is lodged")


def inject(preds: pd.DataFrame):
    import ladder_v2
    orig = ladder_v2.bagged_bud0

    def fake(p, feats, bag):
        return preds[["city", "date", "bud0"]].copy()
    ladder_v2.bagged_bud0 = fake
    return lambda: setattr(ladder_v2, "bagged_bud0", orig)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--export", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--score", action="store_true")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--bag", type=int, default=5)
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    LD.mkdir(parents=True, exist_ok=True)
    if a.export:
        if not a.synthetic:
            _require_registered()
        st, p, met, geo_f, sat, meta, conf = frame(a.synthetic)
        cols = ["city", "date", "pm25_city", *met, *geo_f, *sat]
        tag = "synthetic" if a.synthetic else "real"
        p[cols].to_parquet(LD / f"frame_{tag}.parquet", index=False)
        json.dump(dict(met=met, geo=geo_f, sat=sat, target=tag, cities=int(p.city.nunique())),
                  open(LD / f"frame_{tag}_columns.json", "w"), indent=1)
        print(f"exported {len(p):,} rows, {p.city.nunique()} cities -> frame_{tag}.parquet")
        return 0
    if a.score:
        _require_registered()
    import ladder_v2
    from ladder_v2 import run, boot_city, boot_cluster
    st, p, met, geo_f, sat, meta, conf = frame(a.dry_run)
    disc = sorted(set(st) - set(conf))
    tag = "learners_dryrun" if a.dry_run else "learners_REGISTERED"
    base_feats = met + geo_f + sat
    runs = {}

    # L0 through the injection path
    b0 = ladder_v2.bagged_bud0(p, base_feats, a.bag)
    b0.to_parquet(LD / f"pred_L0_{'synthetic' if a.dry_run else 'real'}.parquet", index=False)
    undo = inject(b0)
    try:
        runs["L0"] = run("maiac", a.splits, a.bag, "crossfit", True, "grid", a.boot, True,
                         frame=(st, p, met, geo_f, sat), meta=meta, score_cities=list(st))
    finally:
        undo()
    # L3: physics features appended (no injection)
    runs["L3"] = run("maiac", a.splits, a.bag, "crossfit", True, "grid", a.boot, True,
                     frame=(st, p, met, geo_f, sat + PHYS), meta=meta, score_cities=list(st))
    # L1, L2 from Kaggle
    for L in ("L1", "L2"):
        t = "synthetic" if a.dry_run else "real"
        shards = sorted(LD.glob(f"pred_{L}_{t}_shard*.parquet"))
        if not shards:
            print(f"  {L}: no pred_{L}_{t}_shard*.parquet, skipped"); continue
        pr = pd.concat([pd.read_parquet(f) for f in shards], ignore_index=True)
        pr["date"] = pd.to_datetime(pr.date); pr["city"] = pr.city.astype(str)
        assert not pr.duplicated(["city", "date"]).any(), f"{L}: shards overlap"
        if not a.dry_run:
            missing = sorted(set(b0.city) - set(pr.city))
            assert not missing, f"{L}: no predictions for {missing}"
        undo = inject(pr)
        try:
            runs[L] = run("maiac", a.splits, a.bag, "crossfit", True, "grid", a.boot, True,
                          frame=(st, p, met, geo_f, sat), meta=meta, score_cities=list(st))
        finally:
            undo()
    out = {"config": dict(splits=a.splits, bag=a.bag, boot=a.boot, learners=list(runs), phys=PHYS)}
    if not a.dry_run:
        R = pd.read_csv(OUTD / "confirm_REGISTERED_percity_reconstruction.csv", index_col=0)
        B = runs["L0"][1]["reconstruction"]
        cols = [c for c in R.columns if c.split("_")[0] in ("first2", "s36", "bg", "bgm2")]
        diff = (B.loc[R.index, cols] - R[cols]).abs().max().max()
        out["parity_L0_vs_ueyfr"] = float(diff)
        assert diff < 1e-9, f"L0 injection path does not reproduce ueyfr ({diff})"
    rng = np.random.default_rng(20260928)

    def summ(v, grp):
        v, grp = np.asarray(v, float), np.asarray(grp); k = ~np.isnan(v); v, grp = v[k], grp[k]
        bc, bk = boot_city(v, rng, a.boot), boot_cluster(v, grp, rng, a.boot)
        return dict(n=int(len(v)), median=float(np.median(v)),
                    city=[float(np.percentile(bc, 2.5)), float(np.percentile(bc, 97.5))],
                    cluster=[float(np.percentile(bk, 2.5)), float(np.percentile(bk, 97.5))])

    for L, (S, percity, _) in runs.items():
        S.to_csv(OUTD / f"{tag}_{L}_splits.csv", index=False)
        for armname in ("reconstruction", "prospective"):
            C = percity[armname]
            C.to_csv(OUTD / f"{tag}_{L}_percity_{armname}.csv")
            S0 = runs["L0"][0]; s0 = S0[S0.arm == armname]; sL = S[S.arm == armname]
            m = s0.merge(sL, on=["city", "seed"], suffixes=("_0", "_L"))
            m["skill_vs_L0"] = 100 * (m.Bud0_rmse_0 - m.Bud0_rmse_L) / m.Bud0_rmse_0
            D = m.groupby("city").skill_vs_L0.median().to_frame().join(meta[["cluster"]])
            for panel, cs in (("confirmation", conf), ("discovery", disc), ("pooled", list(C.index))):
                sub = C[C.index.isin(set(cs))]
                for col in ("first2_rmse", "s36_rmse", "bg_rmse", "bgm2_rmse", "bgm2_exceed",
                            "bgm2_tail"):
                    out[f"{L}.{armname}.{panel}.{col}"] = summ(sub[col], sub.cluster)
                d = D[D.index.isin(set(cs))]
                out[f"{L}.{armname}.{panel}.skill_vs_L0"] = summ(d.skill_vs_L0, d.cluster)
    jp = OUTD / f"{tag}_summary.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, jp)
    print(("dry run (synthetic target) complete -> " if a.dry_run else "-> ") + str(jp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
