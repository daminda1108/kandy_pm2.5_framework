## Moved from CONTEXT.md on 2026-09-28 (verbatim)

### From §4 (spatial cause, F.68/F.69, and Bud4)

🟢 **The CAUSE is measured in Kandy itself (F.68).** A 25-site PM10 transect (Elangasinghe &
Shanthini 2008) records **110 → 4 µg/m³ over 300 m** inside one botanical garden, R² **0.82**
against traffic. The signal is *enormous*; its decay length is **tens to hundreds of metres** and
a 1 km cell integrates over exactly that. **Sub-grid by construction** — a change-of-support
statement, not a data-quality complaint. ⚠ It does **not** resolve W6 (roadside PM10 *variance*
≠ ambient PM2.5 *mass*).

🔴 **Scored against the model (F.69), the first within-Kandy spatial test ever run.** 12 sites,
11–13 LT: observed spread **85×**, model **1.23×**; paired sites 300 m apart are **27.5× observed,
1.000× modelled** (same pixel). Rank ρ +0.44 (n=12, p=0.16), **not significant**. ⚠ A second
apparent pair carried **one coordinate for both sites** and is withdrawn.

🔴 **`Bud4` is an unsupported design assumption**, not a validated rung — but a **tested** one
(2026-09-04, OSF [`2jyfg`](https://osf.io/2jyfg/)), which is a different epistemic object.
Interpolation between a city's own stations is worse than assuming the city uniform (F.60) and a
transferred LUR barely beats a population raster (F.61). Benchmark = best single free predictor,
**built-up land cover at 2.4 km, ρ 0.309** (46 cities, 630 stations); detection limit **0.130**;
registered bar **0.44**; learned pattern reached **0.286** (Δ +0.022, 25/46, p = 0.94) → **L1
held**, reported as *undetectable at this power*. **Sixth null on within-city spatial pattern and
the first with a detection limit stated in advance** — the previous five could only have detected
0.65–0.96. 🟢 Gauge exact to **3.3e-16**: a learned pattern can *misplace* material, never *create* it.
🟡 The band difference is real (temperate +0.457 vs +0.225, p = 0.006) but the mechanism is **not
established** and the test was **not pre-registered** — exploratory. ⚠ **No engineered emission
surface beats a single free raster**, including one carrying OSM industrial land use (a real
predictor that rescues Yichang, where the traffic surface scores **−0.091**).
**Label `Bud4` as a declared assumption wherever it appears.**

### From §5 (closed topics)

### 🔴 The support-scaling ladder is CONFOUNDED — never quote it as a scaling law (F.76)

Support and siting design moved together across its rungs; a direct test on three dense networks
finds temporal averaging collapses contrast by only **1.2–1.7×**, not 69×. **Most of the apparent
ladder is siting contrast, not averaging.** What survives is stronger: the **paired-site test is
unconfounded** (27.5× observed, 1.000× modelled), and **at matched support AND window the model
is close to right** (F.77: monthly p90/p10 **1.175** modelled vs **1.26–1.51** observed; ⚠ the
observed spreads are across *stations*, the model's across *cells*). 🟢 **The amplitude question
is CLOSED** — `s_exp` stays at 1.0. There is no amplitude crisis; what the model cannot do is
*place* the contrast.

### 🟢 Chemistry: ANSWERED, and it is not a fourth pillar (2026-09-06, F.98)

Deepened by the tractable route — species-resolved testing against reanalysis already on disk,
**no CTM**. Three strands, one usable:

- 🟢 **Fréchet bounds** put the locally emitted primary share at Kandy between **9.1% and 48.3%**.
  This replaces the withdrawn *"removing local sources removes half the problem"* — and shows
  that claim sat at the **top** of the admissible range.
- 🔴 **Registered null.** All three confirmatory hypotheses **undetectable** (largest partial ρ
  **0.135** vs MDE **0.431**). The deviation is the finding: the exploratory signal that motivated
  it (pooled 46 cities **+0.388**, p = 0.008) **survives in neither group** — banded 35 **+0.093**,
  CNEMC 11 **+0.036**. **A network effect wearing a chemical variable's name.**
- ⚠ **INVALID, neither held nor refuted.** The species partition ranks **dust 0.806 and sea salt
  0.645 above black carbon 0.387**; an inland valley has no local sea-salt source, so the
  estimator measures episodic variability, not origin. **Never report the reversal.**

**Chemistry is a supporting discipline with one measured bound.** The thesis says so.

### 🔴 The Kandy campaign — designed, costed, registered, and its spatial premise refuted (F.99–F.103)

🧭 **2026-09-17 USER DECISION: NOT IN THE FINAL THESIS — still under development.** The work and
registration (`ad3py`) stay as ongoing project work. **Removed from the thesis 2026-09-17**: §9.7 is
gone; the **F.103 siting experiment** now sits in §8.5 and the **F.112 precipitation null** in §7.2;
`ad3py` appears in Table 7.5 only as a neutral "Kandy measurement design" row.

**35 sites, 5 strata**, over an emission surface spanning **65×** p10→p90 of which the existing
records occupy only the **61st–100th percentile**. Registered blind at **OSF [`ad3py`](https://osf.io/ad3py/)**
before deployment. Plan: `kandy_pm25/docs/sensor_placement_plan_2026-09-05.md` (no longer in the thesis).

🔴 **What the campaign can no longer claim.** Its spatial ambition is dead twice over:
**F.100** — beating the 0.309 benchmark with 18 fitting sites needs a gain of +0.30 to +0.47 while
the 46-city panel resolved **0.130**, and matching it in one city needs **96–304 sites**;
**F.103** — on 43 dense-network cities deliberate siting does **not** measurably beat convenience
siting (**paired −0.044 [−0.095, +0.118]**, 19/43). **The LUR gap is information, not siting.**

🟢 **What it still settles, well powered:** the **level** (the anchor alone); the
**within-cell ratio**, which resolves to **1.044 in seven days** against competing predictions of
1.58 and 27.5; and the **drainage sign test**, whose unit is the night (63.1% over 90).

**Cost: 19,900–49,900 USD** — instruments 9,900, reference anchor 10,000–40,000. ⚠ Mounting,
power, **import duty**, labour and servicing carry **empty unit prices**; none is published for
Sri Lanka. 🔴 **The largest line may be a letter** — CEA has granted access in principle.
🔴 **Re-scoping is not worth doing:** trimming the design stratum 12→10 saves **450 USD**,
under 3%. ⚠ D-efficiency **ranks the wrong designs first** (road-sited 0.70, existing 0.88,
proposal 0.35) — it endorses the two designs already known to produce nulls.

~~The open decision is what the campaign CLAIMS~~ — superseded 2026-09-17: excluded from the thesis.

