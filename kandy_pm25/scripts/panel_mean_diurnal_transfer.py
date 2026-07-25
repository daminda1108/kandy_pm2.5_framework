"""panel_mean_diurnal_transfer.py — does the PANEL-MEAN diurnal shape transfer OUT of
the Chinese panel to tropical / South-Asian cities? The test that decides whether a
sensorless diurnal is Kandy-relevant.

Chain of results:
  Option A  fixed sensor-free box model  e(h)/(BLH*|u|)^g   LOCO median r = 0.412
  Option B  learned, 5 training cities                      LOCO median r = 0.299
  pre-test  panel-mean shape vs held-out PANEL city         median r = 0.892  (!)
            -> the diurnal shape is largely UNIVERSAL; deriving it from meteorology was
               the wrong approach, and no hourly met pull is needed.

But those 199 panel cities are ALL Chinese (CNEMC). A Chinese-urban mean shape matching
other Chinese cities is weak evidence for Kandy — the same China-heavy-panel critique the
preprint already carries (A2). So: build the panel-mean shape from the Chinese panel ONLY,
then score it, with no tuning, against the observed diurnal shape of the non-Chinese
analogue cities (Medellin, Kathmandu, Chiang Mai) and the South-Asian one (Chandigarh).

If it holds out-of-region, a sensorless diurnal is available for Kandy today, at zero
data cost. If it fails, the universality is a Chinese-urban artefact.

Out: results/figures/multicity/panel_mean_diurnal_transfer.{csv,txt}
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xichang_paper_figures as xf
from diurnal_transferability_test import PANEL, city_diurnal

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "figures" / "multicity"
# non-Chinese / out-of-region targets, plus the Chinese analogues as in-region controls
TARGETS = [("medellin", "tropical Andean (Colombia)", "OUT"),
           ("kathmandu", "Himalayan bowl (Nepal)", "OUT"),
           ("chiangmai", "tropical SE Asia (Thailand)", "OUT"),
           ("chandigarh", "Indo-Gangetic plain (India)", "OUT"),
           ("xichang", "Chinese valley", "in"),
           ("taian", "Chinese valley", "in")]


def observed_shape(city):
    """Unit-mean observed diurnal shape for an analogue city (all stations, local time)."""
    xf._setup(city)
    from city_config import cfg
    obs = pd.concat([xf._obs(y) for y in cfg(city)["years"]], ignore_index=True)
    obs = obs.dropna(subset=["pm25"])
    obs["h"] = obs.loct.dt.hour
    obs["day"] = obs.loct.dt.floor("D")
    dm = obs.groupby("day").pm25.transform("mean")
    obs = obs[dm > 0]
    s = obs.pm25 / dm[dm > 0]
    clim = s.groupby(obs.h).mean()
    return (clim / clim.mean()).reindex(range(24))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # ── panel-mean shape from the CHINESE panel only (the donor) ──────────────────
    shapes = {}
    for cd in sorted([p for p in PANEL.iterdir() if p.is_dir()]):
        s = city_diurnal(cd)
        if s is not None:
            shapes[cd.name] = s
    M = pd.DataFrame(shapes)
    donor = M.mean(axis=1)
    donor = donor / donor.mean()
    print(f"donor panel-mean shape built from {M.shape[1]} Chinese panel cities")
    print("  donor peaks at hours: " +
          ", ".join(str(h) for h in donor.nlargest(3).index.tolist()) +
          f" | trough {donor.idxmin()} | swing {donor.max()-donor.min():.3f}")

    rows = []
    for city, desc, region in TARGETS:
        try:
            obs = observed_shape(city)
        except Exception as ex:
            print(f"  {city}: skip ({str(ex)[:60]})"); continue
        idx = obs.dropna().index.intersection(donor.dropna().index)
        if len(idx) < 20:
            print(f"  {city}: skip (incomplete diurnal)"); continue
        r = float(np.corrcoef(obs.loc[idx], donor.loc[idx])[0, 1])
        amp_o = float(obs.max() - obs.min()); amp_d = float(donor.max() - donor.min())
        rows.append(dict(city=city, region=region, desc=desc,
                         r_vs_panel_mean=round(r, 3),
                         obs_peak_h=int(obs.idxmax()), donor_peak_h=int(donor.idxmax()),
                         obs_trough_h=int(obs.idxmin()), donor_trough_h=int(donor.idxmin()),
                         amp_obs=round(amp_o, 3), amp_donor=round(amp_d, 3)))
        print(f"  {city:<11} r={r:+.3f}  obs peak {int(obs.idxmax()):02d}h "
              f"trough {int(obs.idxmin()):02d}h  swing {amp_o:.2f}")
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "panel_mean_diurnal_transfer.csv", index=False)

    out_ = t[t.region == "OUT"]; in_ = t[t.region == "in"]
    L = ["PANEL-MEAN DIURNAL SHAPE — does it transfer OUT of the Chinese panel?",
         "=" * 80,
         f"donor = unit-mean diurnal shape averaged over {M.shape[1]} Chinese CNEMC cities",
         f"donor peak {int(donor.idxmax())}h, trough {int(donor.idxmin())}h, "
         f"swing {donor.max()-donor.min():.3f}", "",
         f"{'city':<12}{'region':>7}{'r':>8}{'obs pk':>8}{'obs tr':>8}{'swing':>8}  regime",
         "-" * 80]
    for _, r in t.iterrows():
        L.append(f"{r.city:<12}{r.region:>7}{r.r_vs_panel_mean:8.3f}"
                 f"{r.obs_peak_h:8d}{r.obs_trough_h:8d}{r.amp_obs:8.2f}  {r.desc}")
    L += ["", f"OUT-of-region (n={len(out_)}): median r = {out_.r_vs_panel_mean.median():+.3f}"
              f"   min = {out_.r_vs_panel_mean.min():+.3f}",
          f"in-region    (n={len(in_)}): median r = {in_.r_vs_panel_mean.median():+.3f}",
          "",
          "REFERENCE  shipped 2-sensor diurnal median r = 0.708 | box model A = 0.412 |",
          "           learned B (5 cities) = 0.299 | within-panel ceiling = 0.892"]
    med = out_.r_vs_panel_mean.median() if len(out_) else np.nan
    worst = out_.r_vs_panel_mean.min() if len(out_) else np.nan
    if np.isfinite(med) and med >= 0.70 and worst >= 0.40:
        v = ("TRANSFERS OUT OF REGION — a sensorless diurnal is available for Kandy NOW, at\n"
             "         zero data cost: use the panel-mean shape (no met, no local sensor).\n"
             "         Next: condition on source mix / latitude to lift the weakest cities,\n"
             "         and gate as usual before it replaces the FECT-sharpened shape.")
    elif np.isfinite(med) and med >= 0.50:
        v = ("PARTIAL — transfers on average but with cities where it fails. Usable as a\n"
             "         disclosed fallback for a city with no sensors, not as a silent default.")
    else:
        v = ("DOES NOT TRANSFER — the within-panel universality is a Chinese-urban artefact.\n"
             "         Keep the disclosed 2-sensor/FECT product; record as a further null.")
    L += ["", f"VERDICT: {v}"]
    txt = "\n".join(L)
    (OUT / "panel_mean_diurnal_transfer.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)


if __name__ == "__main__":
    main()
