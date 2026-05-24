"""
cross_product_v2.py — Pre-reg §6.3 cross-product annual-mean triangulation.

Pre-reg §6.3 verbatim:
  "Compare 2003–2022 annual means from: XGBoost v2 (extrapolation), Van
   Donkelaar V6GL02.04, GEOS-CF×0.536 (2019–2022), MERRA-2 (diagnostic
   only, per gotcha #17). Report pairwise MAE, bias, correlation."

This script handles the 2019–2025 overlap window (where v2 is trained
data — no extrapolation yet). The 2003–2018 v2 extension is deferred to
a separate pass that needs `dataset_v2_extrapolation_2003_2018.parquet`.

Five products compared:
  1. XGBoost v2 quantile median (q50, in-LOMO-prediction)
  2. Van Donkelaar V6GL02.04 (Hammer et al., 1km annual, CNN-derived)
  3. GEOS-CF × 0.536 (NASA GEOS-CF replay, scaled to Kandy ratio)
  4. CAMS × 0.5984 (ECMWF EAC4 reanalysis, scaled to KOALA/CAMS_2019 ratio)
  5. MERRA-2 reconstructed PM2.5 (sum of aerosol species, diagnostic only)

Outputs (under data/processed/stage1_v2/eda/):
  cross_product_annual_means_v2.csv
  cross_product_pairwise_metrics_v2.csv
  cross_product_v2_summary.txt
  results/figures/stage1_v2/eda/F_cross_product_annual.png
  results/figures/stage1_v2/eda/F_cross_product_pairwise.png

Usage:
  python -m src.stage1_satml.evaluation.cross_product_v2
  python src/stage1_satml/evaluation/cross_product_v2.py
"""

import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    PROC_DIR, RAW_DIR, FIGURES_DIR,
    KANDY_PINN_BBOX, KANDY_BBOX,
    CAMS_BIAS_FACTOR_FLAT, KANDY_GEOS_CF_RATIO,
    LOG_FORMAT, LOG_DATEFMT,
)
from src.stage1_satml.models.train_xgboost_v2 import rmse, mae, bias, r2

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("cross_product_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

V2_PREDS = PROC_DIR / "stage1_v2" / "training" / "predictions_lomo_v2.parquet"
VAND_DIR = RAW_DIR / "van_donkelaar"
GEOS_DIR = RAW_DIR / "geos_cf"
V1_MERGED = PROC_DIR / "merged" / "dataset_daily.parquet"
MERRA_DIR = RAW_DIR / "merra2"

OUT_DIR  = PROC_DIR / "stage1_v2" / "eda"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FIGS = FIGURES_DIR / "stage1_v2" / "eda"
OUT_FIGS.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────────────

def annual_v2() -> pd.Series:
    """v2 quantile-median annual mean (averaged across sensors and days)."""
    df = pd.read_parquet(V2_PREDS)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    return df.groupby("year")["xgb_q50"].mean().rename("v2_q50")


def annual_van_donkelaar() -> pd.Series:
    """VanD annual mean over KANDY_PINN_BBOX (15×15 km)."""
    files = sorted(VAND_DIR.glob("V6GL02.04.CNNPM25.AS.*.nc"))
    rows = []
    for f in files:
        # Filename: V6GL02.04.CNNPM25.AS.YYYY01-YYYY12.nc
        try:
            year = int(f.stem.split(".")[-1][:4])
        except (ValueError, IndexError):
            continue
        try:
            ds = xr.open_dataset(f)
        except Exception as e:
            log.warning(f"  skip {f.name}: {e}")
            continue
        sub = ds["PM25"].sel(
            lat=slice(KANDY_PINN_BBOX["lat_min"], KANDY_PINN_BBOX["lat_max"]),
            lon=slice(KANDY_PINN_BBOX["lon_min"], KANDY_PINN_BBOX["lon_max"]))
        v = float(sub.mean().values)
        rows.append((year, v))
        ds.close()
    if not rows:
        return pd.Series(dtype="float64", name="van_donkelaar")
    s = pd.Series({y: v for y, v in rows}, name="van_donkelaar")
    s.index.name = "year"
    return s.sort_index()


def annual_geos_cf_scaled() -> pd.Series:
    """Annual mean of GEOS-CF tavg1hr × Kandy ratio (0.536)."""
    csvs = sorted(GEOS_DIR.glob("kandy_geos_cf_*.csv"))
    parts = []
    for f in csvs:
        try:
            parts.append(pd.read_csv(f))
        except pd.errors.EmptyDataError:
            continue
    if not parts:
        return pd.Series(dtype="float64", name="geos_cf_scaled")
    h = pd.concat(parts, ignore_index=True)
    h["datetime"] = pd.to_datetime(h["datetime"])
    h["year"] = h["datetime"].dt.year
    annual = h.groupby("year")["PM25_RH35_GCC"].mean() * KANDY_GEOS_CF_RATIO
    return annual.rename("geos_cf_scaled")


def annual_cams_scaled() -> pd.Series:
    """Annual mean of CAMS raw × 0.5984 (v1 KOALA correction).
    v1 merged parquet's pm25_observed IS the corrected CAMS, so we use it
    directly (no need to back out + re-apply)."""
    if not V1_MERGED.exists():
        return pd.Series(dtype="float64", name="cams_scaled")
    df = pd.read_parquet(V1_MERGED)
    df["year"] = df.index.year
    annual = df.groupby("year")["pm25_observed"].mean()
    # v1's pm25_observed is already × CAMS_BIAS_FACTOR_FLAT; no re-scaling needed
    return annual.rename("cams_scaled")


def annual_merra2() -> pd.Series:
    """MERRA-2 reconstructed PM2.5 = 1.375·SO4 + OC + BC + DUSMASS25 + SSSMASS25
    summed in kg/kg, converted to µg/m³ (× 1e9 × air density).
    Diagnostic-only per CLAUDE.md gotcha #17 (r(CAMS, MERRA-2) = 0.177)."""
    csvs = sorted(MERRA_DIR.glob("merra2_aerosol_*.csv"))
    rows = []
    for f in csvs:
        try:
            year = int(f.stem.split("_")[-1])
        except ValueError:
            continue
        try:
            d = pd.read_csv(f)
        except pd.errors.EmptyDataError:
            continue
        # Reconstruction in kg/kg; multiply by 1e9 × air density (~1.225 kg/m³)
        # → µg/m³.
        species = ["SO4SMASS", "OCSMASS", "BCSMASS", "DUSMASS25", "SSSMASS25"]
        if not all(c in d.columns for c in species):
            log.warning(f"  {f.name}: missing species columns {set(species)-set(d.columns)}")
            continue
        # 1.375 × ammonium sulfate equivalent for SO4
        pm = (1.375 * d["SO4SMASS"] + d["OCSMASS"] + d["BCSMASS"]
              + d["DUSMASS25"] + d["SSSMASS25"]) * 1e9 * 1.225
        rows.append((year, float(pm.mean())))
    if not rows:
        return pd.Series(dtype="float64", name="merra2_reconstructed")
    s = pd.Series({y: v for y, v in rows}, name="merra2_reconstructed")
    s.index.name = "year"
    return s.sort_index()


# ─────────────────────────────────────────────────────────────────────────────
# Pairwise metrics
# ─────────────────────────────────────────────────────────────────────────────

def pairwise_table(annual_df: pd.DataFrame) -> pd.DataFrame:
    cols = list(annual_df.columns)
    rows = []
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if i >= j:
                continue
            sub = annual_df[[a, b]].dropna()
            if len(sub) < 3:
                continue
            x = sub[a].to_numpy(dtype=np.float64)
            y = sub[b].to_numpy(dtype=np.float64)
            rows.append({
                "product_a": a,
                "product_b": b,
                "n_years":   int(len(sub)),
                "rmse":      rmse(x, y),
                "mae":       mae(x, y),
                "bias_a_minus_b": bias(x, y),
                "pearson_r": float(sub[a].corr(sub[b], method="pearson")),
                "spearman_r": float(sub[a].corr(sub[b], method="spearman")),
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    log.info("── load five products ──")
    v2     = annual_v2()
    vand   = annual_van_donkelaar()
    geos   = annual_geos_cf_scaled()
    cams   = annual_cams_scaled()
    merra  = annual_merra2()
    for label, s in [("v2_q50", v2), ("van_donkelaar", vand),
                     ("geos_cf_scaled", geos), ("cams_scaled", cams),
                     ("merra2_reconstructed", merra)]:
        if len(s):
            log.info(f"  {label:<24} n={len(s):>2}  "
                     f"[{s.index.min()}–{s.index.max()}]  "
                     f"mean={s.mean():.2f}  range=[{s.min():.2f}, {s.max():.2f}]")
        else:
            log.warning(f"  {label}: EMPTY")

    annual_df = pd.DataFrame({
        "v2_q50":               v2,
        "van_donkelaar":        vand,
        "geos_cf_scaled":       geos,
        "cams_scaled":          cams,
        "merra2_reconstructed": merra,
    }).sort_index()
    annual_df.to_csv(OUT_DIR / "cross_product_annual_means_v2.csv")
    log.info(f"wrote {OUT_DIR / 'cross_product_annual_means_v2.csv'}")

    # ── 2019-2025 overlap (v2 in-training window) ──
    overlap = annual_df.loc[2019:2025].dropna(how="all")
    log.info("\n── annual means 2019–2025 (µg/m³) ──")
    log.info(overlap.round(2).to_string())

    # ── pairwise table (full available years) ──
    pw_full = pairwise_table(annual_df)
    pw_full["scope"] = "all_years_available"
    pw_overlap = pairwise_table(annual_df.loc[2019:2025])
    pw_overlap["scope"] = "2019_2025_v2_in_training"
    pw = pd.concat([pw_full, pw_overlap], ignore_index=True)
    pw.to_csv(OUT_DIR / "cross_product_pairwise_metrics_v2.csv", index=False)
    log.info(f"wrote {OUT_DIR / 'cross_product_pairwise_metrics_v2.csv'}")

    log.info("\n── pairwise metrics (2019-2025 overlap) ──")
    log.info(f"  {'A':<22} {'B':<22}  {'n':>3}  {'r':>6}  {'rmse':>5}  {'bias':>6}")
    for _, r in pw_overlap.iterrows():
        log.info(f"  {r['product_a']:<22} {r['product_b']:<22}  "
                 f"{r['n_years']:>3}  {r['pearson_r']:>+6.3f}  "
                 f"{r['rmse']:>5.2f}  {r['bias_a_minus_b']:>+6.2f}")

    # ── Annual-mean time-series figure ──
    fig, ax = plt.subplots(figsize=(9, 5))
    for col, marker, color in [
        ("v2_q50", "o", "#1f77b4"),
        ("van_donkelaar", "s", "#2ca02c"),
        ("geos_cf_scaled", "^", "#d62728"),
        ("cams_scaled", "v", "#ff7f0e"),
        ("merra2_reconstructed", "D", "#7f7f7f"),
    ]:
        s = annual_df[col].dropna()
        if not len(s):
            continue
        ax.plot(s.index, s.values, marker=marker, color=color,
                label=col, markersize=6, linewidth=1)
    ax.axhline(24.5225, linestyle=":", linewidth=0.8, color="black",
               label="KOALA anchor 24.5225 µg/m³")
    ax.set_xlabel("year"); ax.set_ylabel("annual mean PM2.5 (µg/m³)")
    ax.set_title("Cross-product annual-mean triangulation over Kandy (§6.3)")
    ax.legend(loc="upper right", fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_cross_product_annual.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_cross_product_annual.png'}")

    # ── Pairwise correlation matrix figure ──
    products = list(annual_df.columns)
    n = len(products)
    M = np.full((n, n), np.nan)
    for _, r in pw_full.iterrows():
        i, j = products.index(r["product_a"]), products.index(r["product_b"])
        M[i, j] = r["pearson_r"]; M[j, i] = r["pearson_r"]
    np.fill_diagonal(M, 1.0)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(products, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(products, fontsize=8)
    for i in range(n):
        for j in range(n):
            v = M[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:+.2f}", ha="center", va="center",
                        color="white" if abs(v) > 0.5 else "black", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.6, label="Pearson r")
    ax.set_title("Pairwise annual-mean Pearson r (all available years)")
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_cross_product_pairwise.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_cross_product_pairwise.png'}")

    # ── paper-ready text summary (plain-text, no tabulate dep) ──
    def _csvblock(df_in: pd.DataFrame, header: str) -> str:
        return f"\n## {header}\n\n```\n{df_in.round(3).to_csv(index=False)}```"

    lines = [
        "# Pre-reg §6.3 — Cross-product annual-mean triangulation\n",
        f"\n## Annual means (µg/m³), 2019–2025 overlap\n\n```\n{overlap.round(2).to_csv()}```",
        _csvblock(pw_overlap, "Pairwise metrics (2019–2025 overlap, n=v2-in-training years)"),
        _csvblock(pw_full, "Pairwise metrics (all available years per pair)"),
        "\n**Interpretation:**",
        "- v2_q50 is the XGBoost quantile-median LOMO prediction, FECT-anchored.",
        "- van_donkelaar is the independent satellite-CNN annual product over Kandy bbox.",
        "- geos_cf_scaled × 0.536 is the operational reanalysis baseline.",
        "- cams_scaled × 0.5984 is the legacy v1 KOALA-corrected CAMS.",
        "- merra2_reconstructed is DIAGNOSTIC ONLY (per gotcha #17, r(CAMS, MERRA-2)=0.177).",
        "- A reviewer asks: do the independent products agree with v2? Report the Pearson r and bias",
        "  with van_donkelaar — if r > 0.5 across 5 years it's a meaningful independent corroboration.",
    ]
    OUT_TXT = OUT_DIR / "cross_product_v2_summary.txt"
    OUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"wrote {OUT_TXT}")


if __name__ == "__main__":
    main()
