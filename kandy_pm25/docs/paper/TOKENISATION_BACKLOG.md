# Numbers in the manuscript that the claims gate does not protect

`build_claims.py` emits 186 claims and the manuscript resolves 149 of them. Everything else that
looks like a number in the text falls into one of three groups. This file exists because the
third group is the dangerous one and it should be visible rather than implicit.

Last audited 2026-09-04, against the 18-figure build.

## 1. External values — correctly NOT tokenised

Putting someone else's measurement in `claims.json` would give it provenance it does not have:
the file's contract is "this value was recomputed from a scored file in this repository". These
stay as cited text.

| value | where | source |
|---|---|---|
| 110 → 4 µg m⁻³ over 300 m, R² 0.82 | §5.1, §5.2 | Elangasinghe & Shanthini, 25-site survey |
| ~400,000 population | §1.4, §6.1 | census |
| WHO annual guideline and 24-hour interim target | §6.2, §6.4 | WHO 2021 |
| ~9,500 training stations in the fused product | §4.5 | Wei et al. |
| the four Kandy point records (19.6, 22.7, 19.49, 17.8) | §6.5 | Nirmani, Attanayake, Dhammapala |
| ~18–19 µg m⁻³ BAM-anchored | §6.5 | Dhammapala |
| ~25 km composition-product resolution | §6.8 | GEOS-CF documentation |
| 1–2 OC/BC for traffic aerosol | §6.8 | source-apportionment literature |

## 2. Structural constants — not measurements

Configuration and definitions. Wrong only if the model changes, in which case the code changes
with them.

15 × 15 km domain · 1 km reporting resolution · the nominal 90 per cent interval · the 48-hour
episode window · 2019–2026 coverage · 80 per cent power as the design threshold · 1.0 as the
exponent for pure inverse-BLH dilution.

`subgrid.production_res_m` (238 m) is in this group but IS tokenised, because §5 compares it
against a second resolution and the two must be quoted from one place.

## 3. 🔴 Computed here, and still typed — the backlog

Each of these was computed by this project and is currently a literal in the prose. None is known
to be wrong; each is unprotected, which is exactly the condition that produced C2, C3, C4 and
the "32 countries" error. Ranked by consequence.

| value | where | what it needs | ledger |
|---|---|---|---|
| 93 km, r = 0.604, benchmark 0.923 | §7 | **no artefact on disk.** The Kandy–Colombo donor test was run and reported but its output was never written to a file. Re-run and emit. | F.63 |
| 15.6% pixel lift above the basin mean | §6.5 | one line against the shipped field at the NBRO pixel | — |
| 38.5% of hours with T < B; inversion 38.2% → 0.0% | §2.5 | derivable from the shipped anchor and background | gotcha #57 |
| background exceeded total in 24.8–36.1% of hours, mean 29.9% | §2.6 | pre-cap diagnostic; recompute from the v1 background | F.43 |
| constraint sweep: 0 → 0.08 moves f 0.477 → 0.502; rolling-window forms give 0.481, 0.487, 0.540 | §2.6 | the sweep script exists but writes no artefact | F.43 |
| ρ ≈ 0.2–0.28 spatial ceiling | §5.4, §5.7 | a range quoted from several runs; needs one canonical source or an explicit "as reported across the programme" | F.56 |
| 1.26–1.47 observed at comparable cities | §5.6 | source not identified in this pass | F.71 |
| 68 features in the sensorless tier | §4.4 | one line from the fitted frame | — |
| 33 cities in the single-country mid-latitude arm | §4.6 | from the pre-amendment design | Amendment 2 |
| 5 deep-tropical vs 32 temperate reference clusters | §4.6 | from the global census, not from the panel | F.53 |

**Rule for this file.** A number moves out of group 3 only by acquiring a generating script or a
citation. It does not move by being checked once by hand — that is how all of these got here.
