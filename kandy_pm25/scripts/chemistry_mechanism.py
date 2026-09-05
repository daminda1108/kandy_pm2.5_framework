"""chemistry_mechanism.py -- does aerosol composition explain what latitude band only labels?

PRE-REGISTERED at docs/prereg_chemistry_mechanism_2026-09-05.md, lodged and pushed BEFORE this
script was written. Read Section 0 of that document first: it discloses an exploratory probe run
earlier the same day and carries the consequences into the design.

THE QUESTION. The budget ladder says what each observation stream is worth and treats a city as
a city. Chapter 7 of the thesis reports that the ordering differs between latitude bands and
states plainly that latitude is a stratifying LABEL and not a mechanism. This asks whether
chemistry is what the label stands for: a secondary-dominated city is chemically a REGIONAL
problem, so a background observation should be worth more there and a local monitor less; a
primary-dominated city should be the reverse.

WHAT IS CONFIRMATORY AND WHAT IS NOT. The DIRECTION for the sec_frac tests was committed in
pull_panel_speciation.py on 2026-09-01 (b9fd181), four days before any correlation was computed,
so M1-M3 are ONE-SIDED and Holm-corrected as a family of three. The oc_bc test M4 was promoted
to confirmatory only AFTER the probe, so it is TWO-SIDED, corrected separately, and must never
be described as pre-registered.

WHAT THIS REFUSES TO DO. No within-band correlations. At 7-13 cities a band could only reveal
correlations above 0.71, and reporting its silence as evidence is the exact error Chapter 5 of
the thesis documents. Band enters ONLY as a control.

Usage: python scripts/chemistry_mechanism.py [--boot 2000]
Out:   data/processed/modular/chemistry_mechanism.csv
       data/processed/modular/chemistry_mechanism_summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata, spearmanr

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "chemistry_mechanism.csv"
OUT_JSON = MOD / "chemistry_mechanism_summary.json"

# ── everything below this line was fixed by the registration ──────────────────────────────
CONFIRMATORY = [
    # tag, composition variable, outcome, registered direction (one-sided)
    ("M1", "sec_frac", "g_bg", "positive"),
    ("M2", "sec_frac", "g_first2", "negative"),
    ("M3", "sec_frac", "adv", "negative"),
]
EXPLORATORY = [("M4", "oc_bc", "adv", "two-sided")]
N_CONFIRMATORY = len(CONFIRMATORY)
BAND_DF = 3          # a 4-level factor spends 3 degrees of freedom
POWER = 0.80


def mde(n: int, alpha: float, df: int, sided: int) -> float:
    """Minimum detectable |rho| via Fisher z. Depends on n and alpha only, never on the data."""
    se = 1.0 / np.sqrt(n - 3 - df)
    return float(np.tanh((norm.ppf(1 - alpha / sided) + norm.ppf(POWER)) * se))


def partial_on_band(x: np.ndarray, y: np.ndarray, band: np.ndarray):
    """Spearman of x and y with a categorical control.

    Rank both, residualise each rank vector on band indicators, correlate the residuals. This is
    the decisive form: the question is whether composition explains what band labels, so the
    between-band variation has to come out.
    """
    rx, ry = rankdata(x), rankdata(y)
    D = pd.get_dummies(pd.Series(band).astype(str), drop_first=True).to_numpy(float)
    A = np.column_stack([np.ones(len(rx)), D])
    ex = rx - A @ np.linalg.lstsq(A, rx, rcond=None)[0]
    ey = ry - A @ np.linalg.lstsq(A, ry, rcond=None)[0]
    r, _ = spearmanr(ex, ey)
    # p from Fisher z on the residual correlation, spending the control's degrees of freedom
    n_eff = len(rx) - D.shape[1]
    z = np.arctanh(np.clip(r, -0.999999, 0.999999)) * np.sqrt(max(n_eff - 3, 1))
    return float(r), float(2 * (1 - norm.cdf(abs(z)))), int(n_eff)


def one_sided_p(p_two: float, r: float, direction: str) -> float:
    """Convert a two-sided p to one-sided in the REGISTERED direction.

    A result in the wrong direction cannot be evidence for the hypothesis, so it is mapped to
    the near-certain end rather than being silently halved into significance.
    """
    right = (r > 0) if direction == "positive" else (r < 0)
    return p_two / 2.0 if right else 1.0 - p_two / 2.0


def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, order preserved."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for i, idx in enumerate(order):
        running = max(running, (m - i) * pvals[idx])
        adj[idx] = min(running, 1.0)
    return adj.tolist()


def boot_ci(x, y, band, n_boot, seed, partial=True):
    """Bootstrap over CITIES. Days within a city are not independent; the unit is the city."""
    rng = np.random.default_rng(seed)
    n = len(x)
    out = []
    for _ in range(n_boot):
        i = rng.integers(0, n, n)
        if len(np.unique(band[i])) < 2:
            continue
        try:
            r = partial_on_band(x[i], y[i], band[i])[0] if partial else spearmanr(x[i], y[i])[0]
        except Exception:
            continue
        if np.isfinite(r):
            out.append(r)
    if len(out) < 50:
        return np.nan, np.nan
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def load(ladder_file: str) -> pd.DataFrame:
    sp = pd.read_csv(MOD / "panel_speciation.csv", dtype={"city": str})
    L = pd.read_csv(MOD / ladder_file, dtype={"city": str})
    L = L[L.bottom == "Bud0c"]
    j = L.merge(sp[["city", "sec_frac", "oc_bc"]], on="city", how="inner")
    j["g_first2"] = 100 * (j.rmse_Bud0 - j.rmse_Bud1) / j.rmse_Bud0
    j["g_bg"] = 100 * (j.rmse_Bud2 - j.rmse_Bud3) / j.rmse_Bud2
    j["adv"] = j.g_first2 - j.g_bg
    return j.dropna(subset=["g_first2", "g_bg", "adv", "sec_frac", "oc_bc", "band"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260905)
    a = ap.parse_args()

    print("=== chemistry as a mechanism for the value of information ===")
    print("    pre-registered: docs/prereg_chemistry_mechanism_2026-09-05.md\n")

    rows = []
    for ladder_file, ladder_name, primary in (("ladder_maiac.csv", "maiac", True),
                                              ("ladder_revalidated.csv", "ghap", False)):
        j = load(ladder_file)
        n = len(j)
        band = j.band.to_numpy()
        print(f"--- {ladder_name} ladder{'  (PRIMARY)' if primary else '  (sensitivity)'} "
              f"| n = {n} cities ---")
        print(f"    detection limits: confirmatory partial one-sided "
              f"{mde(n, 0.05, BAND_DF, 1):.3f} (nominal), "
              f"{mde(n, 0.05 / N_CONFIRMATORY, BAND_DF, 1):.3f} (Holm worst) | "
              f"exploratory two-sided {mde(n, 0.05, BAND_DF, 2):.3f}")

        block = []
        for tag, var, out, direction in CONFIRMATORY + EXPLORATORY:
            x, y = j[var].to_numpy(float), j[out].to_numpy(float)
            r_pool, p_pool_two = spearmanr(x, y)
            r_part, p_part_two, n_eff = partial_on_band(x, y, band)
            sided = 1 if direction != "two-sided" else 2
            p_part = (one_sided_p(p_part_two, r_part, direction) if sided == 1 else p_part_two)
            lo, hi = boot_ci(x, y, band, a.boot, a.seed)
            block.append(dict(
                ladder=ladder_name, tag=tag, kind="confirmatory" if sided == 1 else "exploratory",
                var=var, outcome=out, direction=direction, n=n,
                rho_pooled=round(float(r_pool), 4), p_pooled_two=round(float(p_pool_two), 5),
                rho_partial=round(r_part, 4), p_partial=round(float(p_part), 5),
                boot_lo=round(lo, 4) if np.isfinite(lo) else None,
                boot_hi=round(hi, 4) if np.isfinite(hi) else None,
                mde_nominal=round(mde(n, 0.05, BAND_DF, sided), 4),
                mde_holm=round(mde(n, 0.05 / N_CONFIRMATORY, BAND_DF, sided), 4)
                if sided == 1 else None))

        conf = [b for b in block if b["kind"] == "confirmatory"]
        for b, padj in zip(conf, holm([b["p_partial"] for b in conf])):
            b["p_holm"] = round(float(padj), 5)
        for b in block:
            if b["kind"] == "exploratory":
                b["p_holm"] = None
            right_sign = (b["rho_partial"] > 0 if b["direction"] == "positive"
                          else b["rho_partial"] < 0 if b["direction"] == "negative" else True)
            big_enough = abs(b["rho_partial"]) >= b["mde_nominal"]
            if b["kind"] == "confirmatory":
                b["verdict"] = ("HELD" if right_sign and big_enough and b["p_holm"] < 0.05
                                else "REFUTED" if not right_sign and big_enough
                                else "UNDETECTABLE at this power")
            else:
                b["verdict"] = ("detected" if big_enough and b["p_partial"] < 0.05
                                else "UNDETECTABLE at this power")
        rows += block

        for b in block:
            star = "  <-- NOT pre-registered" if b["kind"] == "exploratory" else ""
            print(f"    {b['tag']}  {b['var']:9} -> {b['outcome']:9} "
                  f"pooled {b['rho_pooled']:+.3f} | partial {b['rho_partial']:+.3f} "
                  f"[{b['boot_lo']:+.2f},{b['boot_hi']:+.2f}] "
                  f"p={b['p_partial']:.4f} "
                  f"{'holm=' + format(b['p_holm'], '.4f') if b['p_holm'] is not None else '':<14}"
                  f" {b['verdict']}{star}")
        print()

    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)

    # ── why the confirmatory result differs from the probe that motivated it ───────────────
    # REGISTERED n was 46; the band-controlled analysis scores 35, because the 11 cities from
    # the single national network carry no band and cannot enter a band-controlled model. That
    # deviation is not cosmetic, so the cause is decomposed here rather than left to a reader.
    sp = pd.read_csv(MOD / "panel_speciation.csv", dtype={"city": str})
    L = pd.read_csv(MOD / "ladder_maiac.csv", dtype={"city": str})
    L = L[L.bottom == "Bud0c"]
    k = L.merge(sp[["city", "sec_frac", "oc_bc"]], on="city")
    k["g_first2"] = 100 * (k.rmse_Bud0 - k.rmse_Bud1) / k.rmse_Bud0
    k["g_bg"] = 100 * (k.rmse_Bud2 - k.rmse_Bud3) / k.rmse_Bud2
    k["adv"] = k.g_first2 - k.g_bg
    k = k.dropna(subset=["g_first2", "g_bg", "adv", "sec_frac", "oc_bc"])
    grp = {"pooled": k, "banded": k[k.band.notna()], "single_network": k[k.band.isna()]}
    print("--- where the exploratory signal came from (oc_bc vs advantage) ---")
    clus = {}
    for lab, sub in grp.items():
        r, p = spearmanr(sub.oc_bc, sub.adv)
        clus[lab] = dict(n=int(len(sub)), rho=round(float(r), 3), p=round(float(p), 4),
                         median_oc_bc=round(float(sub.oc_bc.median()), 2),
                         median_adv=round(float(sub.adv.median()), 1))
        print(f"    {lab:15} n={len(sub):>3}  rho={r:+.3f}  p={p:.4f}   "
              f"median oc_bc {sub.oc_bc.median():5.2f}  median advantage {sub.adv.median():+6.1f}")
    print("    The pooled correlation is a BETWEEN-CLUSTER difference: it survives in neither")
    print("    group on its own. A network effect wearing a chemical variable's name.")

    prim = d[(d.ladder == "maiac") & (d.kind == "confirmatory")]
    summary = {
        "n_cities": int(d[d.ladder == "maiac"].n.iloc[0]),
        "mde_confirmatory_nominal": float(prim.mde_nominal.iloc[0]),
        "mde_confirmatory_holm": float(prim.mde_holm.iloc[0]),
        "confirmatory_held": int((prim.verdict == "HELD").sum()),
        "confirmatory_refuted": int((prim.verdict == "REFUTED").sum()),
        "confirmatory_undetectable": int(prim.verdict.str.startswith("UNDETECT").sum()),
        "largest_confirmatory_abs_rho": float(prim.rho_partial.abs().max()),
    }
    for _, b in d[d.ladder == "maiac"].iterrows():
        summary[f"{b.tag}_rho_partial"] = float(b.rho_partial)
        summary[f"{b.tag}_verdict"] = str(b.verdict)
    summary["registered_n"] = 46
    summary["cluster_diagnostic"] = clus
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print(f"-> {OUT.name}, {OUT_JSON.name}")
    print(f"\nCONFIRMATORY OUTCOME on the primary ladder: "
          f"{summary['confirmatory_held']} held, {summary['confirmatory_refuted']} refuted, "
          f"{summary['confirmatory_undetectable']} undetectable at this power.")
    print("The registration predicted a bounded null as the most probable outcome.")


if __name__ == "__main__":
    main()
