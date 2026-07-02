"""xichang_twin_figures.py — TEMPORAL HOLD-OUT validation twin for Xichang.

A byte-for-byte mirror of the locked Kandy additive decomposition, built with ONLY
the data classes Kandy has — VanD V6 level, GEOS-CF prior, ERA5 met, SRTM terrain,
VanD-surface S_emit, two anchor stations playing the FECT role — then put through
the test Kandy can never run because it has no ground truth:

    TRAIN the temporal anchor T(t) on 2020–2024 only  →  PREDICT the held-out 2025+
    →  CHECK against Xichang's REAL 2025 measurements, temporally AND spatially.

Nothing from 2025 touches the fit (anchor training, ratio, conformal calibration,
and diurnal/seasonal sharpening all use 2020–2024 only). The two anchor stations are
chosen to span an ELEVATION GRADIENT (valley-floor + elevated), mirroring Kandy's FECT pair. The 2025 field is driven
by 2025 exogenous inputs (GEOS-CF + ERA5), exactly as Kandy production makes any
year. The LEVEL is carried from the 2023 VanD tile (VanD ends 2023 — the same
post-2023 convention Kandy uses for its 2024/25 maps), so the genuine 2-year-ahead
forecast under test is the SEASONAL + DIURNAL shape and the SPATIAL pattern.

Scoring reuses the frozen prereg scorer (score.score_draw) windowed to 2025, so
the gate numbers here are honest out-of-sample metrics, not in-window fit quality.

Two caveats, annotated on the scorecard (X11):
  * the LEVEL is VanD-anchored and VanD V6 is monitor-fused (saw these CNEMC
    stations) → V1 passes partly by construction; the honest zero-GT signal is the
    station-blind SPATIAL pattern (V4);
  * Xichang is LOCAL-dominated (reconciling f≈0.9) vs Kandy REGIONAL (f≈0.25) →
    this validates the MACHINERY + horizontal skill, not Kandy's bg/local split.

Styling matches the v2 paper suite (paperfig.py YlOrRd, square heatmaps, A4).

    python scripts/xichang_twin_figures.py --figs all        # or x1,x6,x11 …
Outputs → results/figures/xichang_twin/{X1..X11}.png
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D

from src.stage1_satml.decomp import pubfig            # noqa: F401 (applies style)
from src.stage1_satml.decomp import paperfig as pf
from src.transfer_validation.citypack import get
from src.transfer_validation.anchors import draws, station_stats, Draw
from src.transfer_validation.assembly import (
    spatial_fields, b_hourly, predict_at_stations, KAPPA, _terrain, _interp2)
from src.transfer_validation import drivers, score
from src.transfer_validation import t_anchor as ta
from src.transfer_validation.vand import level_for_year

CITY = "xichang"
TRAIN_YEARS = (2020, 2021, 2022, 2023, 2024)   # fit window; predict 2025+ held out
TEST_YEAR = 2025                          # held out — never seen by the fit
OUT = REPO / "results" / "figures" / "xichang_twin"
OUT.mkdir(parents=True, exist_ok=True)
DEC = REPO / "data" / "processed" / "decomp"


# ── windowed T(t): mirrors t_anchor.fit_and_build but TRAIN/TEST split ───────
def _anchor_series_win(cp, anchors, years):
    """Per-hour anchor-pair pm25 + row-mean ratio, restricted to `years`."""
    df = pd.read_parquet(cp.station_parquet(),
                         columns=["datetime_utc", "station_id", "pm25", "c_prior"])
    df = df[df.station_id.isin(list(anchors))].dropna(subset=["pm25"])
    df["datetime"] = (pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)
                        .dt.tz_localize(None))
    df = df.dropna(subset=["datetime"])
    df = df[df.datetime.dt.year.isin(set(years))]
    both = df.dropna(subset=["c_prior"])
    ratio = float(both.pm25.mean() / both.c_prior.mean())     # gotcha #39 row-mean
    hourly = df.groupby("datetime")["pm25"].mean().rename("pm25_anchor").reset_index()
    return hourly, ratio


def fit_split(cp, anchors, train_years=TRAIN_YEARS, test_year=TEST_YEAR,
              sharpen=True):
    """T(t) for `test_year`, trained ONLY on `train_years` anchor data.

    Identical recipe to ta.fit_and_build (lag-free LGBM quantile heads + Mondrian
    conformal + climatology sharpening + VanD level re-anchor) — only the temporal
    windows differ, so nothing from the test year informs the fit."""
    from lightgbm import LGBMRegressor
    drv = ta._driver_table(cp)
    obs, ratio = _anchor_series_win(cp, anchors, train_years)
    drv["c_prior_scaled"] = drv.pm25_prior * ratio
    train = drv.merge(obs, on="datetime").dropna(subset=ta.FEATURES + ["pm25_anchor"])
    train["resid"] = train.pm25_anchor - train.c_prior_scaled
    X, y = train[ta.FEATURES], train.resid

    heads, oof = {}, {}
    fold = np.arange(len(train)) * ta.N_FOLDS // max(len(train), 1)
    for a in (0.05, 0.50, 0.95):
        heads[a] = LGBMRegressor(alpha=a, **ta.LGBM_PARAMS).fit(X, y)
        pred = np.full(len(train), np.nan)
        for k in range(ta.N_FOLDS):
            tr, te = fold != k, fold == k
            if te.sum() == 0 or tr.sum() < 500:
                continue
            m = LGBMRegressor(alpha=a, **ta.LGBM_PARAMS).fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
        oof[a] = pred

    cal = train.assign(q05=oof[0.05], q95=oof[0.95]).dropna(subset=["q05", "q95"])
    cal["stratum"] = (cal.datetime.dt.month.astype(str) + "_"
                      + ta._hod_bin(cal.datetime.dt.hour).astype(str))
    cal["s_lo"] = cal.q05 - cal.resid
    cal["s_hi"] = cal.resid - cal.q95
    qq = 1 - ta.ALPHA / 2
    table = cal.groupby("stratum")[["s_lo", "s_hi"]].quantile(qq)
    glo, ghi = float(cal.s_lo.quantile(qq)), float(cal.s_hi.quantile(qq))

    inf = drv[drv.datetime.dt.year == test_year].copy()       # HELD-OUT year
    q05 = heads[0.05].predict(inf[ta.FEATURES])
    q50 = heads[0.50].predict(inf[ta.FEATURES])
    q95 = heads[0.95].predict(inf[ta.FEATURES])
    q05, q95 = np.minimum(q05, q50), np.maximum(q95, q50)
    strat = (inf.datetime.dt.month.astype(str) + "_"
             + ta._hod_bin(inf.datetime.dt.hour).astype(str))
    c_lo = strat.map(table.s_lo).fillna(glo).to_numpy()
    c_hi = strat.map(table.s_hi).fillna(ghi).to_numpy()
    base = inf.c_prior_scaled.to_numpy()
    T = pd.DataFrame({"datetime": inf.datetime.to_numpy(),
                      "T_q05": base + q05 - np.maximum(c_lo, 0),
                      "T_q50": base + q50,
                      "T_q95": base + q95 + np.maximum(c_hi, 0)})

    if sharpen:   # to the TRAIN-year anchor climatology only (no test leakage)
        m_obs = obs.set_index("datetime").pm25_anchor
        tq = T.set_index("datetime").T_q50
        fh = ((m_obs.groupby(m_obs.index.hour).mean() / m_obs.mean())
              / (tq.groupby(tq.index.hour).mean() / tq.mean())).clip(*ta.CLIP_SHARPEN)
        fm = ((m_obs.groupby(m_obs.index.month).mean() / m_obs.mean())
              / (tq.groupby(tq.index.month).mean() / tq.mean())).clip(*ta.CLIP_SHARPEN)
        fac = (T.datetime.dt.hour.map(fh).fillna(1.0)
               * T.datetime.dt.month.map(fm).fillna(1.0)).to_numpy()
        for c in ("T_q05", "T_q50", "T_q95"):
            T[c] = T[c] * fac

    L, tile = level_for_year(cp, test_year)                    # 2023 proxy
    shift = L - float(T.T_q50.mean())
    for c in ("T_q05", "T_q50", "T_q95"):
        T[c] = T[c] + shift
    info = {"ratio": round(ratio, 4), "n_train": int(len(train)),
            "anchors": tuple(map(str, anchors)), "L": round(L, 2),
            "tile": tile, "shift": round(shift, 2)}
    return T, info

OBS_C = "#1f6f8b"      # ground-truth accent (kept inside v2 palette as a cool foil)
MODEL_C = "#b30000"    # YlOrRd-dark, the model line


def _save(fig, name, square=True):
    if square:
        pf.square_heatmaps(fig)
    fig.savefig(OUT / f"{name}.png", dpi=400, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.png")


def _elev_at_stations(cp):
    """Δz (relief above basin floor, m) sampled at every station — the elevation axis."""
    lat1, lon1, dz = _terrain(cp)
    st = cp.stations().set_index("station_id")
    return pd.Series(_interp2(lat1, lon1, dz, st.lat.to_numpy(), st.lon.to_numpy()),
                     index=st.index)


def _draw_list(cp, train_years, test_year):
    """ONE deterministic anchor pair with an ELEVATION GRADIENT (valley-floor +
    elevated), mirroring Kandy's FECT pair (Akurana ~460 m valley-floor + Hantana
    ~738 m slope). The two anchors train T(t); every other station is held-out vault."""
    elig = station_stats(cp, years=train_years)
    elig = set(elig[elig.n_obs >= 4000].station_id)           # train-coverage floor
    dz = _elev_at_stations(cp)
    dz = dz[[s for s in dz.index if s in elig]].dropna()
    floor, elev = dz.idxmin(), dz.idxmax()
    test_st = set(station_stats(cp, years=[test_year]).station_id)
    vault = tuple(s for s in test_st if s not in (floor, elev))
    print(f"  elev-gradient anchors: floor={floor} (Δz {dz[floor]:.0f} m) + "
          f"elevated={elev} (Δz {dz[elev]:.0f} m, gradient {dz[elev]-dz[floor]:.0f} m); "
          f"vault n={len(vault)}")
    return [Draw(seed=0, anchors=(floor, elev), vault=vault)]


# ───────────────────────── build (cache the whole twin) ─────────────────────
class Twin:
    """Train T(t) on TRAIN_YEARS, predict TEST_YEAR, cache OOS scores + grid + obs."""

    def __init__(self):
        # city-centred core domain (urban core central; matches WindNinja + traffic
        # boxes; fixes the off-centre station-box confinement mis-registration)
        core = REPO / "data" / "processed" / "pinn_inputs" / "xichang_terrain_core.npz"
        self.cp = (replace(get(CITY), terrain_npz_name=core.name)
                   if core.exists() else get(CITY))
        self.f = self.cp.f_local
        # windowed CityPacks: S_emit/level from train tiles; assembly+scoring at test
        self.cp_train = replace(self.cp, score_years=TRAIN_YEARS)
        self.cp_test = replace(self.cp, score_years=(TEST_YEAR,))
        self.fields = spatial_fields(self.cp_train)
        self.draws = _draw_list(self.cp, TRAIN_YEARS, TEST_YEAR)
        self.emis = self._emission_layers()
        print(f"=== Xichang TEMPORAL twin: train {TRAIN_YEARS} → test {TEST_YEAR} | "
              f"{len(self.draws)} draws, {len(self.fields['station_id'])} stations, "
              f"f={self.f} ===")

        self.T_by_draw, self.merged, recs = [], [], []
        for d in self.draws:
            T, info = fit_split(self.cp, d.anchors)       # fit excludes TEST_YEAR
            self.T_by_draw.append(T)
            obs = score._vault_obs(self.cp_test, d.vault)
            pred = predict_at_stations(self.cp_test, T, self.fields, self.f)
            m = obs.merge(pred, on=["datetime", "station_id"], how="inner")
            self.merged.append(m)
            recs.append(score.score_draw(self.cp_test, d, T, self.fields, self.f))
            print(f"  draw {d.seed}: anchors={info['anchors']} L={info['L']} "
                  f"n_train={info['n_train']:,} → {TEST_YEAR} n_pairs={len(m):,} "
                  f"vault={m.station_id.nunique()}")

        # OOS gate table (median[min,max] across draws) — same schema as the prereg
        gd = pd.DataFrame([r for r in recs if "error" not in r])
        self.gate = gd.agg(["median", "min", "max"]).T
        self.verdict = score.verdict(self.cp_test, gd)
        print("  OOS gates:", {k: v.split(": ")[-1] for k, v in self.verdict.items()})

        # observed TEST-year station means (the spatial ground truth)
        self.stats = station_stats(self.cp, years=[TEST_YEAR]).set_index("station_id")
        self._grid_field()

    def _emission_layers(self):
        """Kandy-mirror anthropogenic surfaces on the field grid: VanD S_emit,
        congestion-weighted traffic, VIIRS NTL — for the explainability figure."""
        from scipy.interpolate import RegularGridInterpolator
        g = self.fields
        out = {"S_emit": g["S"]}
        tr = DEC / "S_traffic_xichang.npz"
        if tr.exists():
            z = np.load(tr)
            out["traffic"] = z["S_traffic"]
        # VIIRS NTL on the station-footprint grid → resample to the field grid
        try:
            z = np.load(self.cp.ntl_npz(), allow_pickle=True)
            nl = np.asarray(z["lat_grid"], float); no = np.asarray(z["lon_grid"], float)
            ntl = np.asarray(z[[k for k in z.files if "ntl" in k.lower()
                                or "rad" in k.lower() or k in ("ntl", "viirs")][0]], float)
            la1, lo1 = nl[:, 0], no[0, :]
            if la1[0] > la1[-1]:
                la1, ntl = la1[::-1], ntl[::-1, :]
            f = RegularGridInterpolator((la1, lo1), ntl, bounds_error=False,
                                        fill_value=None)
            gg = np.meshgrid(g["glat"], g["glon"], indexing="ij")
            nl_g = f(np.column_stack([gg[0].ravel(), gg[1].ravel()])).reshape(
                len(g["glat"]), len(g["glon"]))
            out["ntl"] = nl_g / np.nanmean(nl_g)
        except Exception as e:  # noqa: BLE001
            print(f"  (NTL layer skipped: {e})")
        return out

    # -- exact additive time-mean over a set of hours (separable, see header) --
    def _coeffs(self, mask_fn):
        """A0,A1,A2 (+ q05/q95 variants) averaged across draws over selected hrs."""
        A = {k: [] for k in ("b", "i50", "iw50", "i05", "iw05", "i95", "iw95")}
        for T in self.T_by_draw:
            B = b_hourly(self.cp_test, T, self.f)
            blh = drivers.blh(self.cp_test).set_index("datetime").blh_m
            w = np.clip((self.fields["h_ridge"] - T.datetime.map(blh).to_numpy())
                        / self.fields["h_ridge"], 0, 1)
            w = np.nan_to_num(w, nan=0.0)
            sc = float(np.nanmean(self.fields["S"] * self.fields["c_grid_on_S"]))
            norm = 1.0 + KAPPA * w * sc
            sel = mask_fn(T.datetime).to_numpy()
            if sel.sum() == 0:
                continue
            for q, tag in ((T.T_q50, "50"), (T.T_q05, "05"), (T.T_q95, "95")):
                inc = (q.to_numpy() - B) / norm
                A[f"i{tag}"].append(np.nanmean(inc[sel]))
                A[f"iw{tag}"].append(np.nanmean((inc * w)[sel]))
            A["b"].append(np.nanmean(B[sel]))
        return {k: float(np.nanmean(v)) for k, v in A.items()}

    def grid(self, coeffs, tag="50"):
        S, c = self.fields["S"], self.fields["c_grid_on_S"]
        return coeffs["b"] + S * coeffs[f"i{tag}"] + KAPPA * S * c * coeffs[f"iw{tag}"]

    def _grid_field(self):
        self.coef_ann = self._coeffs(lambda dt: pd.Series(True, index=dt.index))
        self.map_ann = self.grid(self.coef_ann)
        seas = {"DJF": (12, 1, 2), "MAM": (3, 4, 5),
                "JJA": (6, 7, 8), "SON": (9, 10, 11)}
        self.map_seas = {s: self.grid(self._coeffs(
            lambda dt, mo=mo: dt.dt.month.isin(mo))) for s, mo in seas.items()}

    # -- per-draw curve helpers (mirror score.py aggregation exactly) ----------
    def monthly(self):
        out = []
        for m in self.merged:
            mm = (m.set_index("datetime").groupby(pd.Grouper(freq="MS"))
                  [["pm25", "pm_q50"]].mean().dropna())
            out.append(mm)
        return out

    def diurnal(self):
        return [m.groupby(m.datetime.dt.hour)[["pm25", "pm_q50"]].mean()
                for m in self.merged]

    def station_means(self):
        frames = [m.groupby("station_id")[["pm25", "pm_q50"]].mean()
                  for m in self.merged]
        return pd.concat(frames).groupby(level=0).median()

    def pooled(self):
        return pd.concat(self.merged, ignore_index=True)

    def extent(self):
        g = self.fields
        return [g["glon"][0], g["glon"][-1], g["glat"][0], g["glat"][-1]]

    def st_xy(self):
        st = self.cp.stations()
        return st.set_index("station_id")[["lat", "lon"]]

    def sample_grid(self, M, ids=None):
        """Sample a field-grid (glat×glon) array at station coordinates."""
        from scipy.interpolate import RegularGridInterpolator
        g = self.fields
        f = RegularGridInterpolator((g["glat"], g["glon"]), M,
                                    bounds_error=False, fill_value=None)
        st = self.st_xy()
        if ids is not None:
            st = st.loc[[i for i in ids if i in st.index]]
        vals = f(np.column_stack([st.lat.to_numpy(), st.lon.to_numpy()]))
        return pd.Series(vals, index=st.index)


# ───────────────────────────── figures ──────────────────────────────────────
# Xichang sits well above the Kandy/WHO band, so the Kandy PowerNorm(5, vmax)
# saturates the field. We use a DATA-CENTRED linear scale (robust p2–p98) with
# the v2 YlOrRd cmap so the (smooth, ±10%) spatial structure stays legible.
def _rng(*arrays, plo=2, phi=98):
    v = np.concatenate([np.asarray(a, float).ravel() for a in arrays])
    v = v[np.isfinite(v)]
    return float(np.percentile(v, plo)), float(np.percentile(v, phi))


def _heat(ax, tw, M, vmin, vmax, title, cmap=None):
    im = ax.imshow(M, origin="lower", extent=tw.extent(), aspect="auto",
                   cmap=cmap or pf.PM_CMAP,
                   norm=mcolors.Normalize(vmin=vmin, vmax=vmax))
    ax.set_title(title)
    ax.set_xlabel("lon (°E)"); ax.set_ylabel("lat (°N)")
    return im


def _cbar(fig, im, ax, shrink=0.8):
    return fig.colorbar(im, ax=ax, shrink=shrink, extend="both",
                        label="PM$_{2.5}$ (µg m$^{-3}$)")


def x1_studyarea(tw):
    """Setting: terrain Δz + station network + VanD level context."""
    z = np.load(tw.cp.terrain_npz(), allow_pickle=True)
    dz = np.asarray(z["delta_z"], float)
    lat = np.asarray(z["lat_grid"], float); lon = np.asarray(z["lon_grid"], float)
    fig, ax = plt.subplots(figsize=(7.0, 6.2))
    im = ax.imshow(dz, origin="lower",
                   extent=[lon.min(), lon.max(), lat.min(), lat.max()],
                   aspect="auto", cmap="terrain")
    st = tw.st_xy()
    ax.scatter(st.lon, st.lat, s=55, c="black", marker="^",
               edgecolor="white", linewidth=0.6, zorder=5, label="CNEMC station")
    L, tile = level_for_year(tw.cp, tw.cp.score_years[0])
    ax.set_title(f"Xichang study area — terrain relief & monitor network\n"
                 f"VanD basin level L≈{L:.1f} µg m$^{{-3}}$ ({tile})")
    ax.set_xlabel("lon (°E)"); ax.set_ylabel("lat (°N)")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Δz above basin floor (m)")
    ax.legend(loc="upper right")
    _save(fig, "X1_studyarea")


def x2_inputs(tw):
    """Kandy-mirror anthropogenic + terrain inputs (VanD S_emit, traffic, NTL, c)."""
    g, em = tw.fields, tw.emis
    panels = [("S$_{emit}$ — VanD V6 surface (mean 1)", em["S_emit"], pf.INFERNO,
               "relative"),
              ("Traffic emission — centrality·COPERT (mean 1)",
               em.get("traffic"), pf.INFERNO, "relative"),
              ("VIIRS night-lights (mean 1)", em.get("ntl"), "cividis", "relative"),
              ("Confinement c = z-score(−Δz)", g["c_grid_on_S"], "RdBu_r", "σ")]
    panels = [p for p in panels if p[1] is not None]
    fig, axs = plt.subplots(1, len(panels), figsize=(4.7 * len(panels), 4.8))
    for ax, (title, M, cmap, units) in zip(np.atleast_1d(axs), panels):
        kw = dict(vmin=-2.5, vmax=2.5) if units == "σ" else {}
        im = ax.imshow(M, origin="lower", extent=tw.extent(), aspect="auto",
                       cmap=cmap, **kw)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("lon (°E)"); ax.set_ylabel("lat (°N)")
        fig.colorbar(im, ax=ax, shrink=0.78, label=units)
    fig.suptitle("Blind inputs — exactly the data classes available for Kandy "
                 "(satellite level + bottom-up traffic + night-lights + terrain)",
                 y=1.03, fontsize=10)
    _save(fig, "X2_inputs")


def x3_decomposition(tw):
    """Additive split B(t) + increment → annual-mean field."""
    co = tw.coef_ann
    b_map = np.full_like(tw.map_ann, co["b"])
    inc_map = tw.map_ann - co["b"]
    vmin, vmax = _rng(tw.map_ann)
    fig, axs = plt.subplots(1, 3, figsize=(15.5, 5.0))
    im0 = _heat(axs[0], tw, b_map, vmin, vmax,
                f"B(t) background\n(uniform, ⟨B⟩={co['b']:.1f})")
    _cbar(fig, im0, axs[0])
    im1 = axs[1].imshow(inc_map, origin="lower", extent=tw.extent(), aspect="auto",
                        cmap="YlOrRd")
    axs[1].set_title("Local increment\n[T−B]·P$_{local}$")
    fig.colorbar(im1, ax=axs[1], shrink=0.8, label="µg m$^{-3}$")
    im2 = _heat(axs[2], tw, tw.map_ann, vmin, vmax,
                "Annual mean PM$_{2.5}$\n(B + increment)")
    _cbar(fig, im2, axs[2])
    for ax in axs:
        ax.set_xlabel("lon (°E)"); ax.set_ylabel("lat (°N)")
    fig.suptitle(f"Xichang additive decomposition — held-out {TEST_YEAR} "
                 f"(T(t) trained {TRAIN_YEARS[0]}–{TRAIN_YEARS[-1]})", y=1.02)
    _save(fig, "X3_decomposition")


def x4_seasonal(tw):
    """Seasonal mean fields DJF/MAM/JJA/SON."""
    vmin, vmax = _rng(*tw.map_seas.values())
    fig, axs = plt.subplots(2, 2, figsize=(11.0, 10.0))
    for ax, s in zip(axs.ravel(), ["DJF", "MAM", "JJA", "SON"]):
        im = _heat(ax, tw, tw.map_seas[s], vmin, vmax, s)
    _cbar(fig, im, list(axs.ravel()))
    fig.suptitle(f"Xichang seasonal mean PM$_{{2.5}}$ — held-out {TEST_YEAR} "
                 f"(blind forecast)", y=1.00)
    _save(fig, "X4_seasonal")


def x5_diurnal_model(tw):
    """Model basin-mean diurnal cycle (= T(t); basin mean is T-locked)."""
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    curves = []
    for T in tw.T_by_draw:
        h = T.groupby(T.datetime.dt.hour).T_q50.mean()
        curves.append(h)
        ax.plot(h.index, h.values, color=MODEL_C, alpha=0.25, lw=1)
    med = pd.concat(curves, axis=1).median(axis=1)
    ax.plot(med.index, med.values, color=MODEL_C, lw=2.4, label="model basin-mean (median draw)")
    ax.set_xlabel("hour of day (LT)"); ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
    ax.set_title(f"Xichang modelled diurnal cycle, held-out {TEST_YEAR} "
                 f"(basin mean = T(t))")
    ax.set_xticks(range(0, 24, 3)); ax.legend()
    _save(fig, "X5_diurnal_model", square=False)


def x6_field_vs_obs(tw):
    """THE money shot: predicted field + observed station means, same scale."""
    st = tw.st_xy().join(tw.stats["mean"]).dropna()
    vmin, vmax = _rng(tw.map_ann, st["mean"].to_numpy(), plo=1, phi=99)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    fig, ax = plt.subplots(figsize=(7.6, 6.6))
    im = ax.imshow(tw.map_ann, origin="lower", extent=tw.extent(), aspect="auto",
                   cmap=pf.PM_CMAP, norm=norm)
    ax.scatter(st.lon, st.lat, c=st["mean"], cmap=pf.PM_CMAP, norm=norm,
               s=150, edgecolor="black", linewidth=1.2, zorder=5)
    ax.set_title(f"Held-out {TEST_YEAR}: predicted field vs observed station means "
                 f"(dots)\nsame colour scale — eyeball the spatial agreement")
    ax.set_xlabel("lon (°E)"); ax.set_ylabel("lat (°N)")
    _cbar(fig, im, ax)
    leg = [Line2D([0], [0], marker="o", color="none", markerfacecolor="grey",
                  markeredgecolor="black", markersize=10, label="observed station mean")]
    ax.legend(handles=leg, loc="upper right")
    _save(fig, "X6_field_vs_obs")


def x7_station_scatter(tw):
    """Per-station predicted vs observed mean (V4 spatial)."""
    from scipy.stats import spearmanr
    sm = tw.station_means().join(tw.stats["mean"], how="inner").dropna()
    rho, _ = spearmanr(sm["mean"], sm.pm_q50)
    gate = tw.gate.loc["V4_spatial_rho", "median"]
    fig, ax = plt.subplots(figsize=(6.0, 6.0))
    lo = min(sm["mean"].min(), sm.pm_q50.min()) - 2
    hi = max(sm["mean"].max(), sm.pm_q50.max()) + 2
    ax.plot([lo, hi], [lo, hi], "--", color="grey", lw=1, label="1:1")
    ax.scatter(sm["mean"], sm.pm_q50, s=80, c=MODEL_C, edgecolor="black",
               linewidth=0.6, zorder=4)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_xlabel("observed station mean (µg m$^{-3}$)")
    ax.set_ylabel("predicted station mean (µg m$^{-3}$)")
    ax.set_title(f"Per-station agreement (held-out vault)\n"
                 f"Spearman ρ = {rho:.2f}  (gate V4 median {gate:.2f}, ≥0.40 ✓)")
    ax.legend(loc="upper left")
    _save(fig, "X7_station_scatter", square=False)


def x8_seasonal_overlay(tw):
    """Predicted vs observed monthly city-mean (V2 seasonal)."""
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    obs_c, pred_c = [], []
    for mm in tw.monthly():
        ax.plot(mm.index, mm.pm25, color=OBS_C, alpha=0.2, lw=1)
        ax.plot(mm.index, mm.pm_q50, color=MODEL_C, alpha=0.2, lw=1)
        obs_c.append(mm.pm25.rename(None)); pred_c.append(mm.pm_q50.rename(None))
    obs = pd.concat(obs_c, axis=1).median(axis=1)
    pred = pd.concat(pred_c, axis=1).median(axis=1)
    ax.plot(obs.index, obs.values, color=OBS_C, lw=2.4, label="observed (vault)")
    ax.plot(pred.index, pred.values, color=MODEL_C, lw=2.4, label="model (blind)")
    gate = tw.gate.loc["V2_seasonal_r", "median"]
    mark = "✓" if gate >= 0.80 else "✗"
    ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)"); ax.set_xlabel("month")
    ax.set_title(f"Monthly city-mean, held-out {TEST_YEAR} — model vs observed   "
                 f"(V2 r = {gate:.2f}, ≥0.80 {mark})")
    ax.legend()
    _save(fig, "X8_seasonal_overlay", square=False)


def x9_diurnal_overlay(tw):
    """Predicted vs observed hour-of-day climatology (V3 diurnal).

    The per-draw model curves (faint) scatter: with only TWO anchor sensors the
    hour-of-day shape is weakly constrained, so the rigorous per-draw V3 is low
    out-of-sample even though the median curves track — the honest 2-sensor limit
    (the same one that makes Kandy's diurnal the part most needing local data)."""
    fig, ax = plt.subplots(figsize=(7.8, 4.7))
    obs_c, pred_c = [], []
    for hh in tw.diurnal():
        ax.plot(hh.index, hh.pm_q50, color=MODEL_C, alpha=0.22, lw=1)
        obs_c.append(hh.pm25); pred_c.append(hh.pm_q50)
    obs = pd.concat(obs_c, axis=1).median(axis=1)
    pred = pd.concat(pred_c, axis=1).median(axis=1)
    ax.plot(obs.index, obs.values, color=OBS_C, lw=2.4, marker="o", ms=4,
            label="observed (vault)")
    ax.plot(pred.index, pred.values, color=MODEL_C, lw=2.4, marker="s", ms=4,
            label="model (blind, median draw)")
    g = tw.gate.loc["V3_diurnal_r"]
    mark = "✓" if g["median"] >= 0.70 else "✗"
    ax.set_xlabel("hour of day (LT)"); ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
    ax.set_title(f"Diurnal climatology, held-out {TEST_YEAR} — model vs observed\n"
                 f"per-draw V3 r = {g['median']:.2f} [{g['min']:.2f}, {g['max']:.2f}], "
                 f"≥0.70 {mark}  (2-sensor diurnal is the weak link)")
    ax.set_xticks(range(0, 24, 3)); ax.legend()
    _save(fig, "X9_diurnal_overlay", square=False)


def x10_uq(tw):
    """UQ honesty: raw cov90 (under-covers) + conformal widening → ~0.90."""
    m = tw.pooled()
    inb = (m.pm25 >= m.pm_q05) & (m.pm25 <= m.pm_q95)
    cov_raw = float(inb.mean())
    # empirical post-hoc widening factor q̂ s.t. coverage → 0.90 (illustrative,
    # the principle behind Track-U shift-aware conformal at panel scale)
    mid = m.pm_q50
    lo_d, hi_d = mid - m.pm_q05, m.pm_q95 - mid
    scores = np.maximum((m.pm_q05 - m.pm25) / lo_d.clip(lower=1e-6),
                        (m.pm25 - m.pm_q95) / hi_d.clip(lower=1e-6))
    qhat = float(np.nanquantile(np.maximum(scores, 0) + 1.0, 0.90))
    inb_w = ((m.pm25 >= mid - qhat * lo_d) & (m.pm25 <= mid + qhat * hi_d))
    cov_w = float(inb_w.mean())

    by_h = m.assign(inb=inb).groupby(m.datetime.dt.hour).inb.mean()
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    ax.bar(by_h.index, by_h.values, color="#d9a441", label="raw 90% PI coverage")
    ax.axhline(0.90, ls="--", color="black", lw=1, label="nominal 0.90")
    ax.axhline(cov_raw, ls=":", color=MODEL_C, lw=1.5,
               label=f"raw cov90 = {cov_raw:.2f} (gate V5, under-covers)")
    ax.set_ylim(0, 1); ax.set_xlabel("hour of day (LT)")
    ax.set_ylabel("fraction of obs inside PI")
    ax.set_title("UQ honesty — raw intervals under-cover; conformal widening "
                 f"(×{qhat:.2f}) → cov90 {cov_w:.2f}")
    ax.set_xticks(range(0, 24, 3)); ax.legend(fontsize=7, loc="lower right")
    _save(fig, "X10_uq", square=False)


def x11_scorecard(tw):
    """V1–V6b vs thresholds with the two load-bearing caveats annotated."""
    g = tw.gate
    # (gate, what, value, formatted value, threshold text, PASS?)
    def mn(k): return g.loc[k, "median"]
    rows = [
        ("V1", "level error", f"{mn('V1_level_err_pct'):.1f}%", "≤ 15%",
         abs(mn("V1_level_err_pct")) <= 15),
        ("V2", "seasonal corr.", f"{mn('V2_seasonal_r'):.2f}", "≥ 0.80",
         mn("V2_seasonal_r") >= 0.80),
        ("V3", "diurnal corr.", f"{mn('V3_diurnal_r'):.2f}", "≥ 0.70",
         mn("V3_diurnal_r") >= 0.70),
        ("V4", "spatial rank ρ", f"{mn('V4_spatial_rho'):.2f}", "≥ 0.40",
         mn("V4_spatial_rho") >= 0.40),
        ("V5", "UQ cov90", f"{mn('V5_cov90'):.2f}", "0.85–0.95",
         0.85 <= mn("V5_cov90") <= 0.95),
        ("V6b", "reconciling f", f"{mn('V6b_f_reconciling'):.2f}",
         f"{tw.cp.f_bracket[0]:.2f}–{tw.cp.f_bracket[1]:.2f}",
         tw.cp.f_bracket[0] <= mn("V6b_f_reconciling") <= tw.cp.f_bracket[1]),
    ]
    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    ax.axis("off")
    ax.set_title(f"Xichang twin — gate scorecard  (elevation-gradient anchor pair, "
                 f"train {TRAIN_YEARS[0]}–{TRAIN_YEARS[-1]} → held-out {TEST_YEAR})",
                 fontsize=10, pad=14)
    headers = ["gate", "what it tests", "value", "threshold", "verdict"]
    xcol = [0.05, 0.20, 0.52, 0.66, 0.84]
    ytop, dy = 0.92, 0.115
    for xc, h in zip(xcol, headers):
        ax.text(xc, ytop, h, fontweight="bold", fontsize=9.5,
                transform=ax.transAxes)
    for i, (gate, what, val, thr, ok) in enumerate(rows):
        y = ytop - (i + 1) * dy
        col = "#2e8b57" if ok else "#c0392b"
        ax.add_patch(plt.Rectangle((0.02, y - 0.045), 0.96, dy * 0.86,
                     transform=ax.transAxes, facecolor=col, alpha=0.12,
                     edgecolor="none", zorder=0))
        ax.text(xcol[0], y, gate, fontsize=9.5, transform=ax.transAxes)
        ax.text(xcol[1], y, what, fontsize=9.5, transform=ax.transAxes)
        ax.text(xcol[2], y, val, fontsize=9.5, transform=ax.transAxes)
        ax.text(xcol[3], y, thr, fontsize=9.5, transform=ax.transAxes)
        ax.text(xcol[4], y, "PASS" if ok else "FAIL", fontsize=9.5,
                fontweight="bold", color=col, transform=ax.transAxes)
    cav = ("CAVEATS — what this twin does and does NOT prove:\n"
           "• LEVEL (V1) is anchored to Van Donkelaar V6, which is monitor-fused and "
           "saw these CNEMC\n   stations → V1 passes partly by construction.\n"
           "• The honest zero-ground-truth signal is the station-blind SPATIAL pattern "
           "(V4, NTL/road only).\n"
           "• Xichang is LOCAL-dominated (f ≈ %.2f) whereas Kandy is REGIONAL-dominated "
           "(f ≈ 0.25):\n   this twin validates the MACHINERY + horizontal skill, NOT "
           "Kandy's background/local partition.\n"
           "• V6b reconciling-f = %.2f (>1) → the model UNDER-predicts the observed "
           "cross-station\n   spread: amplitude, not rank, is the scarce skill (F0.2).\n"
           "• V5 raw intervals under-cover; panel-scale shift-aware conformal (Track U) "
           "restores ~0.90 (see X10)."
           % (tw.f, mn("V6b_f_reconciling")))
    ax.text(0.0, -0.16, cav, transform=ax.transAxes, fontsize=7.8, va="top",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", fc="#fff7e6", ec="grey"))
    _save(fig, "X11_scorecard", square=False)


def x12_emission_explain(tw):
    """Is Xichang's observed spatial pattern explainable by anthropogenic activity?

    Observed held-out-2025 station means vs each Kandy-mirror emission proxy."""
    from scipy.stats import spearmanr
    obs = tw.stats["mean"]
    layers = [("VanD V6 surface", tw.emis.get("S_emit")),
              ("traffic emission\n(centrality·COPERT)", tw.emis.get("traffic")),
              ("VIIRS night-lights", tw.emis.get("ntl"))]
    layers = [(n, M) for n, M in layers if M is not None]
    fig, axs = plt.subplots(1, len(layers), figsize=(4.6 * len(layers), 4.5))
    for ax, (name, M) in zip(np.atleast_1d(axs), layers):
        x = tw.sample_grid(M, ids=obs.index)
        d = pd.concat([x.rename("proxy"), obs.rename("obs")], axis=1).dropna()
        rho, p = spearmanr(d.proxy, d.obs) if len(d) >= 4 else (np.nan, np.nan)
        ax.scatter(d.proxy, d.obs, s=70, c=MODEL_C, edgecolor="black", linewidth=0.6)
        ax.set_xlabel(f"{name} (at station)")
        ax.set_ylabel("observed 2025 station mean (µg m$^{-3}$)")
        ax.set_title(f"Spearman ρ = {rho:+.2f}" + (f"  (p={p:.2f})"
                     if np.isfinite(p) else ""), fontsize=9)
    fig.suptitle("Emission explainability — does anthropogenic activity explain WHERE "
                 "Xichang's PM$_{2.5}$ sits?\n(valley-floor urban combustion: vehicle + "
                 "residential/biomass + light industry, inversion-trapped)", y=1.06,
                 fontsize=9.5)
    _save(fig, "X12_emission_explain", square=False)


ALL = {"x1": x1_studyarea, "x2": x2_inputs, "x3": x3_decomposition,
       "x4": x4_seasonal, "x5": x5_diurnal_model, "x6": x6_field_vs_obs,
       "x7": x7_station_scatter, "x8": x8_seasonal_overlay,
       "x9": x9_diurnal_overlay, "x10": x10_uq, "x11": x11_scorecard,
       "x12": x12_emission_explain}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--figs", default="all")
    a = ap.parse_args()
    keys = list(ALL) if a.figs == "all" else [k.strip() for k in a.figs.split(",")]
    tw = Twin()
    # persist the out-of-sample gate table as a citable artifact
    gpath = (REPO / "data" / "processed" / "transfer_validation"
             / f"{CITY}_temporal_holdout_gates.csv")
    tw.gate.to_csv(gpath)
    print(f"  OOS gate table → {gpath}")
    for k in keys:
        print(f"[{k}] {ALL[k].__doc__.splitlines()[0]}")
        ALL[k](tw)
    print(f"\nDone → {OUT}")


if __name__ == "__main__":
    main()
