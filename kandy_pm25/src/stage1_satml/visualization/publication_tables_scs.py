"""
publication_tables_scs.py — RECAP + CREST paper tables T1-T10 (SCS spec).

Outputs both .csv (machine-readable) and .tex (LaTeX booktabs) for each table.

Usage:
    python src/stage1_satml/visualization/publication_tables_scs.py --all
    python src/stage1_satml/visualization/publication_tables_scs.py --table T1 T3 T7
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

OUT = HERE / "results" / "tables" / "publication_scs"
OUT.mkdir(parents=True, exist_ok=True)

DATA = HERE / "data" / "processed" / "stage1_v2"
STAGE2 = HERE / "data" / "processed" / "stage2"


def _save(df: pd.DataFrame, name: str, float_fmt: str = "%.3f", index=False):
    csv_path = OUT / f"{name}.csv"
    tex_path = OUT / f"{name}.tex"
    df.to_csv(csv_path, index=index, float_format=float_fmt)
    try:
        df.to_latex(tex_path, index=index, float_format=float_fmt,
                    escape=True, longtable=False)
    except Exception as e:
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(f"% Could not auto-generate LaTeX: {e}\n")
            f.write(df.to_string(index=index))
    print(f"  {name} -> {csv_path.name} + {tex_path.name}")


# ────────────────────────────────────────────────────────────────────────────
# T1 — Feature inventory (28 features)
# ────────────────────────────────────────────────────────────────────────────
def tbl_T1():
    fp = pd.read_csv(DATA / "feature_provenance_v2.csv")
    units_map = {
        "wind_speed_10m": "m s⁻¹", "blh_era5": "m", "ventilation_coefficient": "m² s⁻¹",
        "lapse_rate_t925_t2m": "K", "nocturnal_blh_ratio": "—",
        "wind_along_corridor": "m s⁻¹", "wind_cross_corridor": "m s⁻¹",
        "wind_into_blocked_sector": "m s⁻¹", "valley_drainage_index": "—",
        "precip_24h": "mm", "precip_7d": "mm", "dry_spell_days": "d",
        "aod_maiac": "—", "aod_blh_ratio": "m⁻¹", "no2_column": "mol m⁻²",
        "fire_count_5d": "count", "cams_pm25_raw": "µg m⁻³",
        "geos_cf_pm25_raw": "µg m⁻³", "prior_disagreement": "µg m⁻³",
        "mei_sin": "—", "mei_cos": "—", "iod_dmi": "K", "mjo_amplitude": "—",
        "pm25_lag_1d": "µg m⁻³", "pm25_lag_7d_mean": "µg m⁻³",
        "pm25_lag_30d_mean": "µg m⁻³", "doy_sin": "—", "doy_cos": "—",
    }
    res_map = {
        "ERA5": "hourly→daily", "MODIS MAIAC": "daily",
        "TROPOMI L3": "daily (overpass)", "VIIRS": "daily",
        "CAMS EAC4": "3h→daily", "GEOS-CF": "1h→daily",
        "NOAA PSL": "monthly→daily", "BoM RMM": "daily",
        "calendar": "daily", "derived": "daily", "FECT": "hourly→daily",
    }
    def _res(src):
        for k, v in res_map.items():
            if k in src: return v
        return "daily"
    fp["unit"] = fp["feature"].map(units_map).fillna("—")
    fp["time_resolution"] = fp["source"].map(_res)
    fp["pre_2018_missing_pct"] = (fp["frac_nan"] * 100).round(2)
    out = fp[["feature", "group", "source", "derivation",
              "unit", "time_resolution", "pre_2018_missing_pct"]].copy()
    out.columns = ["Feature", "Group", "Source", "Formula / derivation",
                   "Unit", "Time resolution", "Missingness (%) full record"]
    _save(out, "T1_feature_inventory", float_fmt="%.2f")


# ────────────────────────────────────────────────────────────────────────────
# T2 — LOMO per-month + pooled metrics with bootstrap CIs
# ────────────────────────────────────────────────────────────────────────────
def tbl_T2():
    pm = pd.read_csv(DATA / "training" / "metrics_per_month_v2.csv")
    xgb_m = pm[pm["model"] == "xgboost_v2"][
        ["calendar_month", "n_obs", "rmse", "mae", "bias", "r2", "cov90", "pi_width"]
    ].copy()
    xgb_m = xgb_m.sort_values("calendar_month").reset_index(drop=True)
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]
    xgb_m["month"] = xgb_m["calendar_month"].apply(lambda m: month_labels[m-1])
    xgb_m = xgb_m[["month", "n_obs", "rmse", "mae", "bias", "r2", "cov90", "pi_width"]]

    ci = pd.read_csv(DATA / "training" / "bootstrap_ci_v2.csv")
    kandy = ci[(ci["config"] == "xgboost_v2_quantile (Kandy LOMO)") &
               (ci["model"] == "primary")]
    pooled_rows = []
    for metric in ["rmse", "mae", "bias", "r2", "cov90", "pi_width", "crps"]:
        r = kandy[kandy["metric"] == metric]
        if r.empty: continue
        pooled_rows.append({
            "metric": metric.upper(),
            "point": r["point"].values[0],
            "ci_low_95": r["ci_low"].values[0],
            "ci_high_95": r["ci_high"].values[0],
        })
    pooled = pd.DataFrame(pooled_rows)

    _save(xgb_m, "T2a_lomo_per_month", float_fmt="%.3f")
    _save(pooled, "T2b_lomo_pooled_bootstrap_ci", float_fmt="%.3f")


# ────────────────────────────────────────────────────────────────────────────
# T3 — Baseline comparison
# ────────────────────────────────────────────────────────────────────────────
def tbl_T3():
    ci = pd.read_csv(DATA / "training" / "bootstrap_ci_v2.csv")
    kandy = ci[ci["config"] == "xgboost_v2_quantile (Kandy LOMO)"]
    summary = pd.read_csv(DATA / "training" / "summary_v2.csv")

    pivot = (kandy.pivot_table(index="model", columns="metric",
                                values=["point", "ci_low", "ci_high"])
                  .reset_index())
    pivot.columns = ["_".join([str(c) for c in col if c]).strip("_")
                     for col in pivot.columns]

    name_map = {
        "primary": "RECAP (quantile XGBoost)",
        "baseline_persistence": "Persistence",
        "baseline_doy_clim": "DOY climatology",
        "baseline_cams_scaled": "CAMS-scaled",
        "baseline_geos_scaled": "GEOS-CF-scaled",
    }
    pivot["Model"] = pivot["model"].map(name_map).fillna(pivot["model"])

    summary_lookup = summary.set_index("model")
    def _cov(m):
        m2 = {"primary": "xgboost_v2", "baseline_persistence": "persistence",
              "baseline_doy_clim": "doy_clim",
              "baseline_cams_scaled": "cams_scaled",
              "baseline_geos_scaled": "geos_scaled"}.get(m, m)
        try:
            return summary_lookup.loc[m2, "cov90_mean"]
        except Exception:
            return np.nan

    rows = []
    order = ["primary", "baseline_persistence", "baseline_doy_clim",
             "baseline_cams_scaled", "baseline_geos_scaled"]
    for m in order:
        sub = pivot[pivot["model"] == m]
        if sub.empty: continue
        row = sub.iloc[0]
        rows.append({
            "Model": row["Model"],
            "RMSE": row.get("point_rmse"),
            "RMSE 95% CI lo": row.get("ci_low_rmse"),
            "RMSE 95% CI hi": row.get("ci_high_rmse"),
            "R²": row.get("point_r2"),
            "R² 95% CI lo": row.get("ci_low_r2"),
            "R² 95% CI hi": row.get("ci_high_r2"),
            "cov90": _cov(m),
        })
    out = pd.DataFrame(rows)
    _save(out, "T3_baseline_comparison", float_fmt="%.3f")


# ────────────────────────────────────────────────────────────────────────────
# T4 — Feature-group ablation
# ────────────────────────────────────────────────────────────────────────────
def tbl_T4():
    abl = pd.read_csv(DATA / "training" / "ablation_comparison_v2.csv")
    base = abl[abl["label"] == "v2.1_full_features"].iloc[0]
    base_rmse = base["xgb_pooled_rmse"]
    nice = {
        "drop_G_temporal":      "G — temporal (lags + DOY)",
        "no_reanalysis":        "E — reanalysis priors (CAMS+GEOS)",
        "drop_C_wet_scavenging": "C — wet scavenging (precip)",
        "no_cams_only":         "E — CAMS only",
        "no_geos_only":         "E — GEOS-CF only",
        "drop_station_latlonelev": "STATION — coordinates",
        "drop_A_ventilation":   "A — ventilation",
        "drop_F_climate_modes": "F — climate modes",
        "drop_D_source_column": "D — source column (AOD/NO₂)",
        "drop_B_valley_transport": "B — valley transport",
        "no_prior_disagree":    "E — prior disagreement",
        "v2.1_full_features":   "Full model (baseline)",
    }
    drop = abl.copy()
    drop["Group"] = drop["label"].map(nice).fillna(drop["label"])
    drop["ΔRMSE (µg m⁻³)"] = drop["xgb_pooled_rmse"] - base_rmse
    drop["ΔRMSE (%)"] = drop["ΔRMSE (µg m⁻³)"] / base_rmse * 100
    drop = drop.sort_values("ΔRMSE (µg m⁻³)", ascending=False)
    drop["Rank"] = range(1, len(drop) + 1)
    out = drop[["Rank", "Group", "n_features", "xgb_pooled_rmse",
                "ΔRMSE (µg m⁻³)", "ΔRMSE (%)",
                "xgb_pooled_r2", "xgb_cov90"]].copy()
    out.columns = ["Rank", "Group (dropped)", "n features (kept)",
                   "RMSE", "ΔRMSE (µg m⁻³)", "ΔRMSE (%)", "R²", "cov90"]
    _save(out, "T4_ablation", float_fmt="%.3f")


# ────────────────────────────────────────────────────────────────────────────
# T5 — Embassy Colombo OOD per-year
# ────────────────────────────────────────────────────────────────────────────
def tbl_T5():
    m = pd.read_csv(DATA / "training" / "metrics_colombo_v2.csv")
    xgb = m[(m["model"] == "xgboost_v2_quantile") &
            (m["scope"].str.startswith("year_") | (m["scope"] == "pooled"))].copy()
    xgb["scope_lbl"] = xgb["scope"].str.replace("year_", "")
    out = xgb[["scope_lbl", "n", "rmse", "mae", "bias", "r2", "cov90", "pi_width", "crps"]].copy()
    out.columns = ["Period", "N", "RMSE", "MAE", "Bias", "R²", "cov90", "PI width", "CRPS"]
    out["H4 cov90 ∈ [0.85, 0.95]"] = out["cov90"].apply(
        lambda c: "PASS" if 0.85 <= c <= 0.95 else "FAIL")
    _save(out, "T5_ood_embassy_per_year", float_fmt="%.3f")


# ────────────────────────────────────────────────────────────────────────────
# T6 — Cross-product triangulation (annual + pairwise r)
# ────────────────────────────────────────────────────────────────────────────
def tbl_T6():
    cp = pd.read_csv(DATA / "eda" / "cross_product_22yr_v2.csv")
    cp_a = cp[cp["year"] >= 2003].copy()
    out_a = cp_a[["year", "v2_q50_22yr", "van_donkelaar",
                  "geos_cf_scaled", "cams_scaled", "merra2_reconstructed"]].copy()
    out_a.columns = ["Year", "RECAP q50", "Van Donkelaar V6GL02",
                     "GEOS-CF×0.536", "CAMS×0.598", "MERRA-2 reconstructed"]

    pw = pd.read_csv(DATA / "eda" / "cross_product_pairwise_metrics_v2.csv")
    pw_all = pw[pw["scope"] == "all_years_available"][
        ["product_a", "product_b", "n_years", "pearson_r",
         "rmse", "bias_a_minus_b"]
    ].copy()
    pw_all.columns = ["Product A", "Product B", "N years",
                      "Pearson r", "RMSE", "Bias (A−B)"]
    _save(out_a, "T6a_annual_cross_product", float_fmt="%.2f")
    _save(pw_all, "T6b_pairwise_metrics", float_fmt="%.3f")

    products = ["v2_q50_22yr", "van_donkelaar", "geos_cf_scaled",
                "cams_scaled", "merra2_reconstructed"]
    corr = cp_a[products].corr()
    corr.index = ["RECAP", "VanD", "GEOS-CF×", "CAMS×", "MERRA-2"]
    corr.columns = corr.index
    _save(corr.reset_index().rename(columns={"index": "Product"}),
          "T6c_pearson_r_matrix", float_fmt="%.3f")


# ────────────────────────────────────────────────────────────────────────────
# T7 — CREST LOOCV v10 vs v11
# ────────────────────────────────────────────────────────────────────────────
def tbl_T7():
    v10 = pd.read_csv(STAGE2 / "kaggle_logs" / "convcnp_v10" /
                      "convcnp_v10_loocv_aggregate.csv")
    v11 = pd.read_csv(STAGE2 / "kaggle_logs" / "convcnp_v11" /
                      "convcnp_v11_loocv_aggregate.csv")
    v10["version"] = "v10"; v11["version"] = "v11"
    merged = pd.merge(v10, v11, on="city", suffixes=("_v10", "_v11"))

    gate_map = {
        "medellin":  ("G3: r ≥ 0.30",
                      lambda r: "PASS" if r >= 0.30 else "FAIL"),
        "chiangmai": ("G2: r ≥ 0.50",
                      lambda r: "PASS" if r >= 0.50 else "FAIL"),
        "kathmandu": ("G1: r ≥ 0.50",
                      lambda r: "PASS" if r >= 0.50 else "FAIL"),
    }
    rows = []
    for _, r in merged.iterrows():
        c = r["city"]; gate_lbl, gate_fn = gate_map[c]
        rows.append({
            "City": {"medellin": "Medellín", "chiangmai": "Chiang Mai",
                     "kathmandu": "Kathmandu"}[c],
            "r v10": r["r_mean_v10"],
            "r v11": r["r_mean_v11"],
            "Δr (v11−v10)": r["r_mean_v11"] - r["r_mean_v10"],
            "bias v10": r["bias_mean_v10"],
            "bias v11": r["bias_mean_v11"],
            "Δbias": r["bias_mean_v11"] - r["bias_mean_v10"],
            "cov90 v10": r["cov90_mean_v10"],
            "cov90 v11": r["cov90_mean_v11"],
            "Gate (r)": gate_lbl,
            "v10 status": gate_fn(r["r_mean_v10"]),
            "v11 status": gate_fn(r["r_mean_v11"]),
        })
    out = pd.DataFrame(rows)
    _save(out, "T7_crest_v10_vs_v11", float_fmt="%.3f")


# ────────────────────────────────────────────────────────────────────────────
# T8 — Stage D Kandy consistency anchors (pending)
# ────────────────────────────────────────────────────────────────────────────
def tbl_T8():
    rows = [
        {"Anchor": "Annual mean PM₂.₅ vs Senarathna 2024 KOALA",
         "Threshold": "Within ±5 µg m⁻³ of 24.5 µg m⁻³",
         "Observed": "pending",
         "Status": "PENDING — Stage D not run"},
        {"Anchor": "Diurnal cycle r vs published diurnal pattern",
         "Threshold": "r ≥ 0.70",
         "Observed": "pending",
         "Status": "PENDING"},
        {"Anchor": "MAIAC AOD spatial-gradient r",
         "Threshold": "r ≥ 0.40 with predicted PM₂.₅ field",
         "Observed": "pending",
         "Status": "PENDING"},
        {"Anchor": "Van Donkelaar V6GL02 spatial overlay",
         "Threshold": "Annual mean within ±25 % at 1 km pixel",
         "Observed": "pending",
         "Status": "PENDING"},
        {"Anchor": "MERRA-2 reanalysis envelope",
         "Threshold": "Annual mean within ±50 %",
         "Observed": "pending",
         "Status": "PENDING"},
    ]
    out = pd.DataFrame(rows)
    out["Date checked"] = "—"
    _save(out, "T8_stage_d_anchors", float_fmt="%.3f")


# ────────────────────────────────────────────────────────────────────────────
# T9 — Pre-registered hypotheses H1–H4
# ────────────────────────────────────────────────────────────────────────────
def tbl_T9():
    rows = [
        {"Hypothesis": "H1 — RECAP beats scaled GEOS-CF baseline by ≥15 % RMSE",
         "Criterion": "(RMSE_GEOS − RMSE_RECAP) / RMSE_GEOS ≥ 0.15",
         "Observed": "−59.8 % vs GEOS-CF (5.73 vs 14.24)",
         "Status": "PASS",
         "Date checked": "2026-05-17"},
        {"Hypothesis": "H2 — Pooled cov90 ∈ [0.85, 0.95]",
         "Criterion": "0.85 ≤ pooled cov90 ≤ 0.95",
         "Observed": "0.889 (LOMO pooled)",
         "Status": "PASS",
         "Date checked": "2026-05-17"},
        {"Hypothesis": "H3 — Pooled R² ≥ 0.60",
         "Criterion": "Pooled R² ≥ 0.60",
         "Observed": "0.689 (LOMO pooled)",
         "Status": "PASS",
         "Date checked": "2026-05-17"},
        {"Hypothesis": "H4 — OOD cov90 at Embassy Colombo ∈ [0.85, 0.95]",
         "Criterion": "0.85 ≤ cov90 ≤ 0.95 at independent OOD site",
         "Observed": "0.861 (pooled 2019–2025)",
         "Status": "PASS",
         "Date checked": "2026-05-18"},
    ]
    _save(pd.DataFrame(rows), "T9_pre_reg_hypotheses")


# ────────────────────────────────────────────────────────────────────────────
# T10 — Pivots summary
# ────────────────────────────────────────────────────────────────────────────
def tbl_T10():
    rows = [
        {"#": "P1",
         "Original commitment": "100 m / 30 min native resolution",
         "What we tried": "Multiple super-resolution + PINN regularisation attempts",
         "What we learned": "Insufficient ground truth + compute for sub-km hourly skill",
         "What changed": "Retired headline; native = 1 km hourly + optional 100 m presentation",
         "Justification": "Honest resolution claim; resolves PINN spatial-skill collapse"},
        {"#": "P2",
         "Original commitment": "CAMS as the calibration label",
         "What we tried": "CAMS-as-label with KOALA flat-annual bias correction (Stage 1 v1)",
         "What we learned": "Circularity: KOALA used to calibrate label AND validate",
         "What changed": "Re-cast CAMS + GEOS-CF as features; FECT-Barkjohn as labels",
         "Justification": "Independent validation chain; FECT calibrated to EPA reference"},
        {"#": "P3",
         "Original commitment": "PINN-based spatial reconstruction (SharedTerrainAnsatz)",
         "What we tried": "Rigid Whiteman-style 6-parameter ansatz; trained Mel + ChiMai + KTM",
         "What we learned": "All 6 parameters hit bound constraints; structural mis-specification",
         "What changed": "Pivot to ConvCNP residual learner (CREST); §4 negative-result case study",
         "Justification": "Soft inductive bias > rigid functional form for cross-city transfer"},
        {"#": "P4",
         "Original commitment": "N=5 source cities (Mel + ChiMai + KTM + Bogotá + Mex City)",
         "What we tried": "Bogotá + Mex City data ingest and per-station calibration",
         "What we learned": "Different atmospheric regime (plateau/coastal); CREST collapsed",
         "What changed": "N=3 source-city LOOCV (Mel + ChiMai + KTM)",
         "Justification": "Regime similarity is dominant transfer condition (KTM-as-finding)"},
        {"#": "P5",
         "Original commitment": "Nuwara Eliya + Badulla zero-shot targets in main scope",
         "What we tried": "Plan deferred — no ground truth at either city",
         "What we learned": "Three-target validation impossible without surface monitoring",
         "What changed": "Kandy-only main scope; NE/Badulla → future work",
         "Justification": "Falsifiable prediction locked: NE should ≥ Kandy on regime grounds"},
        {"#": "P6",
         "Original commitment": "Sim2Real Phase 1 + Phase 2 (synthetic pretrain → fine-tune)",
         "What we tried": "Held as planned branch; gate = mean LOOCV r ≥ 0.50",
         "What we learned": "v10 mean r = 0.424; v11 = 0.426 (gate not triggered)",
         "What changed": "Branch closed; rebranded 'supervised cross-city ConvCNP'",
         "Justification": "Honesty about title-method consistency"},
        {"#": "P7",
         "Original commitment": "Single-shot evaluation against Bowatte/KOALA",
         "What we tried": "Outreach drafts to Bowatte + Lokupitiya (2026-05-20)",
         "What we learned": "Independent data access unresolved; CEA + NBRO withhold publicly",
         "What changed": "Added 22-year extrapolation + Van Donkelaar cross-product triangulation",
         "Justification": "Independent third-product validation despite no field campaign"},
        {"#": "P8",
         "Original commitment": "Single-station calibration with point-mean ratio",
         "What we tried": "Stage 3 v10 used timestamp-mean c_prior ratio",
         "What we learned": "KTM ratio drifted 12 % (0.629 → 0.560 row-mean)",
         "What changed": "v11 row-mean fix; bias reduced ~1.5 µg m⁻³ (less than predicted ~5)",
         "Justification": "Real bug but residual bias is structural regime mismatch"},
    ]
    _save(pd.DataFrame(rows), "T10_pivots_summary")


TABLES = {"T1": tbl_T1, "T2": tbl_T2, "T3": tbl_T3, "T4": tbl_T4,
          "T5": tbl_T5, "T6": tbl_T6, "T7": tbl_T7, "T8": tbl_T8,
          "T9": tbl_T9, "T10": tbl_T10}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--table", nargs="+", choices=list(TABLES))
    p.add_argument("--all", action="store_true")
    args = p.parse_args()
    targets = list(TABLES) if args.all else (args.table or [])
    if not targets:
        p.print_help(); return
    for tid in targets:
        print(f"--- {tid} ---")
        try:
            TABLES[tid]()
        except Exception as e:
            print(f"ERROR in {tid}: {e}")
            import traceback; traceback.print_exc()
    print(f"\nAll tables saved to {OUT}")


if __name__ == "__main__":
    main()
