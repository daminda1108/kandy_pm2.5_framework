"""Sector-weighted emission surface.

THE DEFECT THIS FIXES. `city_config.CITIES[slug]["emix"]` already declares a per-city source mix
(vehic / heat / burn) and it feeds ONLY the emission-timing profile e(t).
`build_traffic_emission.py` contains no reference to it, so the SPATIAL surface is
traffic-centrality alone. At Kathmandu the model therefore asserts 50% biomass burning in TIME
and 100% road network in SPACE. That inconsistency is the recorded Yichang failure mode: a
source spatially decoupled from the road network puts the hotspots in the wrong place.

THE FORM.

    S_emit(x,y) = norm( sum_k  w_k * norm(proxy_k(x,y)) )

Each sector proxy is normalised to unit mean BEFORE weighting, so `w_k` are true emission
shares and not an artefact of proxy units. The sum is renormalised, so the surface stays
unit-mean and the T-lock is untouched.

WHAT THIS IS NOT. Still not a source apportionment (gotcha #59). The LEVEL is carried by T(t)
and reflects all sources however the pattern is built. This changes only WHERE the local
increment is placed, never how much of it there is.

IDENTIFIABILITY. `w_k` cannot be fitted below Bud4 — five independent spatial tests found no
learnable spatial signal, and F.50 measured how little the spatial rungs buy. The weights are
therefore IMPOSED from an inventory (EDGAR / CAMS-GLOB-ANT sector shares) or from the declared
`emix`. They are declared, never learned. In the budget matrix the cell stays `imposed`; only
its provenance improves.

GRACEFUL DEGRADATION. `emix = {"vehic": 1.0}` reproduces the traffic-only surface bit-exactly,
so adopting this cannot silently move any existing city (tested).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


class ProxyError(RuntimeError):
    """A declared sector has no spatial proxy and no admissible fallback."""


def unit_mean(a: np.ndarray) -> np.ndarray:
    """Normalise a positive surface to unit spatial mean."""
    a = np.asarray(a, dtype=float)
    if not np.isfinite(a).any():
        raise ProxyError("proxy is entirely non-finite")
    a = np.where(np.isfinite(a), a, np.nan)
    m = np.nanmean(a)
    if not np.isfinite(m) or m <= 0:
        raise ProxyError(f"proxy has non-positive mean ({m})")
    out = a / m
    return np.where(np.isfinite(out), out, 1.0)


# ── sector proxies ────────────────────────────────────────────────────────────────────────
# Each entry documents WHAT the proxy is and WHY it stands for that sector. A sector with no
# proxy is not silently dropped -- see `compose`.

def proxy_vehicular(g: dict) -> np.ndarray:
    """Road-network centrality x congestion emission factor. The existing surface."""
    return g["traffic"]


def proxy_residential(g: dict) -> np.ndarray:
    """Residential combustion (heating, cooking) co-locates with people.

    Population density is the standard proxy; night lights are an accepted substitute where
    population is unavailable.
    """
    if "population" in g:
        return g["population"]
    if "ntl" in g:
        return g["ntl"]
    raise ProxyError("residential sector needs a population or night-lights surface")


def proxy_burning(g: dict) -> np.ndarray:
    """Open burning (agricultural residue, waste, brick kilns).

    PREFERRED: an observed fire-density climatology or a kiln/industrial land-cover mask.
    FALLBACK (flagged): a peri-urban ring built from population -- open burning concentrates
    at the settled fringe rather than the dense core. The fallback is a PLACEHOLDER; any result
    that depends on it is flagged in the provenance so it cannot be quoted as though it rested
    on observed fire data.
    """
    if "fire" in g:
        return g["fire"]
    if "population" in g:
        p = unit_mean(g["population"])
        # fringe weighting: peaks at moderate density, falls in the dense core and the empty
        # periphery. Deliberately crude -- it is a placeholder, and it is labelled as one.
        s = p / (1.0 + p)
        return s * (1.0 - s / max(float(np.nanmax(s)), 1e-9)) + 1e-6
    raise ProxyError("burning sector needs a fire-density or population surface")


def proxy_industry(g: dict) -> np.ndarray:
    """Industrial point/area sources -- the Yichang failure mode.

    Needs an industrial land-use mask or an SO2 hotspot field; there is no defensible
    population-based fallback, because industry is precisely the sector that does NOT track
    population or roads.
    """
    if "industry" in g:
        return g["industry"]
    raise ProxyError("industry sector needs an industrial land-use or SO2 surface; there is "
                     "no admissible fallback -- industry is by definition the sector that "
                     "does not co-locate with roads or population")


PROXIES = {
    "vehic": proxy_vehicular,
    "heat": proxy_residential,
    "burn": proxy_burning,
    "industry": proxy_industry,
}

# Sectors whose current proxy is a documented placeholder rather than an observation.
PLACEHOLDER_WHEN_FALLBACK = {"burn"}


@dataclass
class Surface:
    S: np.ndarray
    weights_used: dict
    provenance: list = field(default_factory=list)
    dropped: dict = field(default_factory=dict)

    @property
    def is_placeholder_dependent(self) -> bool:
        return any("PLACEHOLDER" in p for p in self.provenance)


def compose(grids: dict, emix: dict, strict: bool = False) -> Surface:
    """Build the sector-weighted unit-mean emission surface.

    grids  -- available spatial proxies, e.g. {"traffic": A, "population": B, "fire": C}
    emix   -- declared source mix, e.g. {"vehic": 0.4, "heat": 0.1, "burn": 0.5}
    strict -- raise if any declared sector lacks a proxy, instead of redistributing its weight

    A sector that cannot be built is NOT silently ignored: its weight is redistributed over the
    sectors that can, and both the drop and the redistribution are recorded. Silently dropping
    it would quietly turn a mixed-source city back into a traffic-only one -- exactly the
    defect this module exists to fix.
    """
    w = {k: float(v) for k, v in emix.items() if float(v) > 0}
    if not w:
        raise ProxyError("emix declares no sector with positive weight")

    built, dropped, prov = {}, {}, []
    for sector, weight in w.items():
        fn = PROXIES.get(sector)
        if fn is None:
            dropped[sector] = f"unknown sector {sector!r}"
            continue
        try:
            surf = unit_mean(fn(grids))
        except ProxyError as e:
            dropped[sector] = str(e)
            continue
        built[sector] = surf
        if sector in PLACEHOLDER_WHEN_FALLBACK and "fire" not in grids:
            prov.append(f"{sector}: PLACEHOLDER fringe proxy (no fire/land-cover surface)")
        else:
            prov.append(f"{sector}: observed proxy")

    if dropped and strict:
        raise ProxyError(f"sectors without a proxy: {dropped}")
    if not built:
        raise ProxyError(f"no sector could be built; dropped={dropped}")

    kept = {k: w[k] for k in built}
    tot = sum(kept.values())
    kept = {k: v / tot for k, v in kept.items()}
    if dropped:
        prov.append(f"weight of {sorted(dropped)} redistributed over {sorted(kept)}")

    S = sum(kept[k] * built[k] for k in built)
    return Surface(S=unit_mean(S), weights_used=kept, provenance=prov, dropped=dropped)
