"""assembly.py — the additive decomposition at an analogue city (Kandy recipe).

    PM(x, y, t) = B(t) + [T(t) − B(t)] · P_local(x, y, t)

faithful to the locked Kandy headline:
  * B(t)      = B_annual(year) × GEOS-CF daily seasonal shape (diurnally flat),
                with B_annual = (1 − f) · L(year) and **f = the literature SA
                point estimate** (prereg §2 + Amendment 1 — the rural floor is
                the V6a diagnostic, NOT the assembly input).
  * T(t)      = the anchor-pair temporal anchor (t_anchor.fit_and_build).
  * P_local   = unit-mean S_emit(x,y) × M(x,y,t) confinement, normalised so the
                domain mean is exactly 1 every hour (basin mean preserved —
                Kandy G1 invariant). A_transport (WindNinja overlay) is NOT
                included — it is the Kandy scenario layer and its per-city wind
                library is not built; documented omission.
  * M(x,y,t)  = 1 + κ·w(BLH_t)·c(x,y);  c = clip(zscore(−Δz), ±2.5) re-centred;
                w = clip((H_ridge − BLH)/H_ridge, 0, 1); κ = 0.15 (Kandy prior);
                H_ridge = 0.75 × range(Δz) per city (the same rule that gives
                Kandy's 300 m from its 414 m max Δz).
  * UQ        = PI width carried by the increment: q05/q95 = B + (T_q05/q95 − B)·P
                (background shifts the centre, not the width — Kandy convention).

For scoring we evaluate the field AT STATION COORDINATES (P_local interpolated
to each station), which is exact for this separable field — no full grid needed.
"""
from __future__ import annotations

import numpy as np

KAPPA = 0.15
CLIP_SIGMA = 2.5
NGRID = 64           # normalisation grid for unit-mean P_local


def _terrain(cp):
    z = np.load(cp.terrain_npz(), allow_pickle=True)
    lat = np.asarray(z["lat_grid"], dtype=float)
    lon = np.asarray(z["lon_grid"], dtype=float)
    dz = np.asarray(z["delta_z"], dtype=float)
    lat1, lon1 = lat[:, 0], lon[0, :]
    if lat1[0] > lat1[-1]:
        lat1, dz = lat1[::-1], dz[::-1, :]
    return lat1, lon1, dz


def _interp2(lat1, lon1, F, la, lo):
    """Bilinear sample of F(lat, lon) at points (la, lo), clipped to the grid."""
    from scipy.interpolate import RegularGridInterpolator
    f = RegularGridInterpolator((lat1, lon1), F, bounds_error=False, fill_value=None)
    return f(np.column_stack([np.clip(la, lat1[0], lat1[-1]),
                              np.clip(lo, lon1[0], lon1[-1])]))


def spatial_fields(cp):
    """S_emit, confinement c, and their station samples. Returns dict."""
    from .vand import s_emit_pattern
    lat1, lon1, dz = _terrain(cp)
    # canonical normalisation grid over the terrain footprint
    glat = np.linspace(lat1[0], lat1[-1], NGRID)
    glon = np.linspace(lon1[0], lon1[-1], NGRID)
    S = s_emit_pattern(cp, glat, glon)                    # unit mean by construction
    # confinement on the native terrain grid, then sampled like S
    c = -(dz - np.nanmean(dz)) / np.nanstd(dz)
    c = np.clip(c, -CLIP_SIGMA, CLIP_SIGMA)
    c = c - np.nanmean(c)
    h_ridge = 0.75 * float(np.nanmax(dz) - np.nanmin(dz))
    st = cp.stations()
    return {
        "glat": glat, "glon": glon, "S": S,
        "lat1": lat1, "lon1": lon1, "c": c, "h_ridge": h_ridge,
        "S_at": _interp2(glat, glon, S, st.lat.to_numpy(), st.lon.to_numpy()),
        "c_at": _interp2(lat1, lon1, c, st.lat.to_numpy(), st.lon.to_numpy()),
        "c_grid_on_S": _interp2(lat1, lon1, c,
                                np.meshgrid(glat, glon, indexing="ij")[0].ravel(),
                                np.meshgrid(glat, glon, indexing="ij")[1].ravel()
                                ).reshape(NGRID, NGRID),
        "station_id": st.station_id.to_numpy(),
    }


def b_hourly(cp, T, f_local: float):
    """B(t) on T's hourly index: per-year (1−f)·L(year) × GEOS-CF daily shape."""
    import pandas as pd
    from . import drivers
    from .vand import level_for_year
    g = drivers.geos_cf_prior(cp)
    g["date"] = g.datetime.dt.floor("D")
    daily = g.groupby("date").pm25_prior.mean()
    out = pd.Series(np.nan, index=T.datetime)
    for y in sorted(set(cp.score_years)):
        L, _ = level_for_year(cp, y)
        b_ann = (1.0 - f_local) * L
        d = daily[daily.index.year == y]
        if len(d) == 0:
            continue
        shape = d / d.mean()                              # mean-1 seasonal shape
        sel = T.datetime.dt.year == y
        out.loc[T.datetime[sel]] = (b_ann *
            T.datetime[sel].dt.floor("D").map(shape).to_numpy())
    return out.to_numpy()


def predict_at_stations(cp, T, fields, f_local: float):
    """Hourly PM quantiles at every station → long DataFrame.

    Columns: datetime, station_id, pm_q05, pm_q50, pm_q95.
    """
    import pandas as pd
    from . import drivers
    B = b_hourly(cp, T, f_local)
    blh = drivers.blh(cp).set_index("datetime").blh_m
    w = np.clip((fields["h_ridge"] - T.datetime.map(blh).to_numpy())
                / fields["h_ridge"], 0, 1)
    w = np.nan_to_num(w, nan=0.0)

    # κ override via fields (post-hoc ablation hook; default = locked prior)
    kap = float(fields.get("kappa", KAPPA))

    # per-hour normaliser so domain-mean(P_local)=1 exactly (G1 invariant):
    # mean over grid of S·(1+κ w c) = 1 + κ w mean(S·c)  (since mean S=1, mean c≈0)
    sc_grid = float(np.nanmean(fields["S"] * fields["c_grid_on_S"]))
    norm = 1.0 + kap * w * sc_grid

    frames = []
    for i, sid in enumerate(fields["station_id"]):
        P = fields["S_at"][i] * (1.0 + kap * w * fields["c_at"][i]) / norm
        frames.append(pd.DataFrame({
            "datetime": T.datetime.to_numpy(), "station_id": sid,
            "pm_q05": B + (T.T_q05.to_numpy() - B) * P,
            "pm_q50": B + (T.T_q50.to_numpy() - B) * P,
            "pm_q95": B + (T.T_q95.to_numpy() - B) * P,
        }))
    return pd.concat(frames, ignore_index=True)
