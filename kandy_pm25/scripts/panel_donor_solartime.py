"""panel_donor_solartime.py — rebuild the panel-mean diurnal donor in SOLAR time,
and check whether the validation cities leak into the training panel.

WHY (flagged caveat, 2026-07-25). The C/C' donor averaged 199 CNEMC cities using raw
CNEMC timestamps, which are Beijing civil time (UTC+8) for the whole country. China
spans ~60 deg of longitude on ONE timezone, so a western city's clock runs up to ~3 h
ahead of its sun. Averaging cities in civil time therefore smears the meteorological
part of the diurnal cycle (boundary-layer growth follows the SUN), even though it keeps
the emission part (rush hours follow the CLOCK) aligned. Neither reference is a priori
correct -- the observed shape is a mix -- so this builds the donor BOTH ways and lets
the transfer skill decide.

Targets are unaffected in practice: every target city's timezone is within ~0.4 h of its
solar time (Kandy -0.13 h, Medellin -0.04 h, Kathmandu -0.06 h, ChiangMai -0.40 h,
Chandigarh -0.38 h), so the distortion is essentially donor-side only.

ALSO (user question): can the analogue cities be used to TRAIN rather than only to
validate? That is only legitimate if the validation cities are not inside the training
panel. This script answers it by coordinate matching (name matching fails -- panel dirs
are slugs like city314 with Chinese `area` names).

Out: results/figures/multicity/panel_donor_solartime.{csv,txt}
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xichang_paper_figures as xf
from diurnal_transferability_test import PANEL, city_diurnal
from panel_mean_diurnal_transfer import observed_shape, TARGETS

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "figures" / "multicity"
MANIFEST = REPO / "data" / "processed" / "cnemc_panel" / "panel_manifest.csv"
CN_REF_MERIDIAN = 120.0          # UTC+8 reference meridian for CNEMC civil stamps


def to_solar(shape24: pd.Series, lon: float) -> pd.Series:
    """Shift a 24-point clock-hour climatology onto SOLAR hours.

    solar = civil + (lon - 120)/15. The offset is constant per city, so shifting the
    curve is exact up to the 1 h binning; interpolate circularly.
    """
    off = (lon - CN_REF_MERIDIAN) / 15.0
    h = np.arange(24)
    v = shape24.reindex(h).to_numpy(float)
    if not np.isfinite(v).all():
        return None
    # value at solar hour s equals the civil-time value at (s - off)
    src = (h - off) % 24
    ext_x = np.concatenate([h - 24, h, h + 24])
    ext_v = np.concatenate([v, v, v])
    return pd.Series(np.interp(src, ext_x, ext_v), index=h)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    man = pd.read_csv(MANIFEST).set_index("slug")
    lines = ["PANEL DONOR — solar-time rebuild + leakage check", "=" * 72]

    # ── 1. leakage: are the validation cities inside the training panel? ─────────
    from city_config import cfg
    lines += ["", "[1] LEAKAGE CHECK — nearest panel city to each validation city",
              "    (a match means that city cannot be BOTH training and independent test)"]
    leak = []
    for city in ["xichang", "taian", "baoji", "yichang", "bazhou", "chandigarh",
                 "kathmandu", "chiangmai", "medellin"]:
        try:
            c = cfg(city)
        except Exception:
            continue
        cen = c.get("cen")          # city_config stores the centre as `cen` = (lat, lon)
        if cen is None:
            bb = c.get("box")
            if not bb:
                continue
            clat = (bb[1] + bb[3]) / 2; clon = (bb[0] + bb[2]) / 2
        else:
            clat, clon = float(cen[0]), float(cen[1])
        d = np.hypot((man.lat - clat) * 111.0,
                     (man.lon - clon) * 111.0 * np.cos(np.radians(clat)))
        k = d.idxmin()
        leak.append(dict(city=city, nearest=k, area=man.loc[k, "area"],
                         km=round(float(d.min()), 1)))
        flag = "*** IN PANEL ***" if d.min() < 30 else "not in panel"
        lines.append(f"    {city:<11} nearest {k} ({man.loc[k,'area']}) "
                     f"{d.min():7.1f} km   {flag}")
    n_leak = sum(1 for r in leak if r["km"] < 30)
    lines.append(f"    -> {n_leak} of {len(leak)} validation cities sit inside the panel")

    # ── 2. donor built both ways ────────────────────────────────────────────────
    civil, solar = {}, {}
    for cd in sorted([p for p in PANEL.iterdir() if p.is_dir()]):
        s = city_diurnal(cd)
        if s is None:
            continue
        civil[cd.name] = s
        if cd.name in man.index:
            ss = to_solar(s, float(man.loc[cd.name, "lon"]))
            if ss is not None:
                solar[cd.name] = ss
    Mc, Ms = pd.DataFrame(civil), pd.DataFrame(solar)
    dc = Mc.mean(axis=1); dc /= dc.mean()
    ds = Ms.mean(axis=1); ds /= ds.mean()
    lines += ["", f"[2] DONOR  civil-time n={Mc.shape[1]}  |  solar-time n={Ms.shape[1]}",
              f"    civil: peak {int(dc.idxmax())}h trough {int(dc.idxmin())}h "
              f"swing {dc.max()-dc.min():.3f}",
              f"    solar: peak {int(ds.idxmax())}h trough {int(ds.idxmin())}h "
              f"swing {ds.max()-ds.min():.3f}",
              f"    longitude spread of panel: {man.lon.min():.1f}-{man.lon.max():.1f} E "
              f"=> solar offsets {(man.lon.min()-120)/15:+.1f} to {(man.lon.max()-120)/15:+.1f} h"]

    # ── 3. transfer to targets, both donors ─────────────────────────────────────
    lines += ["", "[3] TRANSFER r (donor shape vs the city's OWN observed diurnal)",
              f"    {'city':<12}{'region':<26}{'civil':>8}{'solar':>8}{'delta':>8}"]
    rows = []
    for city, desc, reg in TARGETS:
        try:
            obs = observed_shape(city)
        except Exception as e:
            lines.append(f"    {city:<12} SKIP ({str(e)[:40]})")
            continue
        idx = obs.dropna().index
        # LEAVE-ONE-OUT: 5 of the validation cities are IN the panel (section 1), so a
        # donor that includes the target is self-referential. Drop the target's own
        # panel slug before averaging whenever it is present.
        drop = next((r["nearest"] for r in leak
                     if r["city"] == city and r["km"] < 30), None)
        if drop is not None and drop in Mc.columns:
            dcx = Mc.drop(columns=[drop]).mean(axis=1); dcx /= dcx.mean()
            dsx = Ms.drop(columns=[drop]).mean(axis=1); dsx /= dsx.mean()
            loo = f" (LOO: -{drop})"
        else:
            dcx, dsx, loo = dc, ds, ""
        rc = float(np.corrcoef(obs.loc[idx], dcx.loc[idx])[0, 1])
        rs = float(np.corrcoef(obs.loc[idx], dsx.loc[idx])[0, 1])
        rows.append(dict(city=city, region=reg, r_civil=round(rc, 3),
                         r_solar=round(rs, 3), delta=round(rs - rc, 3), loo=bool(loo),
                         obs_peak=int(obs.idxmax()), obs_trough=int(obs.idxmin()),
                         obs_swing=round(float(obs.max() - obs.min()), 3)))
        lines.append(f"    {city:<12}{desc:<26}{rc:8.3f}{rs:8.3f}{rs-rc:+8.3f}{loo}")
    t = pd.DataFrame(rows)
    if len(t):
        out_ = t[t.region == "OUT"]; inr = t[t.region == "in"]
        lines += ["",
                  f"    OUT-of-region median: civil {out_.r_civil.median():+.3f} "
                  f"-> solar {out_.r_solar.median():+.3f}",
                  f"    in-region  median: civil {inr.r_civil.median():+.3f} "
                  f"-> solar {inr.r_solar.median():+.3f}" if len(inr) else ""]
        better = (t.delta > 0).sum()
        lines += ["",
                  f"VERDICT: solar-time donor is better at {better}/{len(t)} targets "
                  f"(median delta {t.delta.median():+.3f}).",
                  "Interpretation: the diurnal shape is a MIX of a sun-driven "
                  "meteorological part and a clock-driven emission part; whichever "
                  "reference wins tells us which part dominates the transferable signal."]
        t.to_csv(OUT / "panel_donor_solartime.csv", index=False)
    pd.DataFrame({"civil": dc, "solar": ds}).to_csv(OUT / "panel_donor_shapes.csv")
    txt = "\n".join(x for x in lines if x is not None)
    (OUT / "panel_donor_solartime.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
