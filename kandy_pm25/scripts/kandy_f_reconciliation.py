"""kandy_f_reconciliation.py — establish the background/local split from evidence
instead of prior (2026-08-02).

WHY
---
`FRAC_LOCAL_YEAR = {2019:0.28, 2020:0.25, 2021:0.21, 2022:0.20, 2023:0.27}` is an
INPUT PRIOR. The claim audit called it the weakest number in the chain: the preprint
once said the split "is stable across years" (false — it is deliberately varied), the
year-to-year variation is reasoned rather than fitted, and 2019's 0.28 sits just outside
our own SBI 90% interval. Every attempt to fix the low-season partition defect has been
blocked by the requirement to hold this prior fixed (F.13, F.15).

The decision (user, 2026-08-02) is to let f move. This script assembles every
independent line of evidence on f so the adopted value is a reconciliation, not a
choice, and so the interval around it is honest.

THE SIX LINES
-------------
L1  COHERENCE BOUND (new, and the only hard one).
    A background cannot exceed the total. If B is flat within a day — which v2's is —
    then B_day <= min_h T(h), so the annual background is capped by the mean of the
    daily minima. That yields a HARD LOWER BOUND on f from the shipped T(t) alone,
    with no external assumption whatsoever. It has never been computed.

L2  NBRO ISLAND NETWORK (external instrument, F.14).
    24 stations in raw ug/m3. The LCS-corrected regional floor gives a measured
    background level; f follows as 1 - B_obs/T over the overlapping days. Wet season
    only (n=44 days), so it constrains the wet season, not the annual mean.

L3  VAN DONKELAAR RURAL FLOOR.
    The construction B originally used: P10 of the rural satellite box relative to the
    basin area mean. Sensorless and annual, but satellite-derived and not independent
    of the level anchor.

L4  SBI POSTERIOR (Track I).  f = 0.181 [0.10, 0.27]. Known to run low against the
    literature bracket at every locally dominated panel city where it can be checked,
    so it is treated as a soft lower line rather than a central estimate.

L5  LITERATURE BRACKET.  World Bank (2022) >50% transboundary across South Asia;
    Seneviratne (2017) PMF for Kandy, regional-dominated. Gives [0.15, 0.50).

L6  W2 ORIGIN CONTRAST (D1/D2).  FECT by air-mass origin: IGP-origin days ~27 ug/m3
    against SW-marine ~6.8. If the marine floor approximates the background and the
    IGP days approximate background-plus-local under loading, the contrast bounds the
    local share on clean days.

Run:  .venv/Scripts/python.exe scripts/kandy_f_reconciliation.py
Out:  data/processed/decomp/kandy_f_reconciliation.{csv,json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
OUT_CSV = DEC / "kandy_f_reconciliation.csv"
OUT_JSON = DEC / "kandy_f_reconciliation.json"

LOCKED = list(range(2019, 2024))
EXT = [2024, 2025, 2026]
LCS_SLOPE = 1.35
SBI = (0.181, 0.10, 0.27)
LIT = (0.15, 0.50)


def load_T(year: int) -> pd.DataFrame:
    s = "_drv" if year in EXT else ""
    t = pd.read_parquet(STG / "T_anchor" / f"T_kandy_hourly_{year}{s}.parquet")
    t["h"] = pd.to_datetime(t.datetime_utc, utc=True)
    t["date"] = t.h.dt.floor("D")
    return t[["h", "date", "T_q50"]]


def l1_coherence() -> dict:
    """Hard lower bound on f from B <= T with a within-day-flat background."""
    rows = []
    for y in LOCKED + EXT:
        try:
            t = load_T(y)
        except FileNotFoundError:
            continue
        g = t.groupby("date").T_q50.agg(["min", "mean"])
        g = g[g["mean"] > 0]
        # a flat daily background can be at most the day's minimum total
        f_day = 1.0 - g["min"] / g["mean"]
        rows.append({"year": y, "n_days": int(len(g)),
                     "f_min_flatB": float(np.average(f_day, weights=g["mean"])),
                     "f_min_flatB_median": float(f_day.median())})
    d = pd.DataFrame(rows)
    return {"per_year": d.to_dict("records"),
            "pooled": float(d.f_min_flatB.mean()),
            "note": "hard lower bound: a within-day-flat background cannot exceed the "
                    "day's minimum total. Uses only the shipped T(t); no external input."}


def l2_nbro() -> dict | None:
    csv = DEC / "kandy_background_nbro_check.csv"
    if not csv.exists():
        return None
    d = pd.read_csv(csv)
    d["date"] = pd.to_datetime(d.date, utc=True)
    floor_raw = float(d.p25.mean())
    floor_cor = floor_raw / LCS_SLOPE
    # total over the same days, from the shipped anchor
    tot = []
    for y in (2026, 2025):
        try:
            t = load_T(y)
        except FileNotFoundError:
            continue
        tt = t.groupby("date").T_q50.mean().reset_index()
        tot.append(tt)
    T = pd.concat(tot).drop_duplicates("date")
    m = d.merge(T, on="date", how="inner")
    if m.empty:
        return None
    return {"n_days": int(len(m)), "network_p25_raw": round(floor_raw, 2),
            "network_p25_lcs_corrected": round(floor_cor, 2),
            "model_total_same_days": round(float(m.T_q50.mean()), 2),
            "f_implied_raw": round(1 - floor_raw / float(m.T_q50.mean()), 3),
            "f_implied_lcs_corrected": round(1 - floor_cor / float(m.T_q50.mean()), 3),
            "season": "wet only (May-Jul overlap) — constrains the wet season, not the annual mean"}


def l3_vand() -> dict | None:
    p = STG / "vandonkelaar_kandy_annual.csv"
    if not p.exists():
        return None
    v = pd.read_csv(p).set_index("year")
    cols = {c.lower(): c for c in v.columns}
    basin = cols.get("basin_mean")
    floor = next((cols[c] for c in cols if "p10" in c or "floor" in c or "rural" in c), None)
    if basin is None or floor is None:
        return {"note": f"columns present: {list(v.columns)} — no rural-floor column found"}
    f = 1 - v[floor] / v[basin]
    return {"per_year": {int(y): round(float(x), 3) for y, x in f.items()},
            "mean": round(float(f.mean()), 3),
            "note": "rural satellite floor vs basin area mean; sensorless but not "
                    "independent of the level anchor"}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== f reconciliation: background vs local split from evidence ===\n")
    res = {}

    print("L1  COHERENCE BOUND (hard, internal, never computed before)")
    l1 = l1_coherence()
    res["L1_coherence"] = l1
    for r in l1["per_year"]:
        print(f"      {r['year']}: f >= {r['f_min_flatB']:.3f}  "
              f"(median day {r['f_min_flatB_median']:.3f}, n={r['n_days']} d)")
    print(f"    pooled hard lower bound on f: {l1['pooled']:.3f}")
    print("    -> ANY within-day-flat background implying a SMALLER f is incoherent.\n")

    print("L2  NBRO ISLAND NETWORK (external instrument)")
    l2 = l2_nbro()
    res["L2_nbro"] = l2
    if l2:
        print(f"      network P25 {l2['network_p25_raw']} raw / "
              f"{l2['network_p25_lcs_corrected']} LCS-corrected")
        print(f"      model total over the same {l2['n_days']} days: "
              f"{l2['model_total_same_days']}")
        print(f"      f implied: {l2['f_implied_raw']:.3f} raw | "
              f"{l2['f_implied_lcs_corrected']:.3f} corrected   [{l2['season']}]\n")
    else:
        print("      unavailable\n")

    print("L3  VAN DONKELAAR RURAL FLOOR")
    l3 = l3_vand()
    res["L3_vand"] = l3
    print(f"      {l3}\n" if l3 else "      unavailable\n")

    print("L4  SBI POSTERIOR (Track I)")
    res["L4_sbi"] = {"point": SBI[0], "ci90": [SBI[1], SBI[2]],
                     "caveat": "runs low against the literature bracket at every locally "
                               "dominated panel city; treat as a soft lower line"}
    print(f"      f = {SBI[0]} [{SBI[1]}, {SBI[2]}]  (known low-biased)\n")

    print("L5  LITERATURE BRACKET")
    res["L5_literature"] = {"range": list(LIT),
                            "sources": ["World Bank 2022 (>50% transboundary, South Asia)",
                                        "Seneviratne 2017 (Kandy PMF, regional-dominated)"]}
    print(f"      f in [{LIT[0]}, {LIT[1]})\n")

    print("L6  W2 ORIGIN CONTRAST")
    res["L6_w2"] = {"igp_origin_fect": 27.0, "sw_marine_fect": 6.8,
                    "ratio": round(6.8 / 27.0, 3),
                    "note": "marine floor / IGP-loaded day; the marine value approximates "
                            "a background, so on loaded days the local+regional excess is "
                            "large and f on CLEAN days is bounded above by 1 - 6.8/T_clean"}
    print(f"      IGP-origin 27.0 vs SW-marine 6.8 (ratio {6.8/27.0:.3f})\n")

    # ── reconciliation ───────────────────────────────────────────────────────
    lower = l1["pooled"]
    lines = {"L1 coherence (hard lower bound)": lower,
             "L4 SBI point": SBI[0],
             "L5 literature lower": LIT[0]}
    if l2:
        lines["L2 NBRO wet-season (LCS-corrected)"] = l2["f_implied_lcs_corrected"]
    if l3 and "mean" in l3:
        lines["L3 VanD rural floor"] = l3["mean"]

    print("=== RECONCILIATION ===")
    for k, v in sorted(lines.items(), key=lambda kv: kv[1]):
        flag = "  <-- HARD BOUND" if k.startswith("L1") else ""
        print(f"    {k:<40} {v:.3f}{flag}")
    viable = {k: v for k, v in lines.items() if v >= lower - 1e-9}
    print(f"\n    lines at or above the hard bound: {len(viable)} of {len(lines)}")
    below = [k for k, v in lines.items() if v < lower - 1e-9]
    if below:
        print(f"    EXCLUDED BY COHERENCE: {below}")
        print("    (these cannot be reconciled with the shipped T(t) under a flat daily B)")
    res["reconciliation"] = {"hard_lower_bound": round(lower, 3),
                             "lines": {k: round(v, 3) for k, v in lines.items()},
                             "excluded_by_coherence": below}

    OUT_JSON.write_text(json.dumps(res, indent=1), encoding="utf-8")
    pd.DataFrame(l1["per_year"]).to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_JSON.name} + {OUT_CSV.name}")


if __name__ == "__main__":
    main()
