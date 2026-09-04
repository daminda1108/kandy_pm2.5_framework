"""D5 — budget matched validation, drawn as the procedure it is.

The protocol is what makes every number in Chapter 7 mean anything, and it is consistently the
hardest part of the method to convey in prose. A city with a dense network is deliberately
crippled down to the target city's information budget, then scored against the monitors that
were taken away from it. The match is the point: a model that has seen thirty monitors measures
a capability the target city will never have.

TOOL CHOICE. graphviz rather than schemdraw. The diagram branches and rejoins, and hand placing
a branch that must not collide is exactly what an automatic layout engine does better than a
person. schemdraw is kept for linear diagrams where position carries meaning.

LAYOUT LESSON, recorded because it applies to all twelve diagrams. The first draft had nine
boxes for a four step procedure and could not be made page shaped: top to bottom it came out at
aspect 0.46, left to right at 7.76. The fix was not a layout parameter, it was deleting five
boxes. A diagram of more than about six ranks will not sit on a page beside its caption.

Run: python d05_validation_protocol.py
Out: thesis/diagrams/D5_validation_protocol.{png,pdf}
"""
from __future__ import annotations

from thesisviz import C, gv_digraph, gv_note, gv_save


def main() -> None:
    g = gv_digraph("D5", rankdir="TB")
    g.attr(splines="polyline", nodesep="0.55", ranksep="0.42")

    g.node("split", "A donor city with a dense network\nsplit its stations",
           fillcolor=C["fill2"], shape="box", style="rounded,filled")

    with g.subgraph() as row:
        row.attr(rank="same")
        row.node("budget", "KEPT: the target city's budget\ndrivers, static geography,\n"
                           "satellite level, two sensors", fillcolor=C["fill2"])
        row.node("held", "WITHHELD: every other monitor\nnever seen by the fit",
                 fillcolor="#fbe3de")

    with g.subgraph() as row:
        row.attr(rank="same")
        row.node("pred", "Fit, and predict at\nthe withheld locations")
        row.node("obs", "Observed means\nat those locations", fillcolor="#fbe3de")

    g.node("score", "Score at the withheld sites\nRMSE and rank correlation",
           fillcolor=C["fill2"], shape="box", style="rounded,filled")

    g.edge("split", "budget")
    g.edge("split", "held")
    g.edge("budget", "pred")
    g.edge("held", "obs")
    g.edge("pred", "score")
    g.edge("obs", "score")

    gv_note(g, "Repeated for each budget tier, this produces one rung of the ladder. The budget "
               "match is what makes\nthe test informative: a model that has seen thirty monitors "
               "measures a capability the target city\nwill never have.")

    p = gv_save(g, "D5_validation_protocol")
    print(f"  wrote {p}")


if __name__ == "__main__":
    main()
