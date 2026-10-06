[STATUS: STUB — outline only, not drafted. Lower-risk section (describes already-built
machinery); good candidate for next writing session. Draft AFTER Results numbers are finalized
so cross-references are accurate, but the prose itself can be written now since it doesn't
depend on the moving numbers.]

# 2. Methods

## 2.1 The declared information-budget framework
- Define tiers Bud0–Bud4 precisely: what each admits, estimates, imposes.
- The coverage-checking mechanism (`require()` / `require_covers()`) — both directions of
  failure it catches, with the F.84 under-powered-tier example as the motivating case.
- Figure F1 goes here (see figures/FIGURE_PLAN.md) — write the introducing paragraph before
  placing it, per house style rule 1.

## 2.2 The 48-city panel
- Construction: OpenAQ, CNEMC, national networks. Climate-band assignment.
- Sample sizes per band (13 temperate, ? subtropical, ? tropical, 13 deep-tropical).
- Cluster non-independence (F.104) — state this UP FRONT here, not as a limitations
  afterthought, since it affects how every CI in Results should be read.
- Figure F2 goes here.

## 2.3 Predictor streams and the MAIAC-vs-GHAP distinction
- Why two satellite AOD products are used, and why MAIAC (raw) is the primary/honest stream
  while GHAP (fused, monitor-blended) is reported for comparison only, given the peer session's
  finding that GHAP partially encodes the ground stations whose value is being measured.
- This subsection needs updating once the peer session's write-up lands — check for an F-code.

## 2.4 Estimator families and the model-family tournament
- The 7 admissible families tested (F.105) — describe methodology, not results.

## 2.5 The eight spatial-limit tests
- One paragraph per test's design (not result): learned-pattern (OSF 2jyfg), full LUR set,
  AlphaEarth embeddings, deliberate-siting, model-family tournament, GNN density benchmark,
  dynamic-transport diagnostics, change-of-support transect.
- Pre-registration status of each — be precise about which are OSF-registered vs. exploratory
  (see the caution from the peer session, 2026-09-23, about not over-claiming registration).

## 2.6 Statistical approach: why paired, not pooled
- This subsection is a NEW addition given the day's findings — write it as a methodological
  point in its own right: define the paired-within-city bootstrap procedure used throughout,
  contrast explicitly with a pooled/unpaired median comparison, and preview that §3 and §4 will
  show three instances where the two approaches disagree.
