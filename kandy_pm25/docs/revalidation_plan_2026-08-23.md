# Re-validation plan — rebuilding the ladder with a spec-compliant `Bud0`

**Trigger:** F.84. The scored `Bud0` used one of its three admitted streams (drivers only; no
satellite level, no static geography), so every gain measured above it is inflated against an
artificially weak baseline. The specification, the pre-registration and the implementation all
disagreed.

**Status of current numbers: DO NOT QUOTE** the ladder step gains, the learner-sensitivity
figures, or the Colombo result until this plan completes.

---

## 1. The design insight — do not replace `Bud0`, decompose it

The obvious remediation is to rebuild `Bud0` with all three streams and re-run. **That would
throw away information.**

Instead, split the bottom of the ladder so that each *globally available* stream becomes its own
rung. The ladder then measures the value of satellite and geography on the same footing as ground
stations:

| rung | information | new? |
|---|---|---|
| **`Bud0a`** meteorology | reanalysis drivers only | = the current `Bud0` |
| **`Bud0b`** + geography | + static geo: terrain, roads, population, built volume, night lights | **new** |
| **`Bud0c`** + satellite | + satellite PM2.5 annual level — **the spec-compliant `Bud0`** | **new** |
| `Bud1` | + 2 local stations | rescored |
| `Bud2` | + 6 more stations | rescored |
| `Bud3` | + regional background | rescored |

**Why this is strictly better than a straight fix:**

- It answers a question the network-design literature actually asks: **what is a satellite product
  worth, in monitor-equivalents?** If `Bud0a→Bud0c` exceeds `Bud0c→Bud1`, then for a city with no
  monitors the first useful investment is not a monitor at all. That is a genuinely publishable
  result and it is not currently in the literature.
- It preserves the honest meteorology-only baseline rather than discarding it.
- It converts F.84 from "we made an error" into "we decomposed the sensorless tier", which is what
  the paper should have done from the start.

⚠ The rungs must still nest **bit-exactly** (P3). `Bud0a` must be recoverable from `Bud0c` by
withholding streams, exactly as the higher rungs are.

## 2. 🔴 The admissibility problem this exposes — fix it in code first

`budgets.require()` raises when a tier **touches a stream it does not admit**. Nothing checks that
a tier **uses what it is entitled to**. A rung can silently under-use its budget, inflating every
gain above it, and the registry passes it.

**Before any re-run**, add the dual check to `src/modular/budgets.py`:

```
require(...)        # unchanged: no stream beyond the budget      (prevents cheating up)
require_covers(...) # NEW:      every admitted stream is present  (prevents under-powering)
```

with a test asserting that each tier's fitted feature set covers its admitted streams. Same class
as gotcha #73 — admissibility enforced by construction rather than by discipline.

## 3. 🔴 A leakage path that must be declared, not fixed

**Every global satellite PM2.5 product is calibrated against a global ground network.** Van
Donkelaar's and GHAP's products both use ground monitors for bias correction — plausibly
*including monitors in our panel cities*.

So a satellite-anchored `Bud0c` is **not strictly sensorless**: it is locally sensorless while
embedding a global ground network that may contain the target city.

This cannot be engineered away — it is a property of every such product. It must be **declared**:

> `Bud0c` is sensorless *in the sense available to a practitioner*: no local monitor is deployed,
> and no local record is read. It is not sensorless in the information-theoretic sense, because
> the satellite product it anchors to was itself calibrated against a global ground network of
> unknown overlap with this panel. We therefore report `Bud0a` alongside it as the strictly
> sensorless bound, and the pair brackets the answer.

⚠ This is the same class as gotcha #73 (a descriptor derived from the target's own outcome
leaks). Reporting both rungs is what makes it honest — and it is why §1's decomposition is not
optional.

## 4. Data

| stream | availability | work |
|---|---|---|
| `DRIVERS_REANALYSIS` | ✅ on disk, 47 cities | none |
| `STATIC_GEO` | ✅ **`lur_predictors.csv`** — 636 stations, 47 cities: roads at 50/100/300/500/1000 m, NDVI, tree cover, water, land cover, built volume, population, night lights at 4 radii | aggregate to **city level** |
| `SATELLITE_LEVEL` | ❌ **not on disk for the panel** | GEE pull, ~47 cities |

**Satellite source — pick one and justify it:** GHAP (1 km, on GEE, ⚠ band `b1` is already
µg m⁻³, do **not** apply the 0.1 scale — gotcha #50) or the ACAG/Van Donkelaar product used in
production. **Recommend GHAP** for the panel because it is directly on GEE and needs no tile
handling; note in the paper that production uses VanD, and that the two agree at Kandy within 6%
(U7).

⚠ **Static-geo support question, to decide before building:** aggregate the LUR predictors over
each city's *stations* (a convenience sample of the city) or over a city polygon? The stations
define where we score, so the station-mean is arguably the right support — but it is not the
city's geography. **Recommend station-mean, declared**, with a city-polygon sensitivity check if
it proves load-bearing.

## 5. Re-registration

The design has changed materially. The existing registration (**https://osf.io/nxqgb/**)
describes a Colombo test against a `Bud0` we now know was under-powered.

**Recommendation: do not withdraw it.** That test was run exactly as registered, its result is
real, and the reason it is superseded is itself a finding. Withdrawing would hide the very thing
the registration exists to demonstrate. Instead:

1. Let `nxqgb` stand, and cite it in the paper as *run, reported, superseded, and why*.
2. Register a **new** pre-registration covering the decomposed ladder and the re-run Colombo test,
   with fresh gates and fresh priors, **before** any re-run.
3. State priors as numbers again, including the honest expectation below.

**Registered prior to declare now, before seeing anything:**

> I expect the ladder to **flatten substantially**. Specifically: `Bud0c→Bud1` will be materially
> smaller than the currently-reported `Bud0→Bud1` of ~24%, because a satellite level anchor
> supplies much of what the first two stations were supplying. I further expect
> `Bud0a→Bud0c` to be **large**, plausibly comparable to or exceeding `Bud0c→Bud1`. If the ladder
> does *not* flatten, that is a finding and means local stations carry information no global
> product does.

## 6. Sequence

| # | step | gate |
|---|---|---|
| 0 | `require_covers()` + test in `budgets.py` | tests pass; the current `Bud0` **fails** the new check, proving it works |
| 1 | Write and register the new pre-registration | registered on OSF **before** step 3 |
| 2 | Aggregate `STATIC_GEO` to city level; GEE pull for `SATELLITE_LEVEL` | coverage ≥ 45 of 47 cities, or the shortfall is named |
| 3 | Rebuild the ladder with `Bud0a/b/c` | P3 bit-exact nesting holds across the new rungs |
| 4 | Re-run learner sensitivity on the new `Bud0c` | conclusion re-tested, not assumed |
| 5 | Re-run Colombo against `Bud0c` | reported once, per the new stopping rule |
| 6 | Update F.50–F.53, F.78, F.81; supersede in `CONTEXT.md` and `CLAUDE.md` | no stale step gains anywhere |

Effort: **days, not weeks.** GEE daily/static pulls are minutes per city (the multi-day rule
applies only to hourly Drive exports), and everything else is already automated.

## 7. Risks

| risk | handling |
|---|---|
| **The ladder flattens and the headline weakens** | It becomes *"a satellite product substitutes for local monitors"* — more useful to a network-design audience than the current numbers. Declare the prior first (§5) so it reads as a prediction, not a rescue. |
| Satellite coverage gaps | Name dropped cities; never silently replace them (the F.51 rule). |
| Static geo helps trivially little | Also a finding — geography adds nothing to a *city-mean* prediction, which is consistent with the measured spatial ceiling. |
| Colombo now passes | Then F.78's diagnosis was an implementation artefact and must be retracted in full. Say so plainly. |
| Scope creep into a third re-run | The stopping rule binds: one rebuild, one report. |

## 8. What must not happen

- **Do not quote the current step gains** in any draft, talk, or supervisor update until this
  completes.
- **Do not re-run Colombo before re-registering.** The one verifiable registration in this project
  is an asset; running first and registering after would destroy it.
- **Do not tune `Bud0c`'s feature set after seeing the ladder.** Fix it in the registration.
