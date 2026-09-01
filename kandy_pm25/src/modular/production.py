"""Binds the EXISTING production pipeline to the information-budget contract.

Every builder that produces a shipped artefact declares the budget it runs at. `declare()`
returns that budget and is meant to be called at the top of a build, so the declaration lives
next to the code rather than in a document that can drift from it.

This is deliberately a THIN layer. It does not change any builder's behaviour; it makes each
builder's information budget explicit and checkable. Tightening a declaration (or discovering
one is wrong) is then a code change with a failing test, not a discussion.
"""
from __future__ import annotations

from . import budgets as bd

# builder / artefact  ->  budget id
BINDINGS: dict[str, str] = {
    # --- Kandy production chain -----------------------------------------------------------
    # T(t) is trained on the FECT residual target AND amplitude-sharpened to FECT, so the
    # whole locked chain sits at Bud1 and scoring A(t) against FECT is in-sample.
    "predict_T_anchor_v3": "Bud1",
    "sharpen_T_diurnal": "Bud1",
    "build_additive_field_v2": "Bud1",
    "build_additive_field_v3": "Bud1",
    "webapp_export": "Bud1",

    # --- siblings, NOT rungs --------------------------------------------------------------
    "kandy_driver_tier_build": "BudExt",   # drops the satellite level anchor
    "kandy_extension_fields": "BudExt",
    "kandy_live_forecast": "Budf",

    # --- multi-city transfer validation ----------------------------------------------------
    # The panel is deliberately run at the two-sensor budget to emulate Kandy's data poverty.
    # That is the design; scoring happens on WITHHELD stations, which are not an input.
    "xichang_prod": "Bud1",
    "city_validation_scorecard": "Bud1",

    # --- sensorless track -------------------------------------------------------------------
    "track_t_a_sensorless": "Bud0",
}


class BindingError(RuntimeError):
    pass


def declare(builder: str) -> bd.Budget:
    """Return the declared budget for a builder, raising if it has none."""
    try:
        return bd.get(BINDINGS[builder])
    except KeyError:
        raise BindingError(
            f"builder {builder!r} has no declared information budget. Add it to "
            f"src/modular/production.BINDINGS before it can produce a shipped artefact."
        ) from None


def require(builder: str, *streams: str) -> bd.Budget:
    """Declare the budget AND assert the streams this builder is about to touch."""
    b = declare(builder)
    b.require(*streams)
    return b


def audit() -> list[dict]:
    """One row per binding: what it may use, what it estimates, whether it is a ladder rung."""
    rows = []
    for name, bid in sorted(BINDINGS.items()):
        b = bd.get(bid)
        rows.append({
            "builder": name, "budget": bid, "rung": b.nested and b.parent is not None or bid == "Bud0",
            "admits": ",".join(sorted(b.admits)),
            "estimates": ",".join(sorted(b.estimates)),
            "imposes": ",".join(sorted(b.imposes)),
        })
    return rows
