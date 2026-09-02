"""Information budgets and the tier contract.

Implements MODEL_SPECIFICATION.md section 5. An information budget declares WHICH observation
streams a tier may use. Builders assert against it, so a stream a tier is not entitled to is
unreachable by construction rather than by discipline.

This exists because two leakage defects were caught by audit AFTER the fact:
  - the temporal anchor was calibrated on the same sensors it was later scored against
    (in-sample circularity), and
  - a city-similarity descriptor was derived from the target city's own outcome, which leaks
    even under leave-one-out.
Both are admissibility errors. Admissibility is now a property of the code.

Budgets are NESTED: Bud0 subset Bud1 subset Bud2 subset Bud3 subset Bud4. The nesting is
asserted at import time (see _validate_registry), so a malformed budget cannot be registered.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, FrozenSet, Optional


# ── observation streams ───────────────────────────────────────────────────────────────────
# The atoms an information budget is built from. A stream is a KIND of information, not a file.

SATELLITE_LEVEL = "satellite_level"        # van Donkelaar / GHAP annual level products
DRIVERS_REANALYSIS = "drivers_reanalysis"  # ERA5 / GEOS-CF / CAMS / MERRA-2 exogenous drivers
STATIC_GEO = "static_geo"                  # DEM, road network, night lights, land cover
SENSOR_PAIR = "sensor_pair"                # <= 2 local low-cost sensors (the Kandy budget)
REFERENCE_MONITOR = "reference_monitor"    # continuous reference-grade local monitor (CEA)
REGIONAL_NETWORK = "regional_network"      # rural / regional stations, background-informing (NBRO)
SPATIAL_NETWORK = "spatial_network"        # passive samplers or mobile campaign (CEA NO2)
FORWARD_DRIVERS = "forward_drivers"        # forecast drivers, no contemporaneous observation

ALL_STREAMS = frozenset({
    SATELLITE_LEVEL, DRIVERS_REANALYSIS, STATIC_GEO, SENSOR_PAIR,
    REFERENCE_MONITOR, REGIONAL_NETWORK, SPATIAL_NETWORK, FORWARD_DRIVERS,
})

# Components the model estimates or imposes.
L, B, A, P, THETA, BIAS, U = "L", "B", "A", "P", "theta", "b_k", "U"


class AdmissibilityError(RuntimeError):
    """Raised when a tier touches a stream its budget does not admit."""


@dataclass(frozen=True)
class Budget:
    """One rung of the information ladder."""

    id: str
    admits: FrozenSet[str]
    estimates: FrozenSet[str]
    imposes: FrozenSet[str]
    parent: Optional[str] = None
    shrink_toward: Optional[str] = None
    nested: bool = True
    note: str = ""

    # `nested=False` marks a SIBLING rather than a rung: a budget that TRADES one stream for
    # another instead of adding to its parent. Such a budget is not on the ladder, so P2
    # monotonicity and P3 exact-degradation do not apply to it and must not be claimed.

    def admits_stream(self, stream: str) -> bool:
        return stream in self.admits

    def require(self, *streams: str) -> None:
        """Assert every stream is admissible at this budget, else raise."""
        bad = [s for s in streams if s not in self.admits]
        if bad:
            raise AdmissibilityError(
                f"budget {self.id} does not admit {bad}; admits={sorted(self.admits)}. "
                f"Either use a richer budget or remove the stream."
            )
        unknown = [s for s in streams if s not in ALL_STREAMS]
        if unknown:
            raise AdmissibilityError(f"unknown stream(s) {unknown}")

    def require_covers(self, *streams: str, allow: Iterable[str] = ()) -> None:
        """Assert this budget USES every stream it admits, else raise.

        `require()` is one-sided: it stops a tier reaching for information it has not been
        granted, and says nothing about a tier that quietly fails to use what it has. That
        asymmetry is not cosmetic. A rung which under-uses its budget inflates EVERY gain
        measured above it, because each higher rung is then scored against a baseline weaker
        than the one the specification promises -- and the registry passes it silently.

        That is exactly what happened (ledger F.84): the scored `Bud0` used seven meteorological
        drivers and neither of the other two streams it admits, so the reported value of the
        first local stations was measured against a baseline that knew nothing about the place.

        `allow` names streams deliberately omitted, and forces the omission to be written down
        at the call site rather than being inferred from silence.
        """
        used, waived = set(streams), set(allow)
        missing = sorted(self.admits - used - waived)
        if missing:
            raise AdmissibilityError(
                f"budget {self.id} ADMITS {missing} but the tier does not use them. "
                f"An under-powered rung inflates every gain measured above it (F.84). "
                f"Either supply these streams, or pass allow={missing!r} to declare the "
                f"omission explicitly."
            )

    def require_covers_units(
        self,
        coverage: "dict[str, Iterable[str]]",
        *,
        allow: Iterable[str] = (),
        label: str = "city",
    ) -> None:
        """Assert EVERY SCORED UNIT carries every stream this budget admits, else raise.

        `require_covers` closes the F.84 hole at the level of the TIER: the code declares which
        streams it is feeding in, and a stream left out has to be waived out loud. It cannot see
        one level down. A tier can pass it and still score individual cities that carry none of
        the data the tier is named for -- the stream is present in the design and absent in the
        row.

        That is exactly what happened (C7, plan 2026-09-01). `revalidate_ladder.py` merged the
        geography and satellite streams with how="left" and never dropped the misses, so one
        city was scored in `Bud0c` with no STATIC_GEO at all. Nothing failed, because
        HistGradientBoostingRegressor accepts NaN natively and simply trained around it. The
        defect surfaced only when a second script -- which had to drop those rows, because Ridge
        cannot take NaN -- disagreed by six percentage points on the headline first rung.
        Enforcing coverage moves `Bud0c -> Bud1` from 17.8% to 15.8%.

        The lesson generalises past this model: **a tolerant learner will silently absorb an
        admissibility error that a strict one would have raised.** Coverage has to be asserted
        on the data, not inferred from the fact that the fit converged.

        `coverage` maps each unit to the streams actually present for it, so this stays free of
        any dataframe dependency and is trivially testable. `allow` names streams that may be
        absent per unit, and forces that concession to be written at the call site.

        Raises rather than filtering: dropping a unit changes what the paper reports, so the
        caller must make that choice explicitly rather than inherit it from a helper.
        """
        waived = set(allow)
        required = self.admits - waived
        short: dict[str, list[str]] = {}
        for unit, present in coverage.items():
            gap = sorted(required - set(present))
            if gap:
                short[str(unit)] = gap
        if short:
            shown = ", ".join(f"{u} missing {g}" for u, g in sorted(short.items())[:5])
            more = "" if len(short) <= 5 else f" (+{len(short) - 5} more)"
            raise AdmissibilityError(
                f"budget {self.id}: {len(short)} of {len(coverage)} {label} units do not carry "
                f"every admitted stream -- {shown}{more}. A unit scored in a rung whose streams "
                f"it lacks is not in that rung (C7). Either restrict the frame to "
                f"stream-complete units and say so, or pass allow=[...] to declare the "
                f"concession."
            )


def require_stream_coverage(
    frame,
    column: str,
    *,
    unit: str = "city",
    min_unit_fraction: float = 0.30,
    min_units_covered: float = 0.80,
) -> None:
    """Assert a merged stream is actually PRESENT, not merely merged.

    A stream can join cleanly and arrive empty. The join key matches, the column exists, every
    value is NaN, and a tolerant learner fits it without a word. That happened five separate
    ways in one session:

      - a tier fed one of the three streams its budget admits (F.84),
      - a city scored in a rung whose stream it lacks (C7, `require_covers_units`),
      - a daily stream pulled for the wrong YEARS, so the merge matched almost nothing
        (gotcha #85: MAIAC pulled 2019-2022 against a frame spanning 2021-2026, 86% post-2023;
        median per-city day coverage came out at 0.0% and HistGradientBoostingRegressor
        returned a clean, plausible, meaningless -0.41%),
      - and a mixed date format that silently NaT'd 60% of rows on read (gotcha #46).

    `require_covers` and `require_covers_units` check the DESIGN and the ROWS. This checks the
    VALUES, which is the only level at which an empty-but-merged stream is visible.

    Raises rather than warning, and reports the distribution rather than a single number, so a
    stream that is present for a handful of units and absent for the rest cannot pass on its
    mean.

    Parameters
    ----------
    min_unit_fraction : the share of a unit's rows that must carry a non-null value for that
        unit to count as covered. Default 0.30 is deliberately permissive -- satellite streams
        have genuine cloud gaps, and the failure this guards against is 0%, not 40%.
    min_units_covered : the share of units that must clear `min_unit_fraction`.
    """
    if column not in frame.columns:
        raise AdmissibilityError(
            f"stream column {column!r} is not in the frame at all -- the merge did not happen")
    per_unit = frame.groupby(unit)[column].apply(lambda s: float(s.notna().mean()))
    covered = per_unit >= min_unit_fraction
    share = float(covered.mean()) if len(per_unit) else 0.0
    if share < min_units_covered:
        worst = per_unit.sort_values().head(5)
        detail = ", ".join(f"{u}={v:.1%}" for u, v in worst.items())
        raise AdmissibilityError(
            f"stream {column!r} is merged but EMPTY for most units: only {share:.0%} of "
            f"{len(per_unit)} {unit} units have >= {min_unit_fraction:.0%} of rows populated "
            f"(required {min_units_covered:.0%}). Median coverage {per_unit.median():.1%}. "
            f"Worst: {detail}. A merged-but-empty stream fits without error and means nothing "
            f"(gotcha #85) -- check the stream's date range against the frame's before pulling."
        )


_BASE = frozenset({SATELLITE_LEVEL, DRIVERS_REANALYSIS, STATIC_GEO})

REGISTRY: dict[str, Budget] = {}


def _reg(b: Budget) -> Budget:
    REGISTRY[b.id] = b
    return b


BUD0 = _reg(Budget(
    id="Bud0", admits=_BASE,
    estimates=frozenset({L, A, THETA}), imposes=frozenset({B, P}),
    note="sensorless. Level and a daily anomaly only -- supplies NO diurnal cycle.",
))

BUD1 = _reg(Budget(
    id="Bud1", admits=_BASE | {SENSOR_PAIR}, parent="Bud0", shrink_toward="Bud0",
    estimates=frozenset({L, A, THETA}), imposes=frozenset({B, P}),
    note="two elevation-gradient sensors. The deployed Kandy budget. "
         "A(t) is CALIBRATED on these sensors, so scoring A against them is in-sample.",
))

BUD2 = _reg(Budget(
    id="Bud2", admits=BUD1.admits | {REFERENCE_MONITOR}, parent="Bud1", shrink_toward="Bud1",
    estimates=frozenset({L, A, THETA, BIAS, U}), imposes=frozenset({B, P}),
    note="continuous reference monitor. First budget at which the low-cost-sensor bias b_k "
         "is identifiable, and the first at which lags are usable (a sequence model becomes "
         "justified for A(t)).",
))

BUD3 = _reg(Budget(
    id="Bud3", admits=BUD2.admits | {REGIONAL_NETWORK}, parent="Bud2", shrink_toward="Bud2",
    estimates=frozenset({L, A, B, THETA, BIAS, U}), imposes=frozenset({P}),
    note="regional/rural network. FIRST budget at which B(t) is estimated rather than imposed.",
))

BUD4 = _reg(Budget(
    id="Bud4", admits=BUD3.admits | {SPATIAL_NETWORK}, parent="Bud3", shrink_toward="Bud3",
    estimates=frozenset({L, A, B, P, THETA, BIAS, U}), imposes=frozenset(),
    note="spatial network or campaign. FIRST budget at which P(s,t) is constrained by local "
         "observation. Below this, five independent tests found no learnable spatial signal.",
))

BUDF = _reg(Budget(
    id="Budf", admits=frozenset({SATELLITE_LEVEL, STATIC_GEO, FORWARD_DRIVERS}),
    parent="Bud0", shrink_toward="Bud0", nested=False,
    estimates=frozenset({L, A}), imposes=frozenset({B, P, THETA}),
    note="forecast. Level only; P from climatology. Not contemporaneous with any observation. "
         "SIBLING, not a rung -- it trades contemporaneous drivers for forward ones.",
))

BUDEXT = _reg(Budget(
    id="BudExt", admits=frozenset({DRIVERS_REANALYSIS, STATIC_GEO, SENSOR_PAIR}),
    parent="Bud1", shrink_toward="Bud1", nested=False,
    estimates=frozenset({L, A, THETA}), imposes=frozenset({B, P}),
    note="the driver-anchored EXTENSION tier (years the satellite level anchor does not reach). "
         "SIBLING, not a rung: it DROPS satellite_level rather than adding a stream, so it is "
         "strictly LESS informed than Bud1 on the level. P2/P3 do not apply between them, and "
         "the extension tier must not be presented as a rung on the information ladder.",
))


def _validate_registry() -> None:
    """Nesting and internal consistency, asserted at import time."""
    for b in REGISTRY.values():
        if not b.admits <= ALL_STREAMS:
            raise AdmissibilityError(f"{b.id} admits unknown streams: {b.admits - ALL_STREAMS}")
        if b.estimates & b.imposes:
            raise AdmissibilityError(
                f"{b.id} both estimates and imposes {sorted(b.estimates & b.imposes)}")
        if b.parent is not None:
            if b.parent not in REGISTRY:
                raise AdmissibilityError(f"{b.id} names unknown parent {b.parent}")
            if b.nested and not REGISTRY[b.parent].admits < b.admits:
                raise AdmissibilityError(
                    f"nesting violated: {b.id} does not strictly contain {b.parent}")


_validate_registry()


def get(budget_id: str) -> Budget:
    try:
        return REGISTRY[budget_id]
    except KeyError:
        raise AdmissibilityError(
            f"unknown budget {budget_id!r}; known: {sorted(REGISTRY)}") from None


def chain(budget_id: str) -> list[str]:
    """The degradation chain from this budget down to the root."""
    out, cur = [], get(budget_id)
    while cur is not None:
        out.append(cur.id)
        cur = get(cur.parent) if cur.parent else None
    return out
