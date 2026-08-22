# Manuscript claims audit — 2026-08-22

Written after ledger **F.64–F.72**. The 28-page manuscript was built 2026-08-14. Several
load-bearing claims have moved since, and **one of them is structural** rather than a wording fix.

Sections 0–2 are the audit. Section 3 is drafted replacement text.

---

## 0. Severity summary

| # | claim | where | severity | action |
|---|---|---|---|---|
| **A** | the spatial validation measures spatial *skill* | §5.3, §5.4, §7.2 | 🔴 **structural** | reframe: it is skill **confounded with change-of-support**, in all ten cities |
| **B** | "the within-city signal at Kandy is small to begin with" | §7 (L17–19) | 🔴 **circular** | replace with four observational datasets |
| **C** | "roughly 90 per cent of local emission to vehicles" | §1 (L88) | 🔴 **refuted** | replace with the graded, measured picture |
| **D** | the FECT slopes "have never been verified against a reference instrument" | §1 (L143), §7.7 | 🟡 **outdated** | now corroborated at Akurana (F.64) |
| **E** | the level axis is strong / unqualified | §5, §6, abstract | 🟡 **needs qualifying** | W11: three of four Kandy records sit below the model |
| **F** | Kandy has "no retrievable public PM2.5 record" | §1 | 🟡 **overstated** | two published Kandy records now exist (F.65) |
| **G** | Seneviratne 2017's five factors, "only one represented by a road surface" | §7.5 | 🟢 **strengthen** | the shares are now known: traffic 7.6%, biomass 14.1% |
| **H** | transboundary framing cites [Abeyratne2006] | §1 | 🟢 **strengthen** | now read: it is a spatial falsification test (F.72) |

---

## 1. 🔴 A — the structural one: the panel's spatial arm has the same defect as the Kandy comparison

§5.3 defines the spatial score as *"the agreement between the modelled and observed ordering of
**stations** within the city."* The model is a **1 km areal mean**; a monitor is a **point**.
So in every one of the ten cities, the spatial arm correlates two different measurands.

F.69 measured what that mismatch is worth **in the target city**: two sites 300 m apart differ by
**27.5×** in observation and **1.000×** in the model, because they share one 998 m pixel. F.71
showed the contrast falls monotonically with averaging support — **85× → 4.0× → 3.0× → 1.23×**.
A model that reproduced the true 1 km areal field *perfectly* would still score poorly against
point monitors, and the size of that penalty is unmeasured.

**Why this is serious rather than pedantic.** The paper's spatial conclusion rests on **five
independent nulls** — the learned-pattern test, dynamic transport, the emission-surface
comparison, the earth-observation embedding, and the land-use regression. **All five are scored
model-field-against-point-station.** They therefore share a defect, and *five tests agreeing is
not independent confirmation when they share a defect* — which is the exact lesson the
remediation plan recorded in its own §1 and then failed to apply one level up.

**What survives, and this matters.** The **R2 local-LUR** result does *not* share the defect: it
regresses station values on station-buffer predictors, point-against-point, no model field
involved, and it still failed (held-out R² −0.194 to −2.350). That failure is a **sample-size**
limit — a median of 12 stations per city against 40–80 in published LUR — not a support artefact.

**So the honest attribution splits three ways**, where the manuscript currently gives one:

1. a **sample-size** limit (measured: R2 fails point-to-point),
2. a **change-of-support** limit (measured at Kandy: F.69/F.71),
3. a **residual information** limit — whatever is left, and the paper can no longer claim to have
   isolated it.

**The claim to make instead** is stronger and defensible: *the fine spatial pattern is not
recoverable at 1 km from public observations, and we can now say why — partly because the
networks are too small to fit a land-use model, and partly because the quantity being asked for
is not defined at the resolution being modelled.*

⚠ **This does not weaken the paper.** It converts a set of unexplained nulls into an explained
limit, and it makes §7.2 — already flagged in the drafting notes as "the section's strongest
general contribution" — genuinely novel. It also retro-justifies the `Bud4` demotion on physical
rather than merely empirical grounds.

⚠ **It does not invalidate the reported ρ.** As an operational statement — *can a user rank
neighbourhoods with this product against what a monitor would read there?* — ρ ≈ 0.2–0.28 stands
and the answer is "poorly". Keep the number; change what it is said to measure.

**Scope check — the other three arms are largely unaffected.** Level is a bias against a
*network mean*, which averages many stations and blunts the mismatch, and it has independent
corroboration (F.54, and now F.65). Seasonal and diurnal are correlations of *normalised network
mean cycles*, where a multiplicative support offset largely cancels. The defect is concentrated
in the spatial arm — which is the arm the paper already reports as failing.

---

## 2. The rest, briefly

**B — circular evidence.** §7 argues the within-city signal is small using the *model's own*
1.31× decile ratio and 8.2% CV. The model imposes the pattern; citing its spread as evidence
about the world is circular, and it is the softest paragraph in the paper. Replaced in §3 below.

**C — the vehicular share.** §1 states "roughly 90 per cent of local emission to vehicles"
from a sector inventory, and the drafting note asks only that it be attributed to the inventory
rather than presented as measured. That is no longer sufficient: **it is refuted as a mass share**
(F.66 — traffic 7.6%, biomass burning 14.1% at Katugastota). F.71 resolves the tension by
geography rather than by picking a side. Replacement drafted below.

**D — FECT calibration.** §1 and §7.7 call the slopes "never verified against a reference
instrument" and "the largest unverified step in the chain". **Now partly closed:** Akurana's
full-record mean of **17.8** sits against a BAM-anchored published value of **~18–19** (F.64).
Soften from *unverified* to *corroborated at one of the two sensors, at the level, and not at the
sub-daily shape*. Do not overclaim — the shape claims still rest on the slopes.

**E — the level axis.** The paper treats level as the strong axis. Since the build: one Kandy
record matches to within 3% and another sits **28% below** the model; three independent sources
state Kandy reads **dirtier than Colombo**; and Ileperuma publishes CEA's 2019 Kandy series as a
figure, describing most values as exceeding the Sri Lankan standards. None is decisive. But the
paper should not go to readers asserting an unqualified strong level axis while **W11** is open.
One honest paragraph in §7.7.

**F — "no retrievable public PM2.5 record".** True of *continuous retrievable series*; no longer
true of published values. Narrow the wording to "no continuous retrievable series", and cite
Nirmani 2025 and Attanayake 2025 as the two published point records — which also lets the paper
report them as external checks, which is a gain.

**G — §7.5 strengthens for free.** It says only one of Seneviratne's five factors is on the road
network. The shares are now in hand: **traffic 7.6%, biomass burning 14.1%, soil 3.8%, sea salt
3.2%**. State them; the limitation becomes quantitative instead of qualitative.

**H — §1 strengthens for free.** [Abeyratne2006] is now read (F.72). It is not a passing mention
of transboundary influence but a **spatial falsification test**: Sri Lanka's own source region
lies south-west, so a local signal must peak in the SW monsoon; the maximum is instead in the NE
(SO₂ 46%), where there are no domestic sources. That independently corroborates the paper's
seasonal-not-chronic position, from a different decade and different pollutants.

---

## 3. Drafted replacement text

### 3a. Replaces §7's opening spatial paragraph (currently L17–25)

> The within-city signal at Kandy is not small. It is large, and it lives below the grid.
>
> Four independent campaigns have measured the spatial contrast of particulate matter in this
> city, at four different averaging supports. Twenty-five kerbside sites sampled over three
> hours span a factor of **85**, from 4 µg m⁻³ inside a botanical garden to 340 at a congested
> junction — and 110 of that 340 is measured at the same garden's entrance, three hundred metres
> from the 4. Twenty sites sampled over eight hours and stratified by land use span a factor of
> **4.0** between sites and **2.0** between land-use classes. Five fixed sites averaged over
> twenty-four hours span **3.0**. The field presented here, at 1 km and hourly, spans **1.23**.
>
> The contrast collapses monotonically as the averaging support grows. That is not a failure of
> the model; it is the definition of the quantity it reports. A concentration field at 1 km is an
> areal mean, and the gradient these campaigns measure has a decay length of order one hundred
> metres. It is averaged away inside a single cell before any estimator sees it.
>
> This reframes the five null results that follow. Each compares a modelled areal field with
> point observations at monitor locations, and each therefore carries an unmeasured penalty from
> the same mismatch: a model that reproduced the true 1 km field exactly would still rank
> stations poorly. We report the nulls because the operational question — can a user rank
> neighbourhoods against what a monitor would read there — is answered by them, and the answer
> is no. We no longer attribute them wholly to an information limit. One of the tests does
> isolate an information limit: a land-use regression fitted station-to-station, with no model
> field involved, fails on its own terms at a median of twelve stations per city against the
> forty to eighty of published designs. What remains is a limit of definition rather than of
> data, and no predictor, network or learner operating at 1 km can lift it.

*(~290 words, replaces ~120. If space is tight, the fourth paragraph is the one to compress —
but not to cut, since it is the part that is new.)*

### 3b. Replaces §1 L88–91 (the vehicular attribution)

> Local emission at Kandy is traffic-led in the urban core and mixed elsewhere. A sector
> inventory attributes roughly nine-tenths of local emission to vehicles, but that figure is an
> inventory prior and the measurements do not support it as a share of mass: receptor modelling
> on filter samples from a suburban site apportions **7.6 per cent** of fine mass to traffic and
> **14.1 per cent** to biomass burning [Seneviratne2017]. A twenty-site study resolves the
> apparent conflict geographically, finding automobile emissions the predominant daytime source
> of combustion tracers in urban and suburban areas, and domestic firewood dominant in rural
> areas while remaining significant in the urban core [Wickramasinghe2011]. What the local
> instrument in Section 7 establishes is the *timing* of the activity-responsive component,
> which is strongly rush-hour peaked; it does not bound the mass share.

### 3c. Replaces the FECT sentence in §7.7

> The correction slopes applied to the two local sensors were, until recently, unchecked against
> any reference instrument. One of the two can now be checked: an independent study anchored to
> a reference monitor reports a mean of about 18 to 19 µg m⁻³ at the Akurana site over an
> overlapping period, against 17.8 in the corrected record used here [Dhammapala2022]. That
> corroborates the *level* at one sensor. It does not corroborate the sub-daily and seasonal
> shapes, which remain the largest step in the chain resting on an unverified calibration.

### 3d. New paragraph for §7.7 (the level qualification, W11)

> The level at Kandy is the best-evidenced axis of this work, and it is not closed. Two point
> records have since been published for the city. One, a network of 24-hour measurements
> supplied by the national building research organisation, gives annual means of 19.6 and 22.7
> µg m⁻³ for 2021 and 2022 against 19.7 and 22.1 in the field presented here. The other, a
> low-cost sensor calibrated against a reference instrument, gives 19.5 where this field gives
> 25.0. The two records disagree with one another by more than either disagrees with the model,
> and the model places their sites within three per cent of each other, so the discrepancy is not
> one the spatial pattern could resolve. Separately, three independent sources report that Kandy
> reads higher than Colombo in the gas phase. We record this as an open discrepancy rather than
> resolving it in favour of the record that agrees.

---

## 4. Recommended order

1. **A** — the §5/§7 reframe. Largest, and it is the one that changes what the paper *claims*.
2. **C**, **D**, **E** — three factual corrections that must not go to readers uncorrected.
3. **F**, **G**, **H** — three free strengthenings.
4. Re-run `assemble_manuscript.py` → `build_report.js`. **Edit the `draft_s*.md` files, never
   `manuscript_kandy.md`.** Figure numbering follows first appearance of `{{fig:tag}}` tokens, and
   pandoc does not resolve `\ref{}` (gotcha #58), so re-check every hardcoded figure number.
