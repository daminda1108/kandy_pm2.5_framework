"""The graphviz diagrams: D1, D3, D6, D7, D9, D10.

One module rather than six files, because they share a tool, a palette and a set of layout
constraints, and keeping them together makes the constraints visible. The matplotlib ones live
in d_schematics.py.

LAYOUT RULES, learned from D5 and applied to all of these:
  - six ranks maximum. If it does not fit, delete content before touching ranksep.
  - the diagram's point goes in the graph label, never in a node.
  - colour carries meaning: blue is information that is free everywhere, red is information
    that must be bought, grey is a step in the machinery.

Usage: python d_flowcharts.py [--only D1]
Out:   thesis/diagrams/D*.png and .pdf
"""
from __future__ import annotations

import argparse
import sys

from thesisviz import C, gv_digraph, gv_note, gv_save


# ── D1: the pipeline ──────────────────────────────────────────────────────────────────────

def d1_pipeline():
    """Chapter 4. What goes in, what is computed, what comes out.

    A reader cannot follow Chapters 6 to 8 without this. It is deliberately the only diagram
    that shows the whole thing at once; every later diagram expands one box of it.
    """
    g = gv_digraph("D1", rankdir="TB")
    g.attr(nodesep="0.35", ranksep="0.40", splines="polyline")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("drv", "Reanalysis drivers\nwind, boundary layer,\ntemperature, humidity",
               fillcolor=C["fill2"])
        s.node("sat", "Satellite\naerosol optical depth\nand annual level", fillcolor=C["fill2"])
        s.node("geo", "Static geography\nterrain, roads, land cover,\npopulation, night lights",
               fillcolor=C["fill2"])
        s.node("obs", "Local sensors\ntwo, low cost", fillcolor="#fbe3de")

    g.node("anchor", "T(t)  temporal anchor\nboosted trees on drivers,\n"
                     "anchored to the satellite level")
    g.node("bg", "B(t)  regional background\nrural floor and seasonal shape,\n"
                 "capped so it cannot exceed the total")
    g.node("pat", "P(x,y,t)  local pattern\nemission proxy times confinement,\n"
                  "normalised to unit spatial mean")
    g.node("field", "PM(x,y,t) = B + max(inc,0)P + min(inc,0) + e(t)(P-1)",
           fillcolor=C["fill2"], shape="box", style="rounded,filled")
    g.node("out", "Hourly field at 1 km\nwith calibrated intervals",
           fillcolor=C["fill2"], shape="box", style="rounded,filled")

    g.edge("drv", "anchor")
    g.edge("sat", "anchor")
    g.edge("obs", "anchor", label="  calibrates")
    g.edge("drv", "bg")
    g.edge("geo", "pat")
    g.edge("anchor", "field")
    g.edge("bg", "field")
    g.edge("pat", "field")
    g.edge("field", "out")

    gv_note(g, "The level is carried by T(t) and is what the observations constrain. The "
               "pattern only decides where\nthe material sits, and because it has unit mean it "
               "cannot change how much of it there is.")
    return g, "D1_pipeline"


# ── D3: budget tiers ──────────────────────────────────────────────────────────────────────

def d3_tiers():
    """Chapter 6. The tiers, what each adds, and the degradation that runs backwards."""
    # Vertical: it is called a ladder, and left to right came out at aspect 6.25.
    g = gv_digraph("D3", rankdir="TB")
    g.attr(nodesep="0.30", ranksep="0.30", splines="polyline")

    # Two columns: the tier on the left, what it can newly constrain on the right. Stacking
    # all five pieces of text in one node gave five ranks of five lines and aspect 0.54.
    tiers = [
        ("b0", "Bud0  sensorless\nsatellite, drivers, static geography", "level", C["fill2"]),
        ("b1", "Bud1  two sensors\n+ two local low cost sensors",
         "diurnal and seasonal shape", "#fbe3de"),
        ("b2", "Bud2  reference\n+ a reference monitor", "instrument bias", "#fbe3de"),
        ("b3", "Bud3  regional\n+ a rural or regional network", "the background B(t)", "#fbe3de"),
        ("b4", "Bud4  spatial\n+ a passive network or campaign",
         "the pattern P\ndeclared, not validated", "#efefef"),
    ]
    for nid, left, gives, fill in tiers:
        with g.subgraph() as row:
            row.attr(rank="same")
            row.node(nid, left, fillcolor=fill)
            row.node(nid + "_c", gives, shape="plaintext", style="", fillcolor="white",
                     fontcolor=C["muted"])
        g.edge(nid, nid + "_c", style="dotted", color=C["muted"], arrowhead="none",
               label="  constrains")

    ids = [t[0] for t in tiers]
    for a, b in zip(ids, ids[1:]):
        g.edge(a, b, label="  adds")
    for a, b in zip(ids[1:], ids):
        g.edge(a, b, label="  degrades\n  bit-exactly", style="dashed",
               color=C["muted"], fontcolor=C["muted"], constraint="false")

    gv_note(g, "The tiers are nested, so a lower tier is not a different model but the same "
               "model with a stream\nwithheld. That is what turns an ablation into a "
               "measurement. Bud4 is a declared design\nassumption and is drawn in grey for "
               "that reason.")
    return g, "D3_budget_tiers"


# ── D6: the pre-registration workflow ─────────────────────────────────────────────────────

def d6_prereg():
    """Chapter 7. Pre-registration drawn as the procedure it is, including the branch that
    distinguishes an honest amendment from a rescued hypothesis."""
    g = gv_digraph("D6", rankdir="TB")
    g.attr(nodesep="0.45", ranksep="0.38", splines="polyline")

    g.node("state", "State the prediction, the refutation\ncriterion, and the detection limit",
           fillcolor=C["fill2"], shape="box", style="rounded,filled")
    g.node("reg", "Register it\nthe timestamp is the whole point")
    g.node("defect", "Defect found in the machinery?", shape="diamond",
           fillcolor="white", style="filled")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("amend", "Before scoring:\namend, dated, and say so", fillcolor=C["fill"])
        s.node("run", "Score against the\nregistered criterion")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("held", "HELD", fillcolor="#e8f2e0", color=C["good"])
        s.node("ref", "REFUTED", fillcolor="#fbe0ee", color=C["bad"])

    g.edge("state", "reg")
    g.edge("reg", "defect")
    g.edge("defect", "amend", label="  yes")
    g.edge("defect", "run", label="  no")
    g.edge("amend", "run")
    g.edge("run", "held")
    g.edge("run", "ref")

    gv_note(g, "After scoring there is no amendment. A criterion changed once the result is "
               "known is not a criterion,\nand a null reported without the detection limit "
               "converts a limit of the experiment into a\nproperty of the world.")
    return g, "D6_prereg_workflow"


# ── D7: the claims gate ───────────────────────────────────────────────────────────────────

def d7_claims_gate():
    """Chapter 10. How a number gets from a scored file into the text, and what stops it
    getting there any other way."""
    g = gv_digraph("D7", rankdir="TB")
    g.attr(nodesep="0.40", ranksep="0.38", splines="polyline")

    g.node("scored", "Scored files\nladder, field, test outputs", fillcolor=C["fill2"])
    g.node("gen", "build_claims.py\nrecomputes every number\nwith statistic, n, source, ledger")
    g.node("json", "claims.json")
    g.node("prose", "Prose carries {{claim:tag}},\nnever a typed number", fillcolor=C["fill2"])
    g.node("check", "Recompute and compare", shape="diamond", fillcolor="white", style="filled")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("fail", "BUILD REFUSED\nprose and data disagree",
               fillcolor="#fbe0ee", color=C["bad"])
        s.node("ok", "Build the document", fillcolor="#e8f2e0", color=C["good"])

    g.edge("scored", "gen")
    g.edge("gen", "json")
    g.edge("json", "check")
    g.edge("prose", "check")
    g.edge("check", "fail", label="  drift")
    g.edge("check", "ok", label="  agree")

    gv_note(g, "Nine numbers in this project had gone stale against their own source before "
               "this existed, including\none stated three different ways in a single document. "
               "Every one was found by a gate like this\nand none by reading.")
    return g, "D7_claims_gate"


# ── D9: what to buy first ─────────────────────────────────────────────────────────────────

def d9_acquisition():
    """Chapter 9. The practical output of the whole thesis, drawn as the decision it is."""
    g = gv_digraph("D9", rankdir="TB")
    g.attr(nodesep="0.45", ranksep="0.40", splines="polyline")

    g.node("start", "A city with no monitoring\nand a fixed budget",
           fillcolor=C["fill2"], shape="box", style="rounded,filled")
    g.node("free", "First, take the free data\nterrain, roads, land cover, population,\n"
                   "night lights, reanalysis, satellite\ncost: nothing", fillcolor=C["fill2"])
    g.node("band", "Which latitude band?", shape="diamond", fillcolor="white", style="filled")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("trop", "Deep tropics\nBUY TWO LOCAL SENSORS FIRST\nthen a regional background",
               fillcolor="#fbe3de")
        s.node("other", "Elsewhere\nBUY A REGIONAL BACKGROUND FIRST\nthen local sensors",
               fillcolor="#fbe3de")

    g.node("never", "Do not buy monitors three to eight.\nThey are worth nothing measurable.",
           fillcolor="#efefef", color=C["muted"], fontcolor=C["muted"])

    g.edge("start", "free")
    g.edge("free", "band")
    g.edge("band", "trop", label="  deep tropical")
    g.edge("band", "other", label="  other")
    g.edge("trop", "never", style="dashed", color=C["muted"])
    g.edge("other", "never", style="dashed", color=C["muted"])

    gv_note(g, "The ordering inverts between the two branches, and the pooled recommendation "
               "is the wrong one for\nthe tropics. A programme in Colombo or Kandy following "
               "the pooled advice would buy the\nwrong instrument first.")
    return g, "D9_acquisition"


# ── D10: who owns which artefact ──────────────────────────────────────────────────────────

def d10_regen_chain():
    """Appendix. The regeneration chain, which exists because a correction written to a file
    that a script regenerates is a correction that will be silently discarded."""
    # Vertical: six steps left to right came out at aspect 12.44, a strip.
    g = gv_digraph("D10", rankdir="TB")
    g.attr(nodesep="0.25", ranksep="0.26", splines="polyline")

    steps = [
        ("t", "predict_T_anchor_v3.py", "T_kandy_hourly_{y}"),
        ("s", "sharpen_T_diurnal.py", "same files, in place"),
        ("m", "build_decomp_map.py", "decomp_predictions_{y}"),
        ("o", "build_overlay_predictions.py", "..._4factor"),
        ("u", "build_spatial_uq.py", "..._spuq"),
        ("a", "build_additive_field.py", "..._additive_v3"),
    ]
    for nid, script, artefact in steps:
        g.node(nid, f"{script}\nowns: {artefact}")
    for a, b in zip([s[0] for s in steps], [s[0] for s in steps[1:]]):
        g.edge(a, b)

    g.node("fig", "figures and exports\nread the shipped field", fillcolor=C["fill2"])
    g.edge("a", "fig")

    gv_note(g, "Before writing a correction to a file, establish which script owns that file's "
               "contents. A background\nre-level was once applied directly to the stored "
               "product, and the next rebuild discarded it\nwithout an error.")
    return g, "D10_regeneration_chain"


BUILDERS = {
    "D1": d1_pipeline, "D3": d3_tiers, "D6": d6_prereg,
    "D7": d7_claims_gate, "D9": d9_acquisition, "D10": d10_regen_chain,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    todo = [a.only] if a.only else list(BUILDERS)

    from PIL import Image
    for key in todo:
        g, name = BUILDERS[key]()
        p = gv_save(g, name)
        w, h = Image.open(p).size
        flag = "" if 0.8 <= w / h <= 2.6 else "   <-- check aspect, may not fit a page"
        print(f"  {key:<4} {name:<28} {w}x{h}  aspect {w/h:.2f}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
